# FastFix Adaptive Mirror validation results — window02 PASS

Current production decision (2026-10-09): **FastFix ACTIVE/ENABLED; RC1 INACTIVE/DISABLED and deprecated.** The operator's final migration decision supersedes earlier RC1-restoration/fallback recommendations below. The same validated engine now serves native Chat/Monitor/API at127.0.0.1:18083, with128K configured context,10831 GPU experts, full13745 mirror, Adaptive ON and MTP4. [Production results](JR_SYCL_V0139_FASTFIX_PRODUCTION_REPORT.md) and [current operations](JR_SYCL_V0139_FASTFIX_PRODUCTION_OPERATIONS.md). Historical validation reports remain dated evidence, not current production policy. No automatic RC1 fallback.


Latest measured result (2026-10-09): **window02 PASS — PROMOTION ELIGIBLE** under the current sustained ≥20tok/s gate. The explicitly approved22GiB unloaded threshold passed at22.485607GiB; separate loaded headroom647MiB passed512MiB. Seven GPU safety tests, captured readiness, actual GGUF mirror exchange and delayed per-layer payload probes passed. Adaptive ON/MTP4 generated2048 actual tokens at25.3 Decode tok/s with no corruption/readiness failure/GPU fault. Three subsequent requests passed; Chinese/math Decode remained17.2/11.2tok/s. RC1 was restored within188.111s; no permanent cutover occurred. [Full results, limitations and raw evidence](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_RESULTS_WINDOW02.md).

All reports below are historical stage records with their original failures/blockers preserved. The new result applies only to the unchanged `8d2ac886…21ef04e` ELF/source `be3105e`; it does not reclassify failed older binaries or optional kernel tests. Fresh production startup/restart/endurance and real128K prompt regression are not claimed by this narrow run.


## Preserved prior-stage record

Approved prepared HEAD:`8b5c202d2dfd45e2a893168c1dde03aefc3c1f5f`. Experimental SHA256 verified:`8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`. The source, binary, model/profile metadata, original ranking and historical Docker image matched the38-file candidate manifest. No engine/configuration/safety check was modified during execution.

Window start2026-10-09T12:11:28.392245+11:00; hard deadline12:31:28. Experimental cutoff12:26:28. Preflight stopped at+3.800s after graceful RC1 shutdown. RC1 recovery completed at+27.206s, approximately12:11:55.598+11:00. The window was closed; no candidate GPU container, safety test, captured probe or inference request was started. No further maintenance run occurred.

## First blocker and responsibility

The prepared plan required **23GiB** free GPU memory after RC1 exit. XPU-SMI reported **24143736832 bytes =22.485607GiB**, leaving a552325120-byte (526.738MiB) shortfall against that gate. Host MemAvailable was59827032KiB =57.0555GiB, above the32GiB requirement. B60 PCI0000:07:00.0/8086:e211 and device state normal were verified; no new GPU faults/reset were present. RC1 server984699 and engine985485 had both exited.

**The23GiB minimum in the plan was an overly conservative preparation error.** The observed free-memory value exactly matches the preserved prior normal RC1 launch record and this restoration's original launcher record. These observations do not establish a new competing allocation or prove that the unchanged10831-expert candidate cannot fit. The candidate's actual loaded headroom was not measured in this window. We did not lower the approved gate and continue testing.

The unchanged production RC1 launcher uses its own previously validated **22GiB GPU /40GiB host** startup gate. Restoration satisfied those original limits without altering any production file. A future plan should explicitly reconcile its pre-load requirement with observed runtime memory accounting and retain the independent loaded512MiB headroom check, exact10831-slot/cache-byte requirement, physical allocation bound and alias checks. A revised resource gate must be reviewed before another GPU execution; this report does not authorize it or certify candidate fit.

## Acceptance matrix

| Requirement | Result | Evidence |
|---|---|---|
| Frozen candidate/build/ranking/runtime identity | PASS |38-file verification; approved HEAD and experimental ELF matched|
| RC1 healthy/idle before cutover | PASS |Two status/metrics samples, no busy/queued request or changing request count; running frozen hash|
| Graceful RC1 shutdown | PASS |Existing systemctl lifecycle; server and engine exited; journal reports stopped|
| B60 identity/health | PASS |PCI8086:e211,0000:07:00.0; XPU-SMI normal|
| Prepared free-memory gate | BLOCKED |22.485607GiB reported, below planned23GiB; host RAM sufficient|
| Seven GPU safety tests | BLOCKED |Not executed|
| Adaptive Mirror ownership/weight/event probe | BLOCKED |Not executed|
| Per-layer Payload captured probe | BLOCKED |Not executed|
| Adaptive ON/MTP4 real execution and A-plan progress | BLOCKED |No candidate loaded; no swaps or verifier windows|
|2048 actual outputs/correctness | BLOCKED |No candidate inference|
| Sustained Decode ≥20tok/s | BLOCKED |N/A; no complete sustained response, no prefixes benchmarked|
| Candidate memory stability / clean shutdown / restart | BLOCKED |Candidate never started|
| No new GPU faults/reset during window | PASS |Preserved kernel journal, normal device state; no candidate stress occurred|
| Experimental process absence | PASS |No candidate/probe container or18086 listener remained|
| Frozen RC1 restoration | PASS |Frozen executable, original32K/ranking/profile/unit, API generation/UI/monitoring verified|
| Conditional production promotion | BLOCKED |Required correctness, sustained performance and restart gates remain unexecuted|

No failed GPU probe or inference evidence is being hidden: there was no candidate GPU execution. CPU/sanitizer results in the offline report remain valid; they are not GPU acceptance.

## Restored production

Service:`jr-strata-sycl-rc1.service`, active/running/enabled, no unexpected restart. Server PID1383233, engine PID**1383707**.

Running ELF SHA256:`cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`.

Original profile:`strata-swift-iq3_xxs-b60-32k.json`. `/v1/models` reports32768 context. Binary, profile, installed unit and original expert ranking hashes before/after are identical. API smoke returned`42` for6×7,3 actual completion tokens; this is a restoration check, not a sustained throughput measurement. Native UI HTTP200, `/status`, `/metrics` and `jr-sycl-watch --json` respond; monitoring reported zero recent B60 fault lines. Production URL:`http://127.0.0.1:18083/`.

GPU accounting: physical25669140480 bytes, max single allocation24385683456 bytes; available after RC1 stop24143736832 bytes. Kernel7.0.0-34-generic, XPU-SMI driver_version17010844. No driver/runtime changes were made. Actual candidate-loaded SYCL/UR/LevelZero mappings and native expert/mirror residency are N/A because its container was never started.

## Updated promotion decision

The operator subsequently authorized conditional promotion at **≥20 sustained Decode tok/s**, with25–30 only an optimization goal. Retain that decision for future validation. It still requires Adaptive ON/MTP4, a correct full2048-token response, mirror/payload/readiness checks, zero corruption/faults, clean shutdown and fresh reliable restart. Do not attribute RC1 smoke throughput or historical failed-prefix rates to this candidate.

RC1 remains the active default. No FastFix production service, startup-policy change or port18083 cutover was performed. Once the revised resource preflight and actual GPU gates pass, a controlled deployment may follow the conditional authorization; recovery time must never be consumed by promotion.

Raw evidence:`logs/fastfix/mirror-repair-window-01/`. Committed copy:`docs/jr-v0139-fastfix-evidence/mirror-repair-window-01/`, including the exact execution controller, approved plan/manifest, first failure, free-memory report, stop/start journals, smoke output and restoration identities.

Restored RC1 native metrics: `{"expert_cache_mib": 15348, "expert_slots": 9248, "kv": "int8", "kv_resident": 0, "max_context": 32768, "mtp_max": 4, "spec": 6, "vram_free_mib": 2936}`.
