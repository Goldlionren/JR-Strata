# FastFix Adaptive Mirror GPU retry window02 — PASS, PROMOTION ELIGIBLE

The approved retry completed all required GPU checks and one correct **2,048-token sustained generation at 25.3 Decode tok/s**. Adaptive ON and the original MTP Spec4 configuration remained enabled. No readiness timeout, coverage hole, stale payload, repeated `!!!!!`, GPU fault/reset or unsafe teardown occurred. RC1 was restored and verified; FastFix has **not** replaced production.

This meets the operator's current ≥20tok/s promotion-eligibility gate for the tested sustained workload. It is a single long request plus three short follow-ups, not a guarantee of general reliability or ≥20tok/s on every prompt. Permanent cutover, a fresh production startup and its health checks are separate operations.

## Exact identities and corrected resource gates

- Tested branch: `jr-b60-sycl-v0.1.39-fastfix`; prepared checkout HEAD `11e46f7f53d5cc45883fe6e6eac0f510c6f1df35`.
- Engine source commit: `be3105e7f66ef4f9668ef129a1938800954b1b3b`; no rebuild or inference-source change during this retry.
- Engine SHA256: `8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`.
- Actual-source Mirror/Payload probe SHA256: `a8e764fd2ee893bc6eb6d327f8eb2edb8e930a292df825153284c9d3afc3eae8`.
- Historical Docker image ID: `sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`.
- Same original Swift IQ3_XXS GGUF/pack/MTP assets and ranking. Ranking SHA256: `8f59b4aa8873209dff11c11e37bcda9529a1335b724a1afeea37bf6388975baf`.
- B60 `0000:07:00.0`, `8086:e211`; selected LevelZero device0 verified in Docker. Kernel `7.0.0-34-generic`; XPU-SMI driver_version `17010844`.
- Build compiler2026.1.1; existing stock runtime SYCL2026.1.0, UR0.12.0, LevelZero loader1.32.0. Live mappings confirm `libsycl.so.9.0.0`, both LevelZero UR adapters0.12.0, loader1.32.0 and Intel GPU library1.17.39758. No library/driver change.

The operator authorized exactly one resource-gate correction: **unloaded B60 free VRAM ≥22GiB**, independently of **loaded headroom ≥512MiB**. XPU-SMI `memory_free_size_byte` was **24,143,736,832 bytes =22.485607GiB**, using the same device/units as the archived baseline. Host MemAvailable was59,399,172KiB =56.647GiB, above32GiB. Initial loaded engine free headroom was **647MiB**. Loaded headroom is the engine's startup report, not a continuously refreshed minimum. The full model/cache budget and alias checks were unchanged.

The old frozen plan/38-file candidate manifest retain their historical preparation record, including the23GiB gate that blocked window01. The exact executed retry controller and explicit22GiB authorization are archived here; do not mistake the old plan for a new approval. Seven CPU resource-boundary/deadline checks, seven existing plan tests and all38 frozen hashes passed.

## Window and settings

Start: **2026-10-09T12:30:37.898370+11:00**. Experimental cutoff12:45:37.898; hard deadline12:50:37.898. Candidate teardown completed at+167.2s; verified RC1 restoration at **+188.111s**, approximately12:33:46.010. The window is closed. No additional GPU run or promotion used its remaining time.

The native experimental server ran at127.0.0.1:18086 under `jr-strata-fastfix-mirror-test.service`, Restart=no, SIGTERM, KillMode=process, SendSIGKILL=no and90s stop timeout. It loaded the historical Docker wrapper and frozen ELF. The execution profile changed only the log destination to a fresh window02 directory.

Original settings:10831 GPU experts/17990MiB (17.57GiB),13745/13745 missing experts mirrored (22.40GiB), adaptive4/96, original ranking, context131072, INT8 KV/resident32768, prefill4096, reserve768MiB, CLI Spec4/min-p0.5, PCIe fraction0.25, prompt cache0, temperature0/seed42/thinkingoff. The original host-assisted verifier path remains enabled. Native metrics `spec=6` describes maximum verifier capture T; `mtp_max=4` and frozen CLI `--spec 4` preserve the tested MTP semantics. Suffix drafting is unchanged.

## Acceptance matrix

| Gate | Verdict | Measured evidence |
|---|---|---|
| Frozen engine/model/profile/ranking/runtime | PASS |38 hashes; Docker running `/proc/1/exe` matches the approved ELF |
| RC1 identity/idleness and graceful stop | PASS |Two idle status/metrics samples, frozen hash, original systemd stop, server/engine exit |
| Unloaded22GiB and host32GiB gates | PASS |22.485607GiB free;56.647GiB MemAvailable; no active swapping at admission |
| Seven focused GPU safety tests | PASS |All seven exited0; logs/commands preserved |
| Captured readiness/event probe | PASS |Guarded plans, delayed readiness, skipped mirror plans, all timeout latches and host outputs |
| Actual GGUF Mirror ownership/weight/event probe | PASS |12 delayed generations/36 pair exchanges on layers0/32/46; independent full-blob hashes and reused captured resident plan |
| Per-layer Payload lifetime | PASS |Actual captured doorbells with GPU-ahead/host-delay, T1/4/6, split/unsplit and changing windows |
| Loaded512MiB headroom | PASS |647MiB at startup; no silent reduction of cache/residency |
| Adaptive ON and committed metadata coverage | PASS |14,066 swaps/251 generations across four requests; every generation has0 holes and replayed residency hash |
| Full2048 actual tokens / runtime output integrity | PASS |2048 actual output tokens; no invalid output, abnormal repetition or readiness error; length-capped |
| Sustained Decode≥20tok/s | PASS |2048 /80.7966s =25.348tok/s; API reports25.3, excludes prefill |
| Three follow-up functional requests | PASS |English, Chinese and independent math check; normal EOS |
| Bounded memory / no OOM | PASS, scoped |Same mirror/cache slots, GTT plateaus; ≥30.699GiB MemAvailable; no allocation error. Longer endurance/leak freedom untested |
| Zero new GPU faults/reset | PASS |Full window kernel journal, normal device state before recovery; process major faults are a different metric |
| Candidate graceful teardown/process absence | PASS |SIGTERM→native Server QUIT/engine exit; tracked drain completed, no unsafe marker; container/server/engine/18086 gone |
| Frozen RC1 restoration | PASS |Hash, original32K profile/ranking/unit, models, generation, native UI/status/metrics/watch, no new fault |
| Current promotion eligibility | PASS: PROMOTION ELIGIBLE |Current narrow correctness/safety/sustained-performance gates met; no permanent deployment performed |
| Complete requested3000-word garden manual | BLOCKED |2048-token cap ends mid-sentence; this is not a complete-answer quality PASS |
| Fresh candidate restart/endurance/real128K prompt | BLOCKED |Not part of this run; candidate started once and shut down cleanly |

Seven safety tests and observed durations: `fastfix_memory_safety`0.598s, `kv_q8_parity`0.693s, `kv_stream_parity`11.165s, `iq_multi_parity`1.747s, `native_grouped_parity`1.598s, `quantize_act_parity`0.650s, `fastfix_ple_staging`0.695s. The alias test refused eight injected unsafe allocations and passed a real512MiB scan; it is not full-cache byte readback. PLE tested90 independent Direct/mmap IQ4_NL windows with delayed I/O/error-before-submit. Readiness probe2.052s; Mirror/Payload probe9.276s. Optional historical GR/S2 limitations are not reclassified.

## Real inference measurements

| Request | Prompt / output tokens | Prefill tok/s | Decode tok/s | TTFT s | Accepted / offered drafts | Finish / review |
|---|---:|---:|---:|---:|---:|---|
| Garden manual |79 /2048|10.6|**25.3**|7.665|1109 /1847|LENGTH_CAPPED; coherent sustained text, corruption gate passed |
| English |26 /58|20.4|21.2|1.423|34 /50|Normal EOS; correct freezing-point explanation |
| Chinese |26 /49|19.0|**17.2**|1.534|25 /38|Normal EOS; correct Chinese explanation |
| Mathematics |39 /50|19.4|**11.2**|2.157|31 /49|Normal EOS; width6, area54 and calculation correct |

The primary request took7.4872s prefill and80.7966s Decode,88.571s client wall time. It passed both earlier306/1186-token failure positions. Aggregate MTP+suffix acceptance was1109/1847 =60.04%; separate MTP-only/suffix acceptance is N/A. No accepted-token speed includes failed prefixes. The prompt itself is79 tokens:131072 configured capacity is **not** a new genuine128K prompt acceptance.

The long request ran940 verifier windows, avgT2.96 and2.18 outputs/window. Existing wall-time instrumentation reports70.12ms/window verification,59.32ms GPU-reach wait,6.35ms host work (CPU experts5.47ms),0.46ms stage,1.60ms commit/emit and14.12ms draft. These overlap and are not GPU kernel-event timings. Expert cache94.2% (1251539/1329140 lookups),8620 additional GPU accesses via PCIe (0.6% of all1337760 routes). Counts include speculative verifier rows, not just accepted output tokens. Short-task cache hit rates were89.0%,86.7%,66.5%; do not hide the much slower math/Chinese results or infer causation from cache rates alone.

No matched RC1 long request was rerun, so no correctness-equivalent percentage speedup is claimed. Earlier failed-prefix/historical rates remain context. One coherent length-capped sample does not certify all factual garden advice or complete-task quality.

## Ownership replay, lifetime and remaining causal limits

Offline replay starts from the frozen STRP profile's first10831 admitted pairs, reproduces each recorded same-layer exchange and computes the full24576-entry residency hash after every publication. All251 hashes match.10831 unique GPU slots and13745 host-backed complement owners remain constant, with no duplicate slot/pair reuse within a batch, stale known pointer or missing backing. **6,735 initially GPU-only experts were actually evicted**. The7330 distinct observed physical host addresses transfer from incoming to outgoing owners consistently. Initial addresses not exchanged are not independently enumerated; this is a log-consistency replay, complemented by the real full-weight probe, not full-cache readback.

The primary response committed12,451 swaps/234 generations; with follow-ups the total is14,066/251. Every logged residency generation reports holes0, and mirror upload precedes matching residency publication. Initial successful-window diagnostics cover all48 A-plan rings with invalid0/missing0, including33/47; diagnostics intentionally do not dump every later successful window. Later progress is demonstrated by completed outputs and committed generations. Exact causes of the old failed expert cannot be retroactively proven without its ID. The repaired invariants now pass actual Adaptive ON execution without reproducing the earlier timeout.

## Memory, disk I/O and limitations

Primary-request peak engine DRM VRAM24,509,032KiB (23.374GiB), GTT25,768,072KiB (24.574GiB), RSS1,631,484KiB; minimum host MemAvailable32,190,148KiB (30.699GiB). Across all four requests VRAM peaked24,511,604KiB, RSS1,631,924KiB; GTT remained25,768,072KiB after initial page commitment. Engine VmSwap remained0. GTT and RSS overlap and must not be summed into physical host use. Fixed host-slot count and short plateau are bounded evidence, not proof of no leak over hours.

Whole primary request, excluding startup but including prefill: process `read_bytes`+608,628,736; `rchar`+758,090,126; `syscr`+38,397; major faults+321,951. In a conservative post-prefill79.563s tail: **read_bytes/rchar+149,057,536; syscr+35,579; major faults+294,103**. Decode-time storage reads remain; Direct PLE and its keepalive behavior were deliberately unchanged. Per-PLE syscall attribution/cache metrics and physical PCIe traffic are N/A; logical host copies do not measure traffic. This task did not eliminate PLE I/O.

System-wide swap-in/out counters changed+7210/+214 pages during the primary request, although engine VmSwap=0 and host RAM stayed available. This cannot be assigned to the engine; do not report zero system swap activity. Warm-tail changes were+5163/+23 pages. Neither process major page faults nor system swap counters are xe GPU faults. No resource conflict or exhaustion was observed.

## Restoration and reproduction

RC1 is active/running/enabled at **http://127.0.0.1:18083/**. Restored server PID1515174, engine PID1516093. Running RC1 SHA256: `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`. Original32768 context,9248 expert slots/15348MiB, original ranking and full mirror retained. Before/after protected binary/profile/unit/ranking hashes match. One short restored API request returned42; native UI HTTP200, `/v1/models`, `/status`, `/metrics` and `jr-sycl-watch --json` pass. No experimental engine/container or18086 listener remains. RC1 startup policy was not changed.

Raw: `logs/fastfix/mirror-repair-window-02/`. Committed evidence: `docs/jr-v0139-fastfix-evidence/mirror-repair-window-02/`; includes exact controller, commands, frozen inputs, source/library identities, full SSE/contents, periodic resources, all probes, kernel/stop journals and restoration. SHA256 inventory verifies the archive. CPU-only artifact/plan commands remain safe:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/mirror-repair-plan.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/mirror_plan_test.py
python3 -B docs/jr-v0139-fastfix-evidence/mirror-repair-window-02/analyze-ownership.py /data/strata-lab/JR-Strata-SYCL-v0139-FastFix
systemctl --user status jr-strata-sycl-rc1.service
jr-sycl-watch --json
```

The archived execution controller is the exact completed procedure, not a standing authorization to rerun. It refuses its existing evidence directory. No further GPU test or production cutover is started here. Recommend the separately controlled FastFix cutover with frozen RC1 fallback and fresh startup/short-inference/UI/monitoring checks; revert on corruption, readiness/lifecycle failure or major regression. Additional optimization is not required to meet this workload's current20tok/s eligibility gate.
