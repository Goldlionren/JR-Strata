#pragma once
#include <cmath>
#include <cstdint>
namespace strata::core {
inline bool valid_draft_result(int32_t token, float probability, int64_t vocab) {
    return token >= 0 && token < vocab && std::isfinite(probability) && probability >= 0.0f && probability <= 1.0f;
}
}
