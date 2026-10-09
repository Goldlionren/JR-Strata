# v0.1.39 FastFix implementation

Current production decision (2026-10-09): **FastFix ACTIVE/ENABLED; RC1 INACTIVE/DISABLED and deprecated.** The operator's final migration decision supersedes earlier RC1-restoration/fallback recommendations below. The same validated engine now serves native Chat/Monitor/API at127.0.0.1:18083, with128K configured context,10831 GPU experts, full13745 mirror, Adaptive ON and MTP4. [Production results](JR_SYCL_V0139_FASTFIX_PRODUCTION_REPORT.md) and [current operations](JR_SYCL_V0139_FASTFIX_PRODUCTION_OPERATIONS.md). Historical validation reports remain dated evidence, not current production policy. No automatic RC1 fallback.


Latest measured result (2026-10-09): **window02 PASS — PROMOTION ELIGIBLE** under the current sustained ≥20tok/s gate. The explicitly approved22GiB unloaded threshold passed at22.485607GiB; separate loaded headroom647MiB passed512MiB. Seven GPU safety tests, captured readiness, actual GGUF mirror exchange and delayed per-layer payload probes passed. Adaptive ON/MTP4 generated2048 actual tokens at25.3 Decode tok/s with no corruption/readiness failure/GPU fault. Three subsequent requests passed; Chinese/math Decode remained17.2/11.2tok/s. RC1 was restored within188.111s; no permanent cutover occurred. [Full results, limitations and raw evidence](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_RESULTS_WINDOW02.md).

All reports below are historical stage records with their original failures/blockers preserved. The new result applies only to the unchanged `8d2ac886…21ef04e` ELF/source `be3105e`; it does not reclassify failed older binaries or optional kernel tests. Fresh production startup/restart/endurance and real128K prompt regression are not claimed by this narrow run.


## Preserved prior-stage record

Approved mirror window01 is **BLOCKED at the planned23GiB free-memory gate**, before any candidate GPU test. Actual clean free memory22.485607GiB matched the prior normal launch record; RC1 was safely restored within27.206s. [Actual results and first blocker](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_RESULTS.md). Conditional promotion now requires≥20 sustained Decode tok/s plus all correctness/safety/restart gates; it remains BLOCKED because GPU validation was not executed.

Current offline update: adaptive GGUF slot exchange and independent per-layer host payload repair are implemented in separate commits. CPU/reference and sanitizer gates pass; repaired-engine GPU acceptance and performance remain **BLOCKED / not executed**. Production RC1 remains unchanged. See [the repair report](JR_SYCL_V0139_FASTFIX_ADAPTIVE_MIRROR_REPAIR.md), the new candidate manifest and [Adaptive ON plan](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_PLAN.md). Historical failures/results below are preserved and do not qualify the new binary.

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


## Latest P0 GPU outcome — window closed (2026-10-09)

**FAIL: readiness timeout remains; no new GPU faults; RC1 restored.** [Full measured results and recovery](JR_SYCL_V0139_FASTFIX_P0_GPU_RESULTS.md) supersede the earlier “GPU pending” state. Seven GPU safety tests and the event probe passed. T=1 and MTP-on512-token controls passed at20.3 and27.9tok/s. The2,048-token request stopped after1,186 tokens with `A-plan ring47 layer46 observed40 skip0`, window896/T1/position1264. No successful sustained2,048-token result exists. Failed-prefix33.9tok/s is not accepted performance.

The controller suspended restoration for assessment; all experimental processes exited, B60 resources returned, no kernel fault or unsafe-drain marker appeared, and unchanged RC1 was restored and verified at330.09 seconds. RC1 engine199664, original32K configuration, active/enabled. The window is closed; do not rerun this failing candidate. Binary/hash/ranking/runtime remain unchanged. Full raw evidence and the initial restoration incident are preserved.


## A-plan offline follow-up — 2026-10-09

[Focused handshake analysis](JR_SYCL_V0139_FASTFIX_APLAN_ANALYSIS.md) identifies the default adaptive-swap/static-mirror coverage hole, but the archived failed expert is unknown. Opt-in diagnostics and15 CPU state/fault cases are prepared; no timeout cure or new GPU performance is claimed. [Proposed narrow diagnostic plan](JR_SYCL_V0139_FASTFIX_APLAN_GPU_PLAN.md) requires new authorization. The previously failed14db752… ELF is preserved at `dist/failed-p0-window-01/strata`; `build-fastfix/strata` now contains the separately hashed diagnostic build recorded in `tools/fastfix/aplan-candidate.json`. RC1 stayed running and unchanged.


## A-plan adaptive isolation — window01 completed

[Measured window01 results](JR_SYCL_V0139_FASTFIX_APLAN_GPU_RESULTS.md): adaptive-off PASS,79 prompt/1536 generated tokens,12.0tok/s Decode,2.52s observed TTFT,820/1373 accepted drafts. Probe passed; no new GPU fault or unsafe teardown. Adaptive-on was never launched: after static teardown344.27s, its390s worst-case bound exceeded the600s experimental cutoff. Causal comparison remains BLOCKED; no exact archived failed expert was recovered. RC1 was restored/verified at400.49s, frozen hash,32768 context, original9248-expert profile, active/enabled. Authorization closed; no promotion or automatic further GPU run.
