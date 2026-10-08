#pragma once
#include <cstdint>
namespace strata::readiness {
enum class Plan { reject, device, host };
inline Plan plan(uint32_t first_failure, uint32_t ready, uint32_t want, uint32_t skip) {
    if (first_failure) return Plan::reject;
    if (skip == want) return Plan::device;
    return ready >= want ? Plan::host : Plan::reject;
}
// Called only by the single waiter in an in-order graph. Preserve the first
// failed ring and its observed words, not a later consequence in the same window.
template<class Load, class Store>
void timeout(uint32_t* flag, uint32_t want, uint32_t observed, uint32_t skip, Load load, Store store) {
    if (!load(flag + 1)) {
        store(flag + 2, observed);
        store(flag + 3, skip);
        store(flag + 1, want);
    }
}
}
