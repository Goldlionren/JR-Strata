# v0.1.39 FastFix implementation

Base: `18f7c3e8a4f9f0ba6e948f60614f95cc551347b7`, verified against the preserved Git bundle. Isolated branch `jr-b60-sycl-v0.1.39-fastfix`. No production files changed.

## Allocation safety

Selectively backport RC1's `arena_alias_check`, bounded retry/cleanup and chunked compute zero-fill helpers. Check expert cache, DeviceArena and verifier allocations without changing their sizes or layout. Preserve the free-VRAM check and original expert ranking. Alias verification destroys only new, uninitialized allocations. The check samples each 64 KiB block; it does not certify every byte of a weight tensor. Full expert readback remains a separate GPU gate.

`fastfix_memory_safety` checks real device memory, synthetic persistent-alias rejection, retry limits and physical-memory bounds. GPU execution is pending. No performance claim yet.

Coherent host allocation helpers are included here for the next independently reviewable synchronization patch. They use Level Zero uncached host memory with matching ownership-aware free; no device driver changes.
