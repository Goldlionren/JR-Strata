#pragma once
#include <cstddef>
#include <utility>
namespace strata::failed_work {
// Error/teardown only. Poll every queue even when another queue has failed. A
// queue query is not an asynchronous-error check; finish() is mandatory too.
struct Result { bool complete; bool error; bool safe() const { return complete && !error; } };
template<class Empty, class Finish, class Expired, class Pause>
Result drain(std::size_t n, Empty empty, Finish finish, Expired expired, Pause pause) noexcept {
    bool error = false;
    for (;;) {
        bool complete = true;
        for (std::size_t i = 0; i < n; ++i) {
            try { if (!empty(i)) complete = false; }
            catch (...) { error = true; complete = false; }
        }
        if (complete) {
            for (std::size_t i = 0; i < n; ++i) {
                try { finish(i); } catch (...) { error = true; }
            }
            return {true, error};
        }
        if (expired()) return {false, error};
        pause();
    }
}
template<class F> struct FailureGuard {
    F failed;
    bool accepted = false;
    ~FailureGuard() noexcept { if (!accepted) failed(); }
};
template<class F> FailureGuard(F) -> FailureGuard<F>;
// Host callback arguments must belong to the submitted operation, not a reused
// verifier slot. The pointed-to allocation is retained until queue completion.
struct Publication {
    unsigned* flag;
    unsigned value;
    template<class Publish> void operator()(Publish publish) const { publish(flag, value); }
};
} // namespace strata::failed_work
