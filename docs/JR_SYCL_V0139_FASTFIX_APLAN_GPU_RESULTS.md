# A-plan adaptive isolation — approved window01 results

**Adaptive OFF PASS; Adaptive ON BLOCKED by the fixed admission limit; RC1 restored PASS.** This is one diagnostic request, not a production qualification or a demonstrated cure for the archived ring47 timeout. No production promotion occurred.

Prepared branch `jr-b60-sycl-v0.1.39-fastfix`, commit `7b7b15db8ebd954fb6f6000ef91e202d2393f859`; engine source `ee3ab2dba75a9597d5ad2c76e8d8e5fb5f764907`. Tested ELF SHA256 `6b00ee839b6cf342fc85bdefa504e17fa80cc3fd94f766611e3707bf1120d6fe`; captured-plan probe SHA256 `3237f2ced414e38d1695631b121dd6dcb54b30fd7a361da615f647323a1de4fa`. Neither binary, inference kernels, model, ranking nor runtime was changed during the window.

Raw evidence: `docs/jr-v0139-fastfix-evidence/aplan-control-window-01/`,54 original evidence files plus archived prepared inputs and a SHA256 manifest. Runtime logs: `logs/fastfix/aplan-control-window-01/`. `window-closeout.json` records one unchanged starting clock, experimental teardown at344.27s, verified RC1 restoration at400.49s (6min40.49s), and closure of this authorization. Experiments finished before600s and restoration before900s. No further GPU execution is authorized by this completed window.

## Acceptance matrix

| Item | Status | Actual evidence |
|---|---|---|
| Prepared artifact and protected RC1 preflight | PASS | HEAD clean;18 frozen files verified; running/disk RC1 hash; idle/queued0 observed twice; normal B60 and readable fault-free kernel journal. |
| Graceful RC1 shutdown | PASS | systemd-only stop; original server198898 and engine199664 exited;18083 released; B60 resources and56.84GiB host available. |
| Docker B60 selector | PASS | Only selected device was Arc Pro B60, UUID ending0700, device57873/e211, architecturebmg_g21, userspace1.17.39758+10. |
| Captured-plan probe | PASS | Four covered/missing/invalid diagnostic generations;12 guarded-plan and12 changing-readiness rounds; controlled delayed DMA publication and completed host outputs; no GPU fault. Expected injected rejection cases are probe fixtures, not production coverage failures. |
| Adaptive OFF | PASS | Fresh original profile, `--adapt-swaps 0`,1536 actual outputs; no request error, readiness timeout or corruption indicator; inspected text coherent. |
| Adaptive ON | BLOCKED | Never launched. After static teardown344.27s, the required390s arm bound would finish at734.27s, beyond the600s experimental cutoff. The prepared admission rule is not replaced with an optimistic estimate. |
| Mirror coverage | PASS for observed initial window; broader runtime proof limited |10831 GPU experts/17990MiB and13745/13745 mirrored missing experts/22.40GiB;48 observed planner rows had no missing/invalid routes. Successful later windows were not individually dumped. |
| A-plan/skip progress | PASS in this control | All48 recorded rings built device plans, published matching skip and used the device-copy decision; A/B/M wait entries/exits match, spin counts0. Request completed beyond both306 and1186 historical failure positions. |
| GPU memory/async lifecycle | PASS for bounded observed checks | Unchanged alias protection/startup slot readback; compute/copy completion guards retained; responsive graceful shutdown; no unsafe-teardown marker or surviving experimental engine. No new full-cache readback test was run. |
| New GPU page fault/reset | PASS | Zero new faults/resets in preserved kernel journals from preflight through restored RC1 smoke. |
| RC1 restoration | PASS | Frozen running hash, original32768 context/9248 slots, API generation, native UI/status/metrics/monitoring and unchanged protected files. |
| Exact adaptive/mirror cause of archived timeout | BLOCKED | No matched adaptive-on result and no failed expert ID in this successful control. |
| Production readiness | BLOCKED | Diagnostic scope only; no release/promotion. |

## Exact configuration

Preserved Docker ID `sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`; historical SYCL2026.1.0/UR0.12.0/Level Zero1.32.0. Actual loaded maps are archived. Source build compiler2026.1.1 remained unchanged.

Native IQ3_XXS model and pack, original profile, CLI cache grant8098 (the variable-size native planner yields10831 experts/17990MiB), complete initial mirror, context131072, INT8 KV resident32768, prefill4096, reserve768MiB, MTP Spec4/min-p0.5, original suffix policy, PCIe fraction0.25, original PLE mode, alias check1, host uncached1, host-assisted loop, and opt-in A-plan diagnostics. The control adds only `--adapt-swaps 0`; the default adapt interval stays4. `static-container.json` preserves the actual command/environment and running PID; `static-launch.json` preserves the transient systemd command.

Only the frozen garden-manual request ran:79 prompt tokens, temperature0, seed42, thinkingoff, max_tokens1536, prompt reuse0. No short functional set, historical binary, broad profiler or additional stress request was run. The response ends at the requested limit, during a raised-bed discussion: **LENGTH_CAPPED**, coherent inspected text but an incomplete manual. This is sustained-generation diagnostic coverage, not complete-task quality acceptance.

## Measured request

| Metric | Result |
|---|---:|
| API actual prompt/output tokens |79 /1536 |
| Prefill |2279.2ms;34.7tok/s |
| Decode |127847.3ms;12.0tok/s |
| HTTP request wall time |130.33s |
| Observed TTFT |2.517s (monitor polling limits precision) |
| Aggregate MTP+suffix drafts accepted/proposed |820/1373;59.72% |
| Suffix subset from engine log |9 windows;13/20 accepted |
| Decode verifier windows |716; average T2.92;2.15 output tokens/window |
| Verifier / commit-emit / drafting per window |172.84 /1.60 /4.12ms, host wall-clock accounting |
| Host GPU-reach wait / layer host work |142.90 /24.00ms per window; not device kernel duration |
| Expert lookup cache hit rate |59.8% (561394/938261); original ranking retained |
| GPU PCIe/peer share counter |64459 entries;6.4% of1002720 routed entries; not physical PCIe byte measurement |
| KV streaming counter |99.91% of5314404 block reads hit VRAM;19.6MiB read from host |

The static result is slower than archived warmed/adaptive27.9tok/s and failed-prefix33.9tok/s. Those runs have different prior requests/cache adaptation and the failed prefix is not correctness-qualified. This window provides no matched adaptive-on speedup/regression percentage and no recovered20+tok/s claim.

## Resources and storage I/O

62 periodic request samples, plus before/after snapshots, came from the owned container engine `/proc/1`, native metrics and host memory counters. Peaks include prefill and Decode, not initialization.

| Metric | Measured range / delta |
|---|---|
| GPU DRM VRAM |24379492–24504016KiB (peak23.369GiB) |
| GPU DRM GTT |25758892–25769772KiB (peak24.576GiB) |
| Engine RSS |1616936–1831528KiB (peak1.747GiB; excludes pinned/mapped accounting) |
| Host MemAvailable |31449520–32490036KiB (minimum29.993GiB) |
| Engine VmSwap |0 throughout |
| System swap |pswpin +1 page; pswpout0; global counter cannot attribute the page to this engine |
| Process read_bytes |+540524544 bytes (515.484MiB) |
| Process rchar / syscr |+728123790 bytes /31275 calls |
| Process major faults |+189 |

I/O deltas cover the whole request, including prefill and Decode, and do not separate PLE, expert or other reads. No disk-free Decode claim is made. A single request cannot establish endurance or absence of progressive leaks. Teardown released resources; health assessment recorded24143736832 B60 free bytes (see raw discovery for authoritative exact value).

## What A-plan observations establish

The first completed window was generation1/T6, a prompt-verifier window, with48 recorded rings. Each record has `entered=ring`, `decision=1`, `skip_written=ring`, no invalid/missing routes, `copy=2` (device plan), and A/B/M wait skip/entry/exit equal to ring with zero spins. Ring47/layer46 is included and was covered there. Later T1/2/3/4 graphs were captured and the716-window Decode completed without a latched failure.

All polled allocations reported `ZE_BIAS_UNCACHED`. The startup `APLAN_CONFIG pcie_mode=0` is printed before the later serving PCIe setup; it is not an authoritative final mode. The observed host plans report PCIe groups but `dma=0`; no inference copy-queue DMA callback occurred in that recorded window. The separate probe exercised an explicitly delayed DMA dependency and publication. Individual GPU event duration, physical PCIe traffic and device timestamps remain N/A.

No `APLAN_RESIDENCY` admission lines appeared with swaps disabled, as expected from the empty pending vector. This alone does not prove coverage. Initial mirror counts, recorded route/residency values, source control gates and successful bounded generation are the available evidence. No unexpected expert ID, missing mirror or failed ring was recorded in this run.

**Causal decision:** disabling adaptive activity is a viable diagnostic control and this request passed beyond the historical failure positions. Without the matched arm, we cannot classify Adaptive Activity as a strongly demonstrated cause. The source-level static-mirror/adaptive-victim coverage hole remains established offline; its role in the specific archived ring47 timeout is unproven. No synchronization change or permanent adaptive-off deployment follows from this result.

## Restoration and closure

After native-server SIGTERM → QUIT and completion, engine/container/18086 were gone; B60 normal/free; no unsafe marker or kernel fault. Protected RC1 binary,32K profile, unit and ranking hashes matched before/after.

Restored service `jr-strata-sycl-rc1.service`: active/enabled; server984699; engine985485. Running SHA256 `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`;32768 context;9248 original experts and15328/15328 missing experts mirrored (24.98GiB). `/v1/models`, `/status`, `/metrics`, native UI root and `jr-sycl-watch --json` responded. The one32-token-cap smoke answered “2 plus 2 equals 4.” RC1 remains running.

The15-minute authorization is closed. No adaptive-on rerun or new GPU task was started. Further causal validation needs a fresh, narrowly scoped authorization; no production promotion is recommended.
