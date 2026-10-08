#pragma once
#include <cstdint>
namespace strata::kernels {
// SYCL-only guarded variants; existing CUDA/HIP APIs and kernels unchanged.
void wait_verify_ready(const uint32_t* flag, uint32_t ring, const uint32_t* skip,
                       int32_t* discard_counts, void* stream);
void copy_verify_plan(int32_t* dst, const int32_t* src, long long n,
                      const uint32_t* skip, uint32_t ring, const uint32_t* flag, void* stream);
}
