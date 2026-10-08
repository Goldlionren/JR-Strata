# FastFix P0: ring 33 timeout and failed teardown

Prepared from `9b074f98c08df0eeadf66bb951e27e98a2036988`; engine source through `47f505b`.
Offline repair candidate only. RC1 remains active and unchanged. No new GPU run or promotion.

## What the preserved evidence establishes

All times below are October 9, 2026, in the archived host journal's local timezone (Australia/Sydney). The preserved output is second-resolution; do not infer subsecond causal ordering.

| Time / evidence | Observation | Limit |
|---|---|---|
| `experimental-journal.txt:43`, 00:41:19 | `expert readiness device wait expired at ring 33`, host sequence 48, after 306 streamed output tokens | The old error did not identify A/B/M, T, position or event ID. |
| `kernel.txt:1382–1392`, 00:41:20 | CCS reset, GuC ID 6, ASID 6195, address `0x0000c71e38990000`, fault response `-ENOENT` | First recorded fault follows the application error. The hardware fault's actual onset could precede its report. |
| `historical-engine.log`, final two lines | Uncaught SYCL exception, `UR_RESULT_ERROR_UNINITIALIZED` | No backtrace identifies the throwing destructor. |
| `experimental-journal.txt:45–48`, 00:41:20 | Server systemd stop/exit | Server exit alone did not establish clean engine shutdown. |

Raw directory: `logs/fastfix/window-01-resume/`. Original failed ELF is retained at `dist/failed-window-01/strata`, SHA256 `faa0efb9b9d2314f2e9140e1b45e9f5d275331b278b086b339b306fb15a0121e`. **Never rerun it.** The intermediate copy-drain-only ELF was `39701868b8532bc20c03faf8ab0009cf881f0611462a09914739c9d5d6696996`; it was never GPU-qualified.

The compute queue's existing wait returned before the old latch rejection. Thus the direct observation is an expert-readiness word expiring *inside* a graph, not proof that a particular SYCL event never completed or that `ext_oneapi_empty()` returned premature success. The failed branch then skipped the copy wait. There was no per-event trace to recover afterward. The old latch was overwritten on each expiry, and channels were tested A then B then M; ring 33 need not be the first failing step or channel.

## Ring ownership and dependency sequence

At `sycl/src/core/verify.cpp:579` and `sycl/src/core/verify.cpp:936`, the verifier numbers a layer/group handoff as `(layer - lb) * G + group + 1`. This run had no `--spec-split`, hence G=1, lb=0, and reported ring 33 corresponds to **zero-based layer 32, group 0**, not token 33 or expert 33.

1. Graph router writes expert IDs/weights and attempts a device expert plan, using VRAM slots or pinned mirror addresses; it publishes the doorbell sequence.
2. Host observes the sequence, computes its expert share, publishes plan A, queues DMA copies and publishes B in an in-order copy-queue host task; M records CPU expert completion.
3. Graph waits for A before copying pointer-bearing plan data, executes resident groups, waits for B before PCIe groups, and waits for M before copying CPU results. A current device-plan skip word bypasses those host waits.
4. At completion the verifier must collect compute **and** copy work before inspecting timeout latches or freeing staging/plan/mirror owners. MTP and asynchronous commit queues can overlap and share owners; error teardown checks every tracked queue on this device.

Source: `sycl/src/core/verify.cpp:933`, `sycl/src/core/verify.cpp:1684`, `sycl/src/kernels/cuda/verify_kernels.dp.cpp:932`.

## Root-cause classification

**Confirmed source defects:** expired plan waits previously allowed downstream plan/pointer consumption; the failed GPU binary returned before its copy drain; other early returns and destructor exceptions could skip queue cleanup. Callback arguments used reusable mutable slots, and pending commit state was cleared before a successful completion check. These are repaired defensively without asserting they all occurred in this incident.

**Unresolved trigger:** which readiness channel expired and why. The archived trace cannot distinguish host publication delay, an incomplete DMA, invalid routing/plan state, loss of mirror/device-plan coverage, memory corruption, or driver/runtime failure. No allocated GPU address map identifies the faulting address. Startup alias checking and a verified cache slot do not exclude later aliasing or invalid pointers. The historical Boolean queue-status translation is already correct and remains unchanged.

**Plausible fault amplification:** freeing shared buffers while a copy or other queue remains active, or consuming an unready plan after a bounded wait. The one-second report ordering supports investigating teardown but does not prove a use-after-free caused the page fault. A synchronization-only diagnosis would overstate the evidence.

## Surgical changes

- `sycl/src/kernels/cuda/verify_kernels.dp.cpp:1177`: a SYCL-only guarded wait records the first failing ring and observed readiness/skip. B failure clears expert counts before any staged-weight consumer. No timeout increases.
- `sycl/src/kernels/cuda/verify_kernels.dp.cpp:1183`: the existing plan-copy position now rejects an unready/sticky-failed plan before reading any host plan words and clears its four counts. Valid device plans still bypass host copies. The native IQ3_XXS compute kernels, memory layout and normal graph order are unchanged. These guards discard a bad window; they do not make an incomplete transfer correct.
- `sycl/src/core/verify.cpp:1329`: every post-submission failure poisons the verifier, dumps diagnostics and requires quiescence before owners can unwind. Success dismisses this guard; no global queue drain is added to successful Decode windows.
- `include/strata/failed_work.hpp` and `sycl/include/strata/sycl_failed_work.hpp`: error/destructor-only five-second queue polling, followed by `wait_and_throw` on all completed queues; an error in one queue does not skip the others. Incomplete or failed quiescence prints `FASTFIX_UNSAFE_TEARDOWN` and exits 86 without C++/SYCL static cleanup. OS/driver process cleanup remains unavoidable and is **not** certified safe; the controller requires hardware assessment before restart. Completion queries are never treated as sufficient async-error evidence.
- `sycl/src/core/verify.cpp:276`, `sycl/src/core/mtp.cpp:122`: verifier/drafter destruction checks outstanding device queues before any graph, arena or pinned allocation is freed. Owned queue pointers begin null rather than aliasing the default queue. A cleanup exception cannot silently continue releasing other owners.
- `sycl/src/core/verify.cpp:1684`: DMA publication captures flag/value by value. Trace mode records queued/published callbacks; staging remains alive until queue completion. Existing in-order DMA ordering is preserved.
- `sycl/src/core/verify.cpp:1835`: pending commit and PLE history advance only after successful completion. Failed commit submission/collection takes the same poison/drain path.
- The watchdog failure hook no longer fabricates readiness by raising all flags to `UINT32_MAX`.
- `STRATA_TEST_VERIFY_NO_DRAFT=1` is an explicit diagnostic-only control: server still allocates under supported `--spec 4`, then evaluates T=1 windows and skips Decode MTP/suffix drafting. Prefill still initializes MTP state. Default MTP behavior is unchanged. `--spec 0` is not a supported historical server configuration and is not used.

Source commits: `f0ce0db` (guards/lifetimes/tests), `4049fde` (T=1 control and bounded plan), `47f505b` (DMA/failure diagnostics). No ranking, model, Docker, compiler/runtime installation, GPU driver, RC1 or other project changes.

## Why earlier tests passed

Earlier handoff probes pre-raised flags or intentionally expired tiny isolated waiters, and checked the latch after completion. They did not execute native pointer consumers after expiry, delayed DMA/host callbacks, shared large allocations during unwind, full recurrent state or 300+ generated tokens. CPU tests prove policy/reference arithmetic, not PCIe visibility, graph scheduling or driver behavior. New focused GPU tests are compiled but pending: captured rejected-plan copy with an intentionally null source, changing windows, sticky diagnostics, zeroed B counts, controlled delayed DMA publication, and completed MTP-style host outputs.

## Residency assessment

Archive: 10,831 GPU experts / 17.57 GiB, 13,745/13,745 pinned missing experts / 22.40 GiB; 648 MiB reported free after full startup. `ExpertCache::init` checks requested bytes against device free memory; `malloc_device_guarded` retains the 64-KiB-stride alias check/retry and chunked compute initialization. Neither sparse alias sampling nor slot-0 readback is full cache integrity proof. This revision changes no byte budget or allocation planner. The P0 plan requests exactly 10,831 slots, checks complete mirror coverage and free resources, and stops if allocation safety fails. **Safe sustained residency remains BLOCKED pending GPU acceptance.** No attempt to force extra residency or reduce safety reserve is authorized here.

## Offline results and limits

| Gate | Result |
|---|---|
| Archived timestamp/ring reconstruction | PASS, with explicit limits above |
| Exact original timeout trigger / fault address owner | BLOCKED: not recorded |
| CPU lifecycle/readiness fault injection | PASS, 11 cases |
| PLE independent Direct/mmap oracle | PASS, 90 windows, T=1/4/6, three histories |
| Reader layouts / completed MTP bounds / actual source ordering | PASS |
| Existing fenced/unfenced Python harness checks | PASS |
| P0 maintenance restoration/deadline gates | PASS, 10 fake-service/profile tests; dry run has no lifecycle actions |
| Isolated Docker build | See final artifact manifest and build log |
| New GPU safety / timeout / 512+ and 2,048-token tests | BLOCKED: fresh authorization required |
| Performance preservation / full cache integrity | BLOCKED: no new GPU measurements |
| RC1 preservation | PASS: active, frozen hash and 32K API confirmed read-only |
| Production promotion | BLOCKED |

CPU evidence: `logs/fastfix/p0-cpu-final.log`; build: `logs/fastfix/p0-final-build.log`; reproducible hashes: `tools/fastfix/p0-frozen.json`; engine identity: `tools/fastfix/p0-candidate.json`. A timing target or CPU PASS is not evidence that the ring timeout is solved.


Budget detail: the preserved log grants **8,098 uniform max-blob slots**, then the existing variable-size native planner expands them into **10,831 profile-ordered experts / 17,990 MiB**. The new controller uses `--expert-cache 8098`, verifies exactly10,831 loaded experts and17,990 MiB with the unchanged ranking, full13,745-expert mirror, and at least512MiB remaining VRAM. Passing `10831` directly to this CLI would enlarge the byte budget and is deliberately avoided. This is the original planner and byte budget, not a new residency optimization.


Frozen new executable: `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/build-fastfix/strata`

SHA256: `14db752d630df2c1d992f77e0da71eb61852ffca0ab6c77ef71bda646af63434`

Final isolated build: **PASS** (`logs/fastfix/p0-final-build.log`). Engine source `47f505b`; controller/profile checks `5a9e576`. CPU lifecycle policy also passes ASan/UBSan. GPU tests have **not** been executed. Final read-only production check: server1586519, engine1587016, frozen RC1 hash, context32768, active/enabled; no new kernel faults in the 07:30–08:39 offline check interval.
