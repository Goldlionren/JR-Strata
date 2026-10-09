#pragma once
#include <cassert>
#include <cstddef>
#include <cstdint>
namespace strata::verify_payload {
// Stable address for one layer/window row, shared by graph publication and CPU consumption.
// A verifier owns only [layer_begin, layer_end), so split stages do not allocate foreign layers.
constexpr size_t row(int64_t layer, int64_t layer_begin, int64_t max_rows, int64_t token_row) {
    assert(layer >= layer_begin && max_rows > 0 && token_row >= 0 && token_row < max_rows);
    return (size_t)(layer - layer_begin) * (size_t)max_rows + (size_t)token_row;
}
} // namespace strata::verify_payload
