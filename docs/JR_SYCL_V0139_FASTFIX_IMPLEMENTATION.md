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

The vendored DPCT async handler previously printed and swallowed every exception. It now rethrows the reported exception so `wait_and_throw` can reach the engine's existing fatal-error path. Merely changing wait calls without this correction would not propagate errors on these queues.

## Frozen build for acceptance

Source through `be83153` (engine's last source change `c2dfde6`), compiler2026.1.1, AOT bmg-g21, precise FP32 and subgroup32, same historical ggml source cache. Experimental engine SHA256:
`faa0efb9b9d2314f2e9140e1b45e9f5d275331b278b086b339b306fb15a0121e`.
Stock image loader resolves all libraries; recorded in `docs/jr-v0139-fastfix-evidence/runtime-loader.txt`. Original executable/image unchanged. `tools/fastfix/frozen.json` pins the exact engine, probes, profile and controller inputs.

Final CPU tests pass (`logs/fastfix/cpu-WhFm2i`). Preserved build logs include a corrected missing C++ header, corrected catch-variable shadowing, and an abandoned synthetic SYCL exception-list test that could not use the runtime's private constructor. That abandoned test is not marked PASS. Handler propagation is source-checked and compiled; real async-fault injection is not claimed. Optional historical S2/GR failures are not concealed or reclassified by this task.

## GPU failure and subsequent offline correction

The tested binary `faa0efb9…a0121e` passed the focused probes and four short requests, then rejected a long request after306 delivered tokens with `expert readiness device wait expired at ring33; host seq=48`. At engine exit a ccs reset/page fault occurred, followed by `UR_RESULT_ERROR_UNINITIALIZED`. This is a failed acceptance; no FastFix promotion.

Review found an error in the new timeout rejection placement: it returned before the pre-existing `copy_->wait()` boundary. Compute completion does not establish copy completion. The offline correction moves timeout rejection after `copy_->wait_and_throw()` and before output consumption; a source regression asserts that ordering. This repairs the demonstrable missing cleanup dependency but is **not yet GPU-validated**, and the exact causal chain of the observed page fault is not proven from the fault address alone. No further GPU experiments run after the fault.

After read-only assessment (experiment gone, normal B60, pre-run free memory restored, no continuing fault), unchanged RC1 was restored and smoke-tested successfully. The hardware health sensor command is unsupported on this driver; it is recorded N/A, not passed. The production binary, profile, ranking and unit hashes remain unchanged.

Final offline cleanup candidate (`355ebe7` engine source) built successfully. SHA256 `39701868b8532bc20c03faf8ab0009cf881f0611462a09914739c9d5d6696996`; **GPU NOT TESTED**. The failed tested artifact remains separately preserved with SHA256 `faa0efb9b9d2314f2e9140e1b45e9f5d275331b278b086b339b306fb15a0121e`. CPU source-order regression passes after the move. Production remains RC1; FastFix controller is blocked.


## P0 ring-timeout offline follow-up (2026-10-09)

The current candidate is an **offline-only lifecycle/readiness repair**, not the failed GPU-tested ELF or the intermediate copy-drain-only build. See [timestamp/root-cause classification, source changes and CPU evidence](JR_SYCL_V0139_FASTFIX_RING_TIMEOUT.md) and the [new 45-minute gated GPU plan](JR_SYCL_V0139_FASTFIX_P0_GPU_PLAN.md). The old maintenance command remains blocked. Current hashes are in `tools/fastfix/p0-candidate.json` and `p0-frozen.json`; no new GPU PASS or throughput result exists.

11 CPU lifecycle/readiness cases, 90 PLE oracle windows, existing reader/output/harness checks and 10 CPU maintenance/profile gates passed. The exact producer responsible for ring33 is still unresolved. New guards reject unready plans, retain GPU owners until verified completion, preserve first-timeout diagnostics and provide a supported T=1 no-Decode-drafting control. Default Spec4, ranking, cache layout and historical Docker runtime are preserved. RC1 stays active and unchanged. Fresh maintenance approval is required.
