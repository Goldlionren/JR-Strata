# v0.1.39 FastFix implementation

Base: `18f7c3e8a4f9f0ba6e948f60614f95cc551347b7`, verified against the preserved Git bundle. Isolated branch `jr-b60-sycl-v0.1.39-fastfix`. No production files changed.

## Allocation safety

Selectively backport RC1's `arena_alias_check`, bounded retry/cleanup and chunked compute zero-fill helpers. Check expert cache, DeviceArena and verifier allocations without changing their sizes or layout. Preserve the free-VRAM check and original expert ranking. Alias verification destroys only new, uninitialized allocations. The check samples each 64 KiB block; it does not certify every byte of a weight tensor. Full expert readback remains a separate GPU gate.

`fastfix_memory_safety` checks real device memory, synthetic persistent-alias rejection, retry limits and physical-memory bounds. GPU execution is pending. No performance claim yet.

Coherent host allocation helpers are included here for the next independently reviewable synchronization patch. They use Level Zero uncached host memory with matching ownership-aware free; no device driver changes.

## Handoff and draft completion

Existing Boolean queue completion and uncached GPU loads are retained. Allocate host-polled flags/results through the upstream Level Zero uncached helper and use its matching free. A second flag word records a bounded device-spin expiry; the host clears it only before a new completed window and rejects the result after completion. Failed verifier/MTP calls already terminate the serve engine; they do not continue using corrupted recurrent state. This diagnostic rejects output from a failed graph; it does not cancel already submitted kernels. The original spin limit is unchanged, with no new per-layer queue drain.

Existing graph-completion waits become `wait_and_throw` at the token/window/draft consumption boundaries. Historical MTP already waits for each draft; no new event architecture or extra wait is introduced. Completed draft IDs and probabilities must be finite/in range. Device-only startup now rejects incomplete mirror coverage instead of merely warning. Large MTP allocations receive the same alias guard; their sizes remain unchanged.

## PLE: existing correct ordering retained

Historical `Verifier::run` computes rows, synchronously gathers, propagates failure, fences, then submits the graph. This already covers mixed resident/mirrored experts and `STRATA_VERIFY_NO_HOST`. It does not have RC1's later delayed-prefetch omission. No PLE execution rewrite is necessary. Focused tests reuse the PLEFix independent IQ4_NL reference with the historical gather sequence: 90 windows, T=1/4/6, repeated/changing rows, three histories, Direct/mmap, delayed I/O and failure before submission. Actual graph visibility is a separate GPU test.
