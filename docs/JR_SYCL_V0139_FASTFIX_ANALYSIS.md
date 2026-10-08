# v0.1.39 FastFix focused analysis

## Evidence and limits

Base `18f7c3e8a4f9f0ba6e948f60614f95cc551347b7` matches the preserved historical bundle/tag. The original checkout and release executable remain forensic references. Read-only comparison used upstream v0.1.40 and the exact v0.1.40.2/v0.1.40.3 tags in the RC1 repository. No newer engine was merged.

The previous Docker restoration produced `root!!!!!` during the 1,036-token request: 28.7 tok/s, 10,831 GPU experts (17.57 GiB), 13,745 missing experts mirrored (22.40 GiB), no contemporaneous GPU reset. Its full response and process I/O are preserved in `/data/strata-lab/Strata/logs/jr-v0139-restoration/20261008/`. The archived 2,932-token/33.5 tok/s record lacks full correctness qualification and complete per-request runtime identity. Neither is a valid correctness-equivalent baseline.

The symptom alone does not identify the cause. There is no archived tensor trace proving a stale PLE row, late MTP write, alias or expert timeout at that exact token. These remain candidate mechanisms until an independent numerical or fault diagnostic demonstrates one.

## What is already correct

- `sycl/src/core/verify.cpp`, `Verifier::run`: synchronous n-gram `gather_batch`, checked return and host fence occur before graph submission. The later RC1 prefetch/no-host staging omission is absent. Preserve this sequence; add independent PLE tests.
- `sycl/src/core/session.cpp` and `verify.cpp`: `ext_oneapi_empty() ? 0 : 1` already correctly translates Boolean completion. No duplicate Boolean fix.
- `sycl/include/strata/sycl_doorbell.hpp`: JR already uses uncached Intel loads and system fences. Preserve those instead of reverting to upstream v0.1.40's older polling.
- `sycl/src/core/mtp.cpp`, `MtpDrafter::draft`: every graph waits before reading the draft ID/probability or launching the next draft. The newer asynchronous MTP poll repair is not applicable wholesale.
- The original native IQ3_XXS kernels, verifier graph structure, routing and chunked full Host Mirror remain unchanged.

## Missing protections repaired

1. Bounded GPU wait kernels silently fell through on expiry. Sticky readiness diagnostics now prevent returning such a token/window as successful; the serve engine terminates on failure. This does not cancel in-flight kernels or establish the historical corruption's cause.
2. Ordinary mapped host allocations lacked upstream uncached Level Zero allocation. Port that allocator/free pair for handoffs, keeping the existing graph schedule.
3. Existing completion waits did not report async errors, and DPCT's handler swallowed them. Propagate them at the existing completion boundaries. No additional per-layer waits.
4. No large-allocation alias verification; the cache used one many-GiB memset. Backport bounded alias checking/retry and compute zeroing, retaining sizes/layout/free-memory checks.
5. Incomplete no-host mirror coverage previously warned and continued. Reject startup in that unsafe configuration.
6. Completed MTP token/probability outputs now receive range/nonfinite checks. These cannot detect every semantically wrong finite output; long-form correctness remains required.

## Runtime and comparison controls

Preserved image ID/digest `sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`. Historical executable SHA256 `ea9111a0542addb7446fb5aee2c9419defd77d341f0f982f696bbf9f67007313` reports compiler2026.1.1. Image runtime: SYCL2026.1.0, UR0.12.0, Level Zero1.32.0. Build mounts the existing2026.1.1 compiler read-only; GPU execution uses the stock preserved image without that mount. No oneAPI2025 substitution or causal claim about2026.

Original ranking SHA256 `8f59b4aa8873209dff11c11e37bcda9529a1335b724a1afeea37bf6388975baf`. Keep historical auto cache,768MiB reserve,131072 context, INT8/32768 resident KV, prefill4096, spec4/min-p0.5, original model/pack/MTP. A device-only profile and separate-engine MTP-off checks are isolation controls, not an unreported default change. PLE Direct remains the historical default; mmap throughput tuning is outside this surgical task.

Performance and GPU gates are pending until the bounded maintenance run. No claim of recovered20+tok/s or solved corruption follows from source inspection or CPU tests.

## Observed GPU evidence (supersedes pending status above)

The first long request reached a real bounded expert-readiness expiry at ring33, after306 delivered tokens. This confirms silent fall-through was a live correctness risk in the historical host-assisted path: a later flag reaching48 does not prove its data was ready when ring33 was consumed. It does not establish that the earlier1036-token`root!!!!!` has exactly the same cause.

A subsequent page fault/reset on engine exit blocks further GPU tests. The newly introduced timeout-return placement skipped the existing expert copy-queue drain; this demonstrable dependency error is corrected offline. Its exact relationship to the fault address still requires validation. The committed correction has no GPU PASS claim. MTP-off and device-only arms remain unexecuted, so neither MTP nor CPU-assisted routing can yet be isolated as the sole cause.

Recommendation: retain RC1. The next narrow investigation, after reviewing this failure, is readiness ring/channel diagnostics and a safe failure-teardown regression, followed by MTP-on/off isolation. Do not change ranking, quantization, residency budget or blanket timeouts to hide the failure. No new GPU window is initiated by this report.


## P0 ring-timeout offline follow-up (2026-10-09)

The current candidate is an **offline-only lifecycle/readiness repair**, not the failed GPU-tested ELF or the intermediate copy-drain-only build. See [timestamp/root-cause classification, source changes and CPU evidence](JR_SYCL_V0139_FASTFIX_RING_TIMEOUT.md) and the [new 45-minute gated GPU plan](JR_SYCL_V0139_FASTFIX_P0_GPU_PLAN.md). The old maintenance command remains blocked. Current hashes are in `tools/fastfix/p0-candidate.json` and `p0-frozen.json`; no new GPU PASS or throughput result exists.

11 CPU lifecycle/readiness cases, 90 PLE oracle windows, existing reader/output/harness checks and 10 CPU maintenance/profile gates passed. The exact producer responsible for ring33 is still unresolved. New guards reject unready plans, retain GPU owners until verified completion, preserve first-timeout diagnostics and provide a supported T=1 no-Decode-drafting control. Default Spec4, ranking, cache layout and historical Docker runtime are preserved. RC1 stays active and unchanged. Fresh maintenance approval is required.
