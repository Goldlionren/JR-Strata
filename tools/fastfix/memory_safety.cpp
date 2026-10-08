// Real alias scan plus fault injection of retry exhaustion; no model needed.
#include "strata/sycl_queue.hpp"
#include <cstdio>
#include <stdexcept>
int main() {
    sycl::queue q{sycl::gpu_selector_v, sycl::property::queue::in_order{}};
    if (!strata::arena_alias_guard_enabled()) return 2;
    int checks = 0;
    try {
        void* p = strata::malloc_device_guarded_checked(32ull << 20, q, "injected alias", [&](auto&, auto*, auto, auto*) {
            ++checks; return uint64_t{1};
        });
        sycl::free(p, q);
        std::fprintf(stderr, "FAIL: unsafe allocation was returned\n"); return 1;
    } catch (const std::runtime_error& e) {
        if (checks != 8 || std::string(e.what()).find("REFUSED") == std::string::npos) throw;
    }
    try {
        void* p = strata::malloc_device_guarded(q.get_device().get_info<sycl::info::device::global_mem_size>() + 1, q);
        sycl::free(p, q); return 1;
    } catch (const std::runtime_error& e) {
        if (std::string(e.what()).find("physical VRAM") == std::string::npos) throw;
    }
    void* p = strata::malloc_device_guarded(512ull << 20, q, "512 MiB safety probe");
    if (strata::arena_alias_check(q, p, 512ull << 20)) return 1;
    sycl::free(p, q);
    std::puts("PASS: 8-check refusal, physical VRAM bound, 512 MiB real alias scan");
}
