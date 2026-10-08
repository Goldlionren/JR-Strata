# FastFix P0 GPU validation — FAIL, RC1 restored

Tested commit `d50b425b811495df7af34df40f23cf352d31dcc1`, branch `jr-b60-sycl-v0.1.39-fastfix`.
Exact engine SHA256 `14db752d630df2c1d992f77e0da71eb61852ffca0ab6c77ef71bda646af63434`.
No code, binaries, ranking, model assets, runtime, drivers or production configuration changed during this run.

One authorized45-minute window began **2026-10-09 08:46:47.761 Australia/Sydney**. Testing stopped on the first readiness failure at08:50:06; verified RC1 restoration completed after**330.09 seconds** (about5m30s). No further experiment was admitted, no clock reset and no time extension. The window is closed; no retry is authorized.

## Acceptance

| Stage / gate | Verdict | Actual evidence |
|---|---|---|
| A — seven GPU safety tests | PASS | All seven exited0, including512MiB alias scan, injected eight-attempt refusal, INT8/streamed KV, IQ/grouped/activation parity and90 independent PLE graph windows |
| B — readiness/event probe | PASS | Captured invalid-plan suppression, twelve changing rounds, gated DMA publication/event dependency, completed host outputs; exit0 |
| C — T=1 no Decode drafting | PASS | Four functional requests plus512 actual tokens,20.3 tok/s, no timeout; clean stop |
| D — MTP Spec4 control | PASS | Four functional requests plus512 actual tokens,27.9 tok/s;278/436 drafts accepted (63.76%) |
| E —2,048-token request | FAIL | **1,186 output tokens**, then A-plan readiness timeout; no final successful usage/DONE |
| Readiness-timeout elimination | FAIL | Passed306 tokens but timeout recurred at ring47/layer46 |
| New GPU page fault/reset | PASS | Zero in full window and restoration journals |
| Memory integrity | PASS for focused tests; BLOCKED for sustained qualification | Fixed cache/mirror loaded, no alias mismatch or allocation error; failed generation cannot certify long-run safety |
| Error cleanup | PASS for this incident | Graph reported SYNCED, no unsafe-exit marker, engines/containers/listener gone, idle free memory recovered; no driver fault |
| RC1 restoration | PASS after independent assessment | Frozen running hash, original32K/ranking, one short generation, native UI/assets/status/metrics, monitor and kernel checks |
| Production adoption | BLOCKED | Sustained correctness gate failed |

Ten of eleven experimental inference requests completed normally; the eleventh failed. No `!!!!!`, `root!!!!!` or replacement-character corruption was observed in retained outputs. Python assertions and mathematical answers passed; English/Chinese answers were coherent and on task. Long-form prefixes were coherent without abnormal repeated blocks, but the512-token outputs are deliberately length-capped and are not complete garden manuals. Natural-language factual claims were not exhaustively certified. Do not turn a prefix or a request error into a quality PASS.

## Actual throughput and request counts

All requests use the prepared fixed prompts, temperature0, seed42, unchanged model/IQ3_XXS weights, original ranking and historical Docker. These are single-run observations, not repeated medians or a reliability estimate. Draft counts are the engine's aggregate speculative counts and can include suffix drafting; do not label them MTP-only acceptance.

| Arm / task | Output tokens | Decode tok/s | Prefill tok/s | TTFT s | Accepted/proposed drafts |
|---|---:|---:|---:|---:|---:|
| mtp-off-beyond306 / beyond306 | 512 | 20.3 | 32.3 | 2.509 | 0/0 |
| mtp-off-functional / english | 54 | 15.0 | 18.5 | 1.495 | 0/0 |
| mtp-off-functional / chinese | 46 | 16.8 | 22.4 | 1.243 | 0/0 |
| mtp-off-functional / python | 53 | 12.2 | 31.4 | 1.422 | 0/0 |
| mtp-off-functional / math | 110 | 16.0 | 39.7 | 1.133 | 0/0 |
| mtp-on-beyond306 / beyond306 | 512 | 27.9 | 32.6 | 2.494 | 278/436 |
| mtp-on-functional / english | 54 | 16.4 | 18.8 | 1.483 | 31/45 |
| mtp-on-functional / chinese | 48 | 17.5 | 21.1 | 1.319 | 24/35 |
| mtp-on-functional / python | 53 | 19.7 | 30.4 | 1.475 | 36/41 |
| mtp-on-functional / math | 110 | 22.4 | 34.2 | 1.314 | 76/97 |
| mtp-on-sustained / sustained | 1186 | N/A — failed | N/A | 0.313 | N/A |

The matched512-token controls show37.4% higher reported Decode rate with speculation, but produce different text. This does not establish a comparable gain over RC1 or over historical unqualified28–33tok/s results. The failed long request's server progress read33.9tok/s; **qualified2,048-token sustained performance is N/A**. Final long-request draft counts, verifier summary and prefill timing are unavailable because the engine returned ERR. Its TTFT0.313s differs materially from the controls; do not treat its failed prefix as a matched sustained benchmark.

For the completed512-token T=1 request:512 windows, mean T1,49.28ms/window; verifier45.46ms (host-observed GPU-reach wait30.83ms, host pool11.97ms, staging0.33ms), commit/emit1.66ms, draft0.
For completed512-token MTP-on:234 windows, mean T2.86,2.19 accepted outputs/window,78.43ms/window; verifier68.80ms (host-observed reach wait43.49ms, host pool21.33ms, staging0.48ms), commit/emit1.92ms, draft5.56ms. These are existing **host wall timings**, not device event durations or GPU occupancy measurements.

## Failure evidence and narrower classification

`mtp-on-engine.log:56`:

```text
readiness timeout A-plan ring=47 layer=46 group=0 observed=40 skip=0 window=896 T=1 pos=1264 host_seq=48
```

At08:50:06 the native server reported an error after1,186 tokens. The user-facing window896 corresponds to zero-based host trace window895. The first failing channel was **A, host expert-plan readiness**, not the B DMA-ready channel. Its required value47 was not observed before the device wait expired; observed40 and skip0 mean no current device-plan bypass was taken. Host trace shows the GPU sequence already at47 while the host worked through earlier layers. The host eventually published A47 and all final flags reached48, and the graph reported `SYNCED`; late readiness does not validate the already-discarded window.

This narrows the immediate failure to the plan handoff. It does **not** prove why the device-plan bypass failed despite complete startup cache/mirror coverage, whether any visibility delay contributed, or whether old ring33 had the same trigger. The failing window was **T=1 inside the MTP-enabled run**; do not diagnose this as an exclusively multi-row verifier or draft-token problem. A512-token T=1 control is not a2,048-token isolation test. No extra long control was run after failure.

No DMA callback pair appears in the retained final160-event excerpt; it cannot establish a failed DMA transfer. Exact device event timestamps and per-node durations remain N/A. The trace footer says “no GPU breadcrumb ... GPU never started”; that inference is invalid here: `sycl/src/kernels/cuda/verify_kernels.dp.cpp:1309` deliberately stores zero for its unsupported SYCL timer. Host sequence progress, the device timeout latch and SYNCED prove the graph did execute. Preserve the original misleading footer as raw evidence rather than rewriting logs.

Unlike the previous incident, **no CCS reset/page fault, uninitialized-runtime exception or FASTFIX_UNSAFE_TEARDOWN marker occurred**. This supports the new bad-plan suppression and cleanup behavior for this occurrence; it does not prove general fault immunity or fix the original producer timing problem. No timeout or safety setting was relaxed.

## Residency, memory and I/O

Both arms loaded exactly10,831 experts,17,990MiB cache (~17.57GiB) and13,745/13,745 pinned missing experts (~22.40GiB). The frozen uniform grant was8,098; original variable-size packing, reserve768MiB, context131072, INT8 resident KV32768 and prefill4096 were preserved. Cache MiB and mirror GiB are native rounded display values; exact allocation byte counts are not exposed by these logs. Initial loaded free VRAM was649MiB (T=1) and652MiB (MTP-on). Spec4 MTP plus default suffix support reports maximum verifier6, MTP4, lookup3; those settings were unchanged.

Across recorded requests, peak engine DRM VRAM was24,503,356KiB (**23.368GiB**) and GTT25,812,892KiB (**24.617GiB**). Peak engine RSS1,846,268KiB (**1.761GiB**) excludes substantial pinned allocations and is not the total host cost. Lowest host MemAvailable31,298,844KiB (**29.849GiB**). Engine VmSwap stayed0. System `pswpin` increased by one page during the failed long request; `pswpout` stayed unchanged. Report this small observed swap activity rather than “no swap.” The short run showed no large unbounded growth, but does not qualify leak-free endurance.

| Request interval | Process read_bytes delta | rchar delta | syscr delta | Major faults |
|---|---:|---:|---:|---:|
| T=1,512 tokens | 5,676,851,200 | 15,309,376,909 | 35,289 |125 |
| MTP-on,512 tokens | 4,101,611,520 | 9,231,674,765 | 26,836 |121 |
| MTP-on,failed1,186-token prefix | 3,512,008,704 | 11,343,598,990 |38,033 |0 |

These process intervals include prompt handling and generation, and the last includes error handling. They are **not isolated PLE I/O**. PLE-specific row reads/cache statistics/wait time are N/A in this frozen build; expert streaming, PLE and other process reads cannot be separated from `/proc/io` alone. No zero-SSD-I/O claim is made. Raw two-second samples include GPU power/frequency and before/after data in `measured-summary.json` and per-request JSON.

## Recovery and final production state

The controller correctly blocked automatic restoration on the engine error and preserved `RESTORATION-INCIDENT.json`. It stopped the experimental server via systemd; engine179947 exited. Independent follow-up confirmed both experimental engine PIDs169394/179947 absent, no FastFix container, port18086 free, B60normal and24,143,736,832 free device bytes matching the idle baseline. Two fresh kernel/device checks found no new fault. Only then was unchanged RC1 started, within the original clock.

RC1 server**198898**, engine**199664**, active/enabled, no restart-policy edits. Running SHA256:

```text
cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028
```

API context32768, original9,248 resident experts and original ranking. Protected binary/profile/unit/ranking hashes match preflight. One32-token-cap smoke returned “2 plus 2 is 4.” Native `/`, `web/app.js`, `/v1/models`, `/status`, `/metrics` and `jr-sycl-watch --json` responded. Chat/Monitor/About tab assets are present; no automated browser-click test was performed. No experimental engine remains. RC1 stays running at **http://127.0.0.1:18083/**.

## Recommendation

Keep RC1 in production. FastFix is worth a **focused A-plan publication/device-plan fallback repair**, given correct512-token results at20.3/27.9tok/s and fault-free failure cleanup. It is not production-ready and has not met the2,048-token gate. Do not retry this executable or increase blanket timeouts to get a benchmark. Further source work or a new GPU window needs the next task decision; no optimization or additional run was performed here.

Raw evidence: `logs/fastfix/p0-window-01/`; committed exact copy: `docs/jr-v0139-fastfix-evidence/p0-window-01/`, with SHA256 manifest. The original controller's199.46s incident remains intact; `manual-restoration.json` and `window-closeout.json` record the final330.09s verified recovery. Tested binary and prepared source remain unchanged.
