#pragma once
#include "strata/failed_work.hpp"
#include <dpct/dpct.hpp>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <thread>
namespace strata {
[[noreturn]] inline void unsafe_gpu_exit(const char* reason) noexcept {
    std::fprintf(stderr, "FASTFIX_UNSAFE_TEARDOWN: %s; GPU quiescence/error-free completion unproven. "
                         "No application GPU allocations will be freed; assess GPU health before restart.\n", reason);
    std::fflush(nullptr);
    // Do not unwind owners or run SYCL static destructors on an unhealthy queue.
    // Driver process cleanup is unavoidable; this does NOT assert a healthy GPU.
    std::_Exit(86);
}
inline void drain_device_or_exit(const char* reason) noexcept {
    try {
        auto queues = dpct::get_current_device().queues_snapshot();
        const auto until = std::chrono::steady_clock::now() + std::chrono::seconds(5);
        const auto result = failed_work::drain(queues.size(),
            [&](std::size_t i) { return queues[i]->ext_oneapi_empty(); },
            [&](std::size_t i) { queues[i]->wait_and_throw(); },
            [&] { return std::chrono::steady_clock::now() >= until; },
            [] { std::this_thread::sleep_for(std::chrono::milliseconds(1)); });
        if (!result.safe()) unsafe_gpu_exit(reason);
    } catch (...) { unsafe_gpu_exit(reason); }
}
} // namespace strata
