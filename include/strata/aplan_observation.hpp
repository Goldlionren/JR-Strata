#pragma once
#include <cstdint>
namespace strata::aplan {
// Diagnostic-only snapshots. Never authorize a plan, extend a wait or change output.
struct Route {
    uint32_t hash = 2166136261u, invalid = 0, missing = 0, resident = 0, mirrored = 0;
    int32_t first_bad = -1, expert = -1, slot = -1;
    uint64_t mirror = 0;
};
inline Route inspect(const int32_t* ids, const int32_t* slots, const unsigned long long* mirrors,
                     int n, int n_expert) {
    Route r;
    for (int i = 0; i < n && i < 64; ++i) {
        const int e = ids[i], s = slots[i];
        r.hash = (r.hash ^ uint32_t(e)) * 16777619u;
        const bool invalid = e < 0 || e >= n_expert;
        const bool missing = !invalid && s < 0 && mirrors[i] == 0;
        r.invalid += invalid; r.missing += missing;
        r.resident += !invalid && s >= 0;
        r.mirrored += !invalid && s < 0 && mirrors[i] != 0;
        if ((invalid || missing) && r.first_bad < 0) {
            r.first_bad=i; r.expert=e; r.slot=s; r.mirror=mirrors[i];
        }
    }
    return r;
}
struct Wait {
    uint32_t entered=0, skip=0, before=0, after=0, spins=0, exited=0;
};
struct Device {
    uint64_t generation=0; // host sets only between completed windows
    uint32_t expected=0, entered=0, decision=0, skip_written=0;
    int32_t entries=0, shared_bad=0;
    uint64_t res_address=0, mirror_address=0;
    Route route{};
    Wait wait[3]{}; // A, B, M; sequence observations, NOT GPU duration
    uint32_t copy_action=0; // 1 rejected, 2 device, 3 host
};
struct Host {
    int64_t begin_ns=0, publish_ns=0, fetch_ns=0, return_ns=0;
    uint32_t seq_begin=0, seq_publish=0, seq_return=0;
    int32_t groups=0, entries=0, pcie=0, dma=0;
};
// Evidence classification is deliberately conservative; shared_bad is the actual kernel decision.
enum class Finding { incomplete, rejected_routes, unexplained_reject, skip_mismatch, completed };
inline Finding classify(const Device& d, uint64_t generation, uint32_t ring) {
    if (d.generation!=generation || d.expected!=ring || d.entered!=ring || !d.decision)
        return Finding::incomplete;
    if (d.decision==2)
        return (d.entries>64 || d.route.invalid || d.route.missing) ? Finding::rejected_routes : Finding::unexplained_reject;
    if (d.skip_written!=ring || (d.wait[0].entered && d.wait[0].skip!=ring)) return Finding::skip_mismatch;
    return d.wait[0].exited ? Finding::completed : Finding::incomplete;
}
}
