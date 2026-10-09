# FastFix validation results — current Adaptive Mirror window02 PASS

Current production decision (2026-10-09): **FastFix ACTIVE/ENABLED; RC1 INACTIVE/DISABLED and deprecated.** The operator's final migration decision supersedes earlier RC1-restoration/fallback recommendations below. The same validated engine now serves native Chat/Monitor/API at127.0.0.1:18083, with128K configured context,10831 GPU experts, full13745 mirror, Adaptive ON and MTP4. [Production results](JR_SYCL_V0139_FASTFIX_PRODUCTION_REPORT.md) and [current operations](JR_SYCL_V0139_FASTFIX_PRODUCTION_OPERATIONS.md). Historical validation reports remain dated evidence, not current production policy. No automatic RC1 fallback.


Latest measured result (2026-10-09): **window02 PASS — PROMOTION ELIGIBLE** under the current sustained ≥20tok/s gate. The explicitly approved22GiB unloaded threshold passed at22.485607GiB; separate loaded headroom647MiB passed512MiB. Seven GPU safety tests, captured readiness, actual GGUF mirror exchange and delayed per-layer payload probes passed. Adaptive ON/MTP4 generated2048 actual tokens at25.3 Decode tok/s with no corruption/readiness failure/GPU fault. Three subsequent requests passed; Chinese/math Decode remained17.2/11.2tok/s. RC1 was restored within188.111s; no permanent cutover occurred. [Full results, limitations and raw evidence](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_RESULTS_WINDOW02.md).

All reports below are historical stage records with their original failures/blockers preserved. The new result applies only to the unchanged `8d2ac886…21ef04e` ELF/source `be3105e`; it does not reclassify failed older binaries or optional kernel tests. Fresh production startup/restart/endurance and real128K prompt regression are not claimed by this narrow run.


## Preserved prior-stage record

Approved mirror window01 is **BLOCKED at the planned23GiB free-memory gate**, before any candidate GPU test. Actual clean free memory22.485607GiB matched the prior normal launch record; RC1 was safely restored within27.206s. [Actual results and first blocker](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_RESULTS.md). Conditional promotion now requires≥20 sustained Decode tok/s plus all correctness/safety/restart gates; it remains BLOCKED because GPU validation was not executed.

Current offline update: adaptive GGUF slot exchange and independent per-layer host payload repair are implemented in separate commits. CPU/reference and sanitizer gates pass; repaired-engine GPU acceptance and performance remain **BLOCKED / not executed**. Production RC1 remains unchanged. See [the repair report](JR_SYCL_V0139_FASTFIX_ADAPTIVE_MIRROR_REPAIR.md), the new candidate manifest and [Adaptive ON plan](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_PLAN.md). Historical failures/results below are preserved and do not qualify the new binary.

Do not deploy FastFix. RC1 is restored, active and enabled. One bounded window began2026-10-09 00:37:38 Australia/Sydney; verified restoration completed within393 seconds of that original start. A fixture-only first segment restored RC1, and the continuation inherited the same deadline. Testing stopped on the first runtime readiness failure and subsequent GPU fault. No MTP-off/device-only comparison or further GPU experiment followed.

Tested source/controller: `cbaf04c` (engine source `c2dfde6`); tested engine SHA256 `faa0efb9b9d2314f2e9140e1b45e9f5d275331b278b086b339b306fb15a0121e`, preserved at `dist/failed-window-01/strata`. The later copy-drain correction is offline-only and must not inherit these GPU results.

## Acceptance matrix

| Criterion | Status | Actual evidence |
|---|---|---|
| CPU PLE numerical reference | PASS |90 windows, T1/4/6, three histories, repeated/changing rows, Direct/mmap;90/110-byte Reader tests|
| GPU PLE staging/graph ordering | PASS |90 independent IQ4_NL reference windows, delayed reads and gather-error gate|
| Legacy full PLE block oracle | BLOCKED |Exact Q2_0 table/dense/capture fixtures unavailable; exit2 before GPU work|
| Seven focused safety/numerical tests | PASS |alias/retry, KV Q8, streamed KV, IQ multi, native grouped, activation quantization, independent PLE staging|
| Readiness diagnostic probe | PASS |12 rounds; all three timeout latches and completed outputs|
| Queue/expert readiness in real inference | FAIL |ring33 timeout after306 delivered long-response tokens; host seq48|
| MTP-on short correctness | PASS |English, Chinese, Python assertions, math correct|
| Matched MTP-on/off | BLOCKED |Stopped after runtime failure; off arm never started|
| Complete expert coverage/cache strategy | PASS |10831 resident +13745/13745 mirrored; same ranking/auto strategy|
| Large-allocation alias sampling | PASS |512MiB probe, eight-failure rejection and guarded model startup; no reported alias mismatch|
| End-to-end memory/lifecycle integrity | FAIL |ccs reset/page fault on error exit; not a full weight-readback certificate|
|2048+ token generation | FAIL |306 delivered, error; no successful final usage/timing record|
|No output corruption in acceptance workload | BLOCKED |No`!!!!!` in captured prefix/short responses, but long workload aborted|
|≥20tok/s sustained usable target | BLOCKED |Partial rate cannot qualify sustained performance|
|Zero GPU faults/resets | FAIL |One recorded ccs reset and associated page fault at00:41:20|
|Graceful FastFix teardown | FAIL |Server stopped and container exited, but engine threw Level Zero error during exit|
|RC1 restoration | PASS |After hardware assessment: PID1587016, frozen hash,32K/9248 slots, actual generation, monitoring, no new restoration fault|
|Production readiness | FAIL |Explicit reexecution/deployment blocker retained|

## Measured requests

Same original Swift IQ3_XXS model/pack/ranking, stock Docker runtime,131072 configured context, INT8 KV/32768 resident, prefill4096,768MiB reserve, spec4/min-p0.5 with historical suffix behavior, temperature0/seed42. These are single measurements per prompt, not medians of repeated benchmarks. Prompt tokens are actual API counts.

|Task|Prompt|Generated|Prefill tok/s|Decode tok/s|TTFT s|Accepted/offered drafts|Quality|
|---|---:|---:|---:|---:|---:|---:|---|
|English|26|54|19.0|16.6|1.458|31/45|Correct salt/freezing explanation|
|Chinese|26|48|21.4|17.8|1.297|24/35|Correct Chinese explanation|
|Python|43|53|32.0|20.2|1.401|36/45|Executable formula and independent assertions pass|
|Mathematics|43|146|35.5|23.6|1.266|100/123|Width6, area54; math correct, verbose beyond requested80 words|
|Garden manual|79|306 delivered|N/A final|N/A final|2.419|N/A|Aborted; requested2048|

Short-request aggregate draft acceptance191/248=77.0%; this includes suffix drafts and is not MTP-only. The long request's server progress log reported26.4tok/s when reporting the error, but no successful engine DONE/final API timing exists. It is **partial failed-run throughput**, not a sustained result or performance target PASS. No 2048-token claim.

Existing decode wall-time instrumentation reports verifier92.98–142.89ms/window and draft8.86–10.01ms/window for the four short requests. GPU-reach wait73.87–99.67ms/window and host work13.45–45.43ms/window overlap GPU execution; do not sum them as independent GPU timings or call them measured kernel latency. CPU experts remain active despite complete mirror coverage in this historical host-assisted configuration.

## Resource and I/O evidence

Model startup:10831 GPU experts/17.57GiB;13745 mirrored experts/22.40GiB;648MiB free VRAM after graph/head setup. Alias protection stayed enabled. No cache-size reduction.

Long-request samples (includes prefill and failed request tail, not warm-decode-only):

- Peak engine VRAM24,507,412KiB; GTT25,810,816KiB. Device accounting can include overlapping allocations; do not sum GTT and RSS.
- Minimum host MemAvailable31,581,688KiB; peak process RSS1,836,732KiB; process swap0. Pinned allocations are not fully represented by RSS.
- `read_bytes` +3,149,996,032; `rchar` +7,907,448,206; `syscr` +21,059; major faults +123. System swap-in/out +0/+0.
- Sampled GPU clock2400MHz; sampled power76.56–108.71W.
- Full PLE-specific read count/cache-hit/gather-time attribution: N/A in this historical build. These process reads include auxiliary/model/expert activity and cannot all be attributed to PLE.
- Too few/short requests to establish leak freedom. No RAM exhaustion observed, but GPU error makes overall memory/lifecycle gate FAIL.

## Failure chronology and recovery

At00:41:19 the server returned `verify: expert readiness device wait expired at ring33; window discarded; host seq=48; restart engine before reuse`. At00:41:20 xe reported ccs engine reset, ASID6195, address`0x0000c71e38990000`, FaultType0/AccessType0/FaultLevel4, followed by`-ENOENT`. Engine exit threw `UR_RESULT_ERROR_UNINITIALIZED`. The automatic restorer correctly withheld restart.

Read-only assessment confirmed experimental server1563446/engine1563537 and container were gone, port18086 released, B60 normal, free VRAM24,143,736,832bytes (same as pre-run idle), adequate host RAM, and no continuing faults. `xpu-smi health` temperature sensor is unsupported: N/A. Only then was original RC1 started. Running hash `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`; server1586519, engine1587016; smoke: “2 plus 2 equals4.” No new fault during restoration. Original profiles/unit/ranking/binary hashes match.

The new timeout early return preceded an existing copy-queue drain. That error-path dependency is corrected offline in`355ebe7`; no GPU retest is claimed. The timeout itself remains unresolved; increasing every timeout or assuming PLE/MTP caused it would exceed the evidence.

## Historical comparison

Prior28.7tok/s/1036 tokens had`root!!!!!`; archived33.5tok/s/2932 tokens lacks complete qualification. FastFix's short16.6–23.6tok/s and failed long-prefix26.4tok/s neither prove recovered sustained performance nor a correctness-equivalent regression. No unsafe original binary was rerun.

Raw evidence: `logs/fastfix/window-01/`, `logs/fastfix/window-01-resume/`, build/CPU logs under `logs/fastfix/`. Compact committed evidence and SHA256 inventory: `docs/jr-v0139-fastfix-evidence/`.


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
