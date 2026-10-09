// include/strata/core/gguf_expert_source.hpp - the SYCL port: experts read from the GGUF on demand, no host arena.
//
// **WHY.** `ArenaExpertSource` keeps every expert as a resident host copy (R2.1): 23.4 GiB for the Coder, which
// the CPU pool computes misses from. On a card that holds every expert (12,288 slots on a 32 GB Arc) nothing is
// ever computed from that copy after the fill, and on a 23 GiB machine the copy cannot exist at all. This source
// gathers one blob at a time straight from the model's shard - the same three tensor slices the arena loader
// concatenates - into a small ring of staging buffers. The pointer is valid until the ring wraps, which is the
// `ExpertSource` contract ("until the next `blob()` call") with slack.
//
// It is slow per blob (three reads, ~2.7 MB) and that is fine: the profile fill reads each expert once at start,
// the prefill's lent slots are refilled a few hundred at a time, and with every expert resident the pool never
// asks. A blob in the startup/adaptive pinned complement is device-readable; other blobs retain GGUF fallback.
#pragma once

#include "strata/core/expert_source.hpp"

#include "strata/adaptive_mirror.hpp"
#include <sycl/sycl.hpp>
#include <cstdint>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace strata::core {

class GgufExpertSource : public ExpertSource {
public:
    GgufExpertSource() = default;
    ~GgufExpertSource() override;
    GgufExpertSource(const GgufExpertSource&) = delete;
    GgufExpertSource& operator=(const GgufExpertSource&) = delete;

    /// Needs `expert_layout()` loaded from a native pack (`native_experts.txt` with the tensor offsets) and the
    /// `--native` shard. Refuses a canonical pack: that one has experts.bin and the arena is the right source.
    bool open(const std::string& shard1, int64_t n_layers, int64_t n_expert, std::string& err);
    void close();

    const uint8_t* blob(int64_t layer, int64_t expert) override;
    /// The blob gathered straight into `dst` (bytes = the layer's blob size), from any thread: no ring slot, so the
    /// prompt path's stager threads read the streamed experts themselves instead of holding ring pointers that a
    /// later blob() call overwrites (the 80k-token run of 2026-09-30 streamed ~1,900 blobs per chunk through 512 slots).
    bool read_into(int64_t layer, int64_t expert, uint8_t* dst, size_t bytes) const;
    int64_t reads() const override { return reads_; }

    /// SYCL port, plan item 2: the experts that did not fit the VRAM cache, read once into pinned host memory the
    /// GPU can address (USM host). They are then `pinned()` with a `device_alias()`: the verify window reads them over
    /// PCIe on the GPU (its "direct" mode) and the prompt path DMAs them, instead of an SSD read each time they are
    /// routed - what made decode collapse to 4-5 tok/s at 256K (docs/INTEL.md). At most `cap` bytes; returns the
    /// number mirrored. Threads read in parallel.
    int64_t mirror(const std::vector<std::pair<int64_t, int64_t>>& pairs, uint64_t cap, int threads, std::string& err);
    bool pinned(int64_t layer, int64_t expert) const override;
    /// Exact expert alias only. An unmirrored expert returns nullptr, never another expert's bytes.
    const uint8_t* device_alias(int64_t layer, int64_t expert) const override;
    bool pcie_layer(int64_t layer) const override;
    // Caller has completed the preceding verifier window/host pool and joins adaptation before the next
    // window. Copy/commit may overlap MTP (its own expert arena) and state-only verifier commit.
    bool exchange_async(const std::vector<adaptive_mirror::Swap>& swaps,
                        const std::vector<int32_t>& residency, ExpertCache& cache,
                        sycl::queue& queue, std::string& err);
    bool finish_exchanges(std::vector<int32_t>& residency, ExpertCache& cache, std::string& err);
    bool exchanges_pending() const { return exchange_.active(); }
    uint64_t mirror_generation() const { return mirror_generation_; }
    void mirror_table(std::vector<unsigned long long>& table) const;
    uint64_t mirrored_bytes() const { return mirror_bytes_; }

private:
    int fd_of(int64_t layer, int role, std::string& err);

    std::string shard_;
    std::string dir_;
    std::vector<int> fds_;              ///< per distinct file name, opened once
    std::vector<std::string> names_;
    std::vector<int> layer_fd_;         ///< per layer and role (3 * layer + role): index into fds_
    std::vector<std::vector<uint8_t>> ring_;
    std::vector<int64_t> ring_key_;                 ///< (layer << 20 | expert) held by each slot, -1 = empty
    std::unordered_map<int64_t, size_t> where_;     ///< key -> slot
    size_t ring_next_ = 0;
    std::mutex mu_;
    int64_t n_layers_ = 0, n_expert_ = 0;
    int64_t reads_ = 0;
    // JR: Intel USM host allocations are chunked instead of one giant allocation.
    // Every block is independently pinned/device-readable; mirror_ptr_ gives the
    // exact USM address for every mirrored (layer, expert).
    std::vector<uint8_t*> blocks_;
    uint64_t mirror_bytes_ = 0;
    std::vector<uint8_t*> mirror_ptr_;              ///< per (layer, expert), nullptr = not mirrored
    adaptive_mirror::Batch exchange_;
    sycl::event exchange_event_;
    sycl::queue* exchange_queue_ = nullptr;
    uint8_t* exchange_scratch_ = nullptr; // one maximum-sized expert, reused on an in-order queue
    uint64_t mirror_generation_ = 0;
    void require_committed() const;
    std::vector<uint8_t*> layer_first_;             ///< first mirrored blob in each layer
};

}  // namespace strata::core
