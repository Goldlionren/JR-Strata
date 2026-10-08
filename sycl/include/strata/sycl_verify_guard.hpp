#pragma once
#include <cstdint>
#include "strata/aplan_observation.hpp"
namespace strata::kernels {
// SYCL-only guarded variants; existing CUDA/HIP APIs and kernels unchanged.
void wait_verify_ready(const uint32_t* flag, uint32_t ring, const uint32_t* skip,
                       int32_t* discard_counts, void* stream, strata::aplan::Wait* observation = nullptr);
void copy_verify_plan(int32_t* dst, const int32_t* src, long long n,
                      const uint32_t* skip, uint32_t ring, const uint32_t* flag, void* stream, strata::aplan::Device* observation = nullptr);
void resident_plan_observed(const int32_t* ids, int n_entries, int k, const int32_t* res_layer, int n_expert,
    const uint8_t* cache_base, const unsigned long long* slot_off, long long blob, int32_t* plan,
    long long capx, uint32_t* skip, uint32_t ring, void* stream, strata::aplan::Device* observation);
}
