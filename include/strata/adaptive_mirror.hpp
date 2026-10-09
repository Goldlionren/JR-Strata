#pragma once
// CPU-testable ownership transaction used by the GGUF adaptive copy path.
#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>
#include <utility>
#include <unordered_set>
namespace strata::adaptive_mirror {
struct Swap { size_t in, out; int32_t slot; };
struct Item { Swap swap; uint8_t* host; };
class Batch {
public:
    bool prepare(const std::vector<Swap>& swaps, size_t experts_per_layer,
                 const std::vector<int32_t>& residency, const std::vector<uint8_t*>& mirror,
                 uint64_t generation, std::string& err) {
        if (active() || experts_per_layer == 0 || residency.size() != mirror.size())
            return fail(err, "active exchange or invalid table dimensions");
        std::unordered_set<size_t> experts;
        std::unordered_set<int32_t> slots;
        std::unordered_set<uint8_t*> hosts;
        std::vector<Item> items;
        for (const auto& s : swaps) {
            if (s.in >= mirror.size() || s.out >= mirror.size() || s.in == s.out ||
                s.in / experts_per_layer != s.out / experts_per_layer || s.slot < 0 ||
                residency[s.in] != -1 || residency[s.out] != s.slot ||
                !mirror[s.in] || mirror[s.out] || !experts.insert(s.in).second ||
                !experts.insert(s.out).second || !slots.insert(s.slot).second ||
                !hosts.insert(mirror[s.in]).second)
                return fail(err, "stale, uncovered, duplicated or cross-layer exchange");
            items.push_back({s, mirror[s.in]});
        }
        items_ = std::move(items); generation_ = generation; completed_ = false;
        return true;
    }
    bool active() const { return !items_.empty(); }
    const std::vector<Item>& items() const { return items_; }
    // Called only after the real final copy event's wait_and_throw succeeds.
    void copies_completed() { completed_ = true; }
    bool commit(std::vector<int32_t>& residency, std::vector<uint8_t*>& mirror,
                uint64_t& generation, std::string& err) {
        if (!active() || !completed_ || generation != generation_ || residency.size() != mirror.size())
            return fail(err, "incomplete copy or changed exchange generation");
        for (const auto& i : items_) {
            const auto& s = i.swap;
            if (s.in >= mirror.size() || s.out >= mirror.size() ||
                residency[s.in] != -1 || residency[s.out] != s.slot ||
                mirror[s.in] != i.host || mirror[s.out])
                return fail(err, "exchange ownership changed before commit");
        }
        // No readers between prepare and device publication. Validate every item before changing any.
        for (const auto& i : items_) {
            const auto& s = i.swap;
            mirror[s.out] = i.host; mirror[s.in] = nullptr;
            residency[s.out] = -1; residency[s.in] = s.slot;
        }
        ++generation; items_.clear(); completed_ = false;
        return true;
    }
private:
    static bool fail(std::string& err, const char* msg) { err = msg; return false; }
    std::vector<Item> items_;
    uint64_t generation_ = 0;
    bool completed_ = false;
};
// The production and CPU fault-injection queues execute this same three-copy schedule.
template<class Gpu, class Bytes, class Copy>
void enqueue(const Batch& batch, uint8_t* scratch, Gpu gpu_of, Bytes bytes_of, Copy copy) {
    for (const auto& i : batch.items()) {
        auto* gpu = gpu_of(i.swap.slot);
        const size_t bytes = bytes_of(i.swap.in);
        copy(scratch, gpu, bytes);
        copy(gpu, i.host, bytes);
        copy(i.host, scratch, bytes);
    }
}
} // namespace strata::adaptive_mirror
