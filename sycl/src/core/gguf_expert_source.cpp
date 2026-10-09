// src/core/gguf_expert_source.cpp - see the header. Plain C++, no device code.
#include "strata/core/gguf_expert_source.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"

#include <cstring>
#include <fcntl.h>
#include <unistd.h>
#include <dpct/dpct.hpp>
#include <sycl/sycl.hpp>
#include <thread>
#include <atomic>
#include <stdexcept>
#include "strata/sycl_failed_work.hpp"

namespace strata::core {

namespace {
constexpr size_t kRing = 512;   // blobs alive at once: the prompt path holds a layer's worth of streamed experts
}

GgufExpertSource::~GgufExpertSource() { close(); }

void GgufExpertSource::close() {
    // Never reclaim mapped weights/scratch while graph, DMA or host-task readers may still reference them.
    if (!blocks_.empty() || exchange_scratch_) strata::drain_device_or_exit("GGUF mirror destruction");
    if (exchange_scratch_) sycl::free(exchange_scratch_, dpct::get_in_order_queue());
    exchange_scratch_ = nullptr;
    exchange_ = adaptive_mirror::Batch{};
    exchange_queue_ = nullptr;
    mirror_generation_ = 0;
    for (uint8_t* b : blocks_)
        if (b != nullptr) sycl::free(b, dpct::get_in_order_queue());
    blocks_.clear();
    mirror_bytes_ = 0;
    mirror_ptr_.clear();
    layer_first_.clear();
    for (int fd : fds_) if (fd >= 0) ::close(fd);
    fds_.clear(); names_.clear(); layer_fd_.clear(); ring_.clear(); ring_key_.clear(); where_.clear();
    ring_next_ = 0;
}

bool GgufExpertSource::open(const std::string& shard1, int64_t n_layers, int64_t n_expert, std::string& err) {
    close();
    const auto& lay = strata::kernels::cpu::expert_layout();
    if (!lay.native || lay.gguf_off.size() < (size_t) (3 * n_layers)) {
        err = "--stream-experts needs a native (IQ) pack whose native_experts.txt carries the GGUF tensor offsets";
        return false;
    }
    for (int64_t l = 0; l < n_layers; ++l)
        for (int r = 0; r < 3; ++r)
            if (lay.gguf_off[(size_t) (3 * l + r)] == 0) {
                err = "--stream-experts: layer " + std::to_string(l) + " has no GGUF offset for its experts";
                return false;
            }
    shard_ = shard1;
    const size_t cut = shard1.find_last_of("/\\");
    dir_ = cut == std::string::npos ? std::string() : shard1.substr(0, cut + 1);
    n_layers_ = n_layers;
    n_expert_ = n_expert;
    layer_fd_.assign((size_t) (3 * n_layers), -1);
    for (int64_t l = 0; l < n_layers; ++l)
        for (int r = 0; r < 3; ++r)
            if (fd_of(l, r, err) < 0) { close(); return false; }
    ring_.resize(kRing);
    for (auto& b : ring_) b.resize((size_t) lay.max_blob);
    ring_key_.assign(kRing, -1);
    return true;
}

// The file of role `role` (0 gate, 1 up, 2 down) of `layer`. ExpertLayout::gguf_file is per layer AND role
// (`3 * layer + role`) since upstream 0.1.31; indexing it by layer alone read a shard-2 layer from shard 1 (Swift 1.5,
// whose layers 13-47 are in shard 2: garbage IQ1_M scales, NaN logits - 2026-10-01).
int GgufExpertSource::fd_of(int64_t layer, int role, std::string& err) {
    const size_t i = (size_t) (3 * layer + role);
    if (layer_fd_[i] >= 0) return fds_[(size_t) layer_fd_[i]];
    const auto& lay = strata::kernels::cpu::expert_layout();
    std::string name = shard_;
    if (lay.gguf_file.size() > i && !lay.gguf_file[i].empty()) name = dir_ + lay.gguf_file[i];
    for (size_t k = 0; k < names_.size(); ++k)
        if (names_[k] == name) { layer_fd_[i] = (int) k; return fds_[k]; }
    const int fd = ::open(name.c_str(), O_RDONLY | O_CLOEXEC);
    if (fd < 0) { err = "--stream-experts: cannot open " + name; return -1; }
    names_.push_back(name);
    fds_.push_back(fd);
    layer_fd_[i] = (int) fds_.size() - 1;
    return fd;
}

const uint8_t* GgufExpertSource::blob(int64_t layer, int64_t expert) {
    require_committed();
    if (layer < 0 || layer >= n_layers_ || expert < 0 || expert >= n_expert_ || ring_.empty()) return nullptr;
    if (!blocks_.empty() && !mirror_ptr_.empty()) {
        if (uint8_t* m = mirror_ptr_[(size_t) (layer * n_expert_ + expert)])
            return m;
    }
    const auto& lay = strata::kernels::cpu::expert_layout();
    const auto& fm = lay.fmt[(size_t) layer];
    const uint64_t blob = lay.bytes[(size_t) layer];
    // the arena loader's gather, for one expert: [gate | up | down] from the three tensors
    const uint64_t per[3] = {fm.up_off, fm.up_off, blob - fm.down_off};
    const uint64_t at[3] = {0, fm.up_off, fm.down_off};
    const int64_t key = ((int64_t) layer << 20) | expert;
    size_t slot;
    {
        std::lock_guard<std::mutex> lk(mu_);
        auto it = where_.find(key);
        if (it != where_.end()) { ++reads_; return ring_[it->second].data(); }   // still resident
        slot = ring_next_;
        ring_next_ = (ring_next_ + 1) % ring_.size();
        if (ring_key_[slot] >= 0) where_.erase(ring_key_[slot]);
        ring_key_[slot] = key;
        where_[key] = slot;
    }
    std::vector<uint8_t>& buf = ring_[slot];
    for (int r = 0; r < 3; ++r) {
        const int fd = fds_[(size_t) layer_fd_[(size_t) (3 * layer + r)]];
        const uint64_t src = lay.gguf_off[(size_t) (3 * layer + r)] + per[r] * (uint64_t) expert;
        uint64_t done = 0;
        while (done < per[r]) {
            const ssize_t n = ::pread(fd, buf.data() + at[r] + done, (size_t) (per[r] - done), (off_t) (src + done));
            if (n <= 0) { std::lock_guard<std::mutex> lk(mu_); where_.erase(key); ring_key_[slot] = -1; return nullptr; }
            done += (uint64_t) n;
        }
    }
    ++reads_;
    return buf.data();
}

int64_t GgufExpertSource::mirror(const std::vector<std::pair<int64_t, int64_t>>& pairs,
                                 uint64_t cap, int threads, std::string& err) {
    const auto& lay = strata::kernels::cpu::expert_layout();
    sycl::queue& q = dpct::get_in_order_queue();

    require_committed();
    if (!blocks_.empty()) strata::drain_device_or_exit("GGUF mirror replacement");
    // A fresh mirror replaces any previous one.
    for (uint8_t* b : blocks_)
        if (b != nullptr) sycl::free(b, q);
    blocks_.clear();
    mirror_bytes_ = 0;
    mirror_ptr_.assign((size_t) (n_layers_ * n_expert_), nullptr);
    layer_first_.assign((size_t) n_layers_, nullptr);

    struct Item {
        int64_t layer;
        int64_t expert;
        uint64_t bytes;
    };

    std::vector<Item> take;
    uint64_t wanted = 0;

    for (const auto& [l, e] : pairs) {
        if (l < 0 || l >= n_layers_ || e < 0 || e >= n_expert_)
            continue;

        const uint64_t b =
            (lay.bytes[(size_t) l] + 255ull) / 256ull * 256ull;

        if (wanted + b > cap)
            break;

        take.push_back({l, e, b});
        wanted += b;
    }

    if (take.empty())
        return 0;

    // Intel Arc / Level Zero: avoid one very large USM host allocation.
    // Default 4 GiB blocks. Override for experiments with:
    // STRATA_MIRROR_BLOCK_MIB=<MiB>
    uint64_t block_cap = 4ull << 30;

    if (const char* v = std::getenv("STRATA_MIRROR_BLOCK_MIB")) {
        const long long mib = std::atoll(v);
        if (mib >= 256)
            block_cap = (uint64_t) mib << 20;
    }

    // A block must always be able to hold the largest single expert blob.
    block_cap = std::max<uint64_t>(
        block_cap,
        ((uint64_t) lay.max_blob + 255ull) / 256ull * 256ull
    );

    auto fail_cleanup = [&]() {
        for (uint8_t* b : blocks_)
            if (b != nullptr) sycl::free(b, q);
        blocks_.clear();
        mirror_bytes_ = 0;
        mirror_ptr_.assign((size_t) (n_layers_ * n_expert_), nullptr);
        layer_first_.assign((size_t) n_layers_, nullptr);
    };

    size_t first = 0;
    int64_t mirrored = 0;

    while (first < take.size()) {
        size_t last = first;
        uint64_t block_bytes = 0;

        while (last < take.size()) {
            const uint64_t b = take[last].bytes;

            if (last > first && block_bytes + b > block_cap)
                break;

            block_bytes += b;
            ++last;
        }

        if (last == first) {
            err = "mirror: internal chunk sizing failure";
            fail_cleanup();
            return -1;
        }

        uint8_t* base = nullptr;

        try {
            base = (uint8_t*) sycl::malloc_host(block_bytes, q);
        } catch (const sycl::exception& ex) {
            err = std::string("mirror chunk: ") + ex.what();
        }

        if (base == nullptr) {
            if (err.empty())
                err = "mirror: no pinned host memory for chunk of " +
                      std::to_string(block_bytes >> 20) + " MiB";

            fail_cleanup();
            return -1;
        }

        // Offsets inside this block.
        std::vector<uint64_t> offs(last - first);
        uint64_t off = 0;

        for (size_t i = first; i < last; ++i) {
            offs[i - first] = off;
            off += take[i].bytes;
        }

        std::atomic<size_t> next{0};
        std::atomic<bool> bad{false};
        std::vector<std::thread> ts;

        const size_t count = last - first;

        for (int t = 0; t < std::max(1, threads); ++t) {
            ts.emplace_back([&] {
                for (size_t j; (j = next.fetch_add(1)) < count && !bad.load();) {
                    const Item& it = take[first + j];

                    if (!read_into(
                            it.layer,
                            it.expert,
                            base + offs[j],
                            (size_t) lay.bytes[(size_t) it.layer])) {
                        bad.store(true);
                    }
                }
            });
        }

        for (auto& th : ts)
            th.join();

        if (bad.load()) {
            sycl::free(base, q);
            err = "mirror: reading an expert from the GGUF failed";
            fail_cleanup();
            return -1;
        }

        blocks_.push_back(base);
        mirror_bytes_ += block_bytes;

        for (size_t i = first; i < last; ++i) {
            const Item& it = take[i];
            uint8_t* ptr = base + offs[i - first];

            mirror_ptr_[(size_t) (it.layer * n_expert_ + it.expert)] = ptr;

            if (layer_first_[(size_t) it.layer] == nullptr)
                layer_first_[(size_t) it.layer] = ptr;

            ++mirrored;
        }

        first = last;
    }

    return mirrored;
}

bool GgufExpertSource::pinned(int64_t layer, int64_t expert) const {
    require_committed();
    if (blocks_.empty() ||
        layer < 0 || layer >= n_layers_ ||
        expert < 0 || expert >= n_expert_ ||
        mirror_ptr_.empty())
        return false;

    return mirror_ptr_[(size_t) (layer * n_expert_ + expert)] != nullptr;
}

void GgufExpertSource::require_committed() const {
    if (exchange_.active()) throw std::logic_error("GGUF mirror read during uncommitted adaptive exchange");
}

const uint8_t* GgufExpertSource::device_alias(int64_t layer, int64_t expert) const {
    require_committed();
    if (layer < 0 || layer >= n_layers_ || expert < 0 || expert >= n_expert_ || mirror_ptr_.empty()) return nullptr;
    return mirror_ptr_[(size_t)(layer * n_expert_ + expert)];
}

bool GgufExpertSource::pcie_layer(int64_t layer) const {
    require_committed();
    return layer >= 0 && layer < n_layers_ && !layer_first_.empty() && layer_first_[(size_t)layer] != nullptr;
}

void GgufExpertSource::mirror_table(std::vector<unsigned long long>& table) const {
    require_committed();
    table.resize(mirror_ptr_.size());
    for (size_t i = 0; i < table.size(); ++i) table[i] = (unsigned long long)mirror_ptr_[i];
}

bool GgufExpertSource::exchange_async(const std::vector<adaptive_mirror::Swap>& swaps,
                                     const std::vector<int32_t>& residency, ExpertCache& cache,
                                     sycl::queue& queue, std::string& err) {
    if (swaps.empty()) return true;
    if (!queue.is_in_order()) { err = "GGUF exchange needs an in-order copy queue"; return false; }
    // Validate cache ownership too: never trust an index into repurposed slot storage.
    for (const auto& s : swaps) {
        if (s.slot < 0 || s.slot >= cache.slots() || s.in >= residency.size() || s.out >= residency.size() ||
            cache.slot_of(s.out / n_expert_, s.out % n_expert_) != s.slot ||
            cache.slot_of(s.in / n_expert_, s.in % n_expert_) != kNotResident) {
            err = "GGUF exchange cache ownership mismatch"; return false;
        }
    }
    const auto& lay = strata::kernels::cpu::expert_layout();
    if (!exchange_scratch_) {
        try { exchange_scratch_ = sycl::malloc_host<uint8_t>((size_t)lay.max_blob, queue); }
        catch (const std::exception& e) { err = e.what(); return false; }
        if (!exchange_scratch_) { err = "GGUF exchange scratch allocation failed"; return false; }
    }
    if (!exchange_.prepare(swaps, (size_t)n_expert_, residency, mirror_ptr_, mirror_generation_, err)) return false;
    exchange_queue_ = &queue;
    try {
        // Preserve victim first, upload incoming, then reuse its host slot. In-order execution also protects
        // the single scratch buffer between swaps. No reader is admitted until finish + both table uploads.
        adaptive_mirror::enqueue(exchange_, exchange_scratch_,
            [&](int32_t slot) { return (uint8_t*)cache.device_slot(slot); },
            [&](size_t in) { return (size_t)lay.blob_bytes(in / n_expert_); },
            [&](uint8_t* dst, const uint8_t* src, size_t bytes) { exchange_event_ = queue.memcpy(dst, src, bytes); });
        return true;
    } catch (const std::exception& e) {
        err = e.what();
        strata::drain_device_or_exit("partial GGUF adaptive exchange submission");
        return false; // contents may be partly replaced: caller must end this engine, never resume Decode
    }
}

bool GgufExpertSource::finish_exchanges(std::vector<int32_t>& residency, ExpertCache& cache, std::string& err) {
    if (!exchange_.active()) return true;
    try {
        exchange_event_.wait_and_throw();
        exchange_queue_->throw_asynchronous();
        const auto items = exchange_.items();
        exchange_.copies_completed();
        if (!exchange_.commit(residency, mirror_ptr_, mirror_generation_, err)) return false;
        for (const auto& i : items)
            cache.replace(i.swap.in / n_expert_, i.swap.out % n_expert_, i.swap.in % n_expert_);
        return true;
    } catch (const std::exception& e) {
        err = e.what();
        strata::drain_device_or_exit("GGUF adaptive exchange completion failed");
        return false;
    }
}

bool GgufExpertSource::read_into(int64_t layer, int64_t expert, uint8_t* dst, size_t bytes) const {
    if (layer < 0 || layer >= n_layers_ || expert < 0 || expert >= n_expert_ || dst == nullptr) return false;
    const auto& lay = strata::kernels::cpu::expert_layout();
    const auto& fm = lay.fmt[(size_t) layer];
    const uint64_t blob = lay.bytes[(size_t) layer];
    if (bytes < blob) return false;
    const uint64_t per[3] = {fm.up_off, fm.up_off, blob - fm.down_off};
    const uint64_t at[3] = {0, fm.up_off, fm.down_off};
    for (int r = 0; r < 3; ++r) {
        const int fd = fds_[(size_t) layer_fd_[(size_t) (3 * layer + r)]];
        const uint64_t src = lay.gguf_off[(size_t) (3 * layer + r)] + per[r] * (uint64_t) expert;
        uint64_t done = 0;
        while (done < per[r]) {
            const ssize_t n = ::pread(fd, dst + at[r] + done, (size_t) (per[r] - done), (off_t) (src + done));
            if (n <= 0) return false;
            done += (uint64_t) n;
        }
    }
    return true;
}

}  // namespace strata::core
