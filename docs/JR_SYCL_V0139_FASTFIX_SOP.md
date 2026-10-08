# FastFix experimental SOP

Worktree `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix`, branch `jr-b60-sycl-v0.1.39-fastfix`. No autostart or production promotion. The operator's final authorization covers completing controlled validation and RC1 restoration; it does not authorize changes to drivers, production profiles or other projects.

## Offline reproduction

```
cd /data/strata-lab/JR-Strata-SYCL-v0139-FastFix
bash tools/fastfix/cpu-tests.sh
bash tools/fastfix/build.sh
sha256sum build-fastfix/strata
```

The build uses the pinned historical image and read-only compiler/ggml sources. No GPU device is mapped during compilation. Run GPU tests with stock image runtime, never the build compiler mount.

## Bounded GPU acceptance

Maximum60 minutes from recorded preflight; no new experiment after minute45, all experimental teardown by minute50, final10 minutes reserved for RC1. Abort on GPU fault/reset, unsafe resource state, incorrect output, readiness/async error, failed numerical safety test, or surviving experimental engine. No retry of the unsafe historical binary.

Before stopping: verify frozen RC1 hash, service identity, two idle/zero-queue observations, B60 vendor8086/devicee211/PCI0000:07:00.0, available resources and accessible clean kernel journal. Preserve status and configuration hashes. Stop only using `systemctl --user stop jr-strata-sycl-rc1.service`; verify engine/server gone and memory released. Do not change enabled state.

GPU tests use the repaired build: memory alias/retry, KV Q8, KV streaming, IQ multi, native grouped, activation quantization and PLE parity. Add real graph PLE90-window oracle and readiness/completion probe. These are compatible v0.1.39 tests, not unmodified newer v0.1.40 batch-kernel tests.

After all pass, start the native Python server on localhost18086 using the pinned Docker image/new binary and original assets. Verify complete mirror, original cache strategy and native endpoints. Run short English/Chinese/Python/math at deterministic sampling, paired MTP on/off in separate engine startups with the same explicit expert slot count, then one2048-token garden-manual request beyond the prior1036-token failure point. Measure API and engine timing, output quality, MTP, process I/O, RAM/swap, GPU VRAM/GTT and device frequency/power where exposed. Do not claim success for an early EOS below2048 or for a length-capped incomplete task.

After clean stop (SIGTERM to native server → QUIT → queue drain), verify container/engine gone, free memory and kernel health. Only then start RC1 with its existing systemd unit. Verify running executable SHA256 `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`,32K model endpoint, native status/metrics/UI and one short generation. Leave RC1 running. A serious hardware fault requires assessment before either runtime is restarted.

## Recovery

```
systemctl --user stop jr-strata-fastfix-test.service
# Verify no FastFix container/engine, released B60 and no new GPU fault first.
systemctl --user start jr-strata-sycl-rc1.service
curl --fail http://127.0.0.1:18083/v1/models
jr-sycl-watch --json
```

Transient experimental service has Restart=no, KillMode=process, KillSignal=SIGTERM, SendSIGKILL=no and90-second stop timeout. Never broad pkill, Docker force removal or kill9. Preserve diagnostics if graceful shutdown fails.

Exact controller command (one window; requires the local `frozen.json` hashes to match):

```
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/maintenance.py \
  --execute-authorized --out logs/fastfix/window-01
```

The historical native server has no request-level switch that completely disables MTP. After the primary spec4 workload, the controller uses separate startups for device-only spec4 and spec0. It fixes both to the primary run's exact expert slot count. These are correctness-isolation comparisons, not identical-computation performance arms. Existing `STRATA_DECODE_TIMING=1` emits verifier/draft wall times; those are not GPU event timings. No new profiler is installed.

The archived `ple_parity` full-block selftest requires an exact Q2_0 GGUF size/offset, dense pack and captured input/output fixtures absent from this runtime. Preserve its BLOCKED result; do not substitute a Swift shard and call that oracle passed. The executable focused safety sequence uses the independent `fastfix_ple_staging` Direct/mmap graph test instead, followed by the handoff test. A harness-only continuation can use `--resume-start logs/fastfix/window-01/cutover.json`; this inherits the original absolute deadline and cannot extend it.

## Current disposition after failed acceptance

**Do not execute FastFix GPU tests or deploy this binary.** `tools/fastfix/acceptance-blocker.json` makes the maintenance controller refuse GPU execution before any service change. The failed tested binary is retained in `dist/failed-window-01/`; `build-fastfix/strata` becomes the later offline cleanup candidate and must not be mistaken for the tested artifact. The original60-minute window ended early after failure; no further tests are scheduled.

RC1 is already restored, enabled and running at http://127.0.0.1:18083/. It retains its32K profile, original ranking,9248 cache slots and full mirror. The first automatic restoration refusal and later manual recovery assessment are both preserved; do not overwrite the incident record with PASS. `manual-restoration.json` records the separately assessed successful restoration.

The tested timeout path failed safe for token delivery but did not achieve safe engine teardown. The offline follow-up moves timeout rejection after copy-queue completion. Its GPU correctness and teardown remain BLOCKED until a separately reviewed, bounded test is authorized. Do not remove the blocker merely to reuse an old command.


## P0 ring-timeout offline follow-up (2026-10-09)

The current candidate is an **offline-only lifecycle/readiness repair**, not the failed GPU-tested ELF or the intermediate copy-drain-only build. See [timestamp/root-cause classification, source changes and CPU evidence](JR_SYCL_V0139_FASTFIX_RING_TIMEOUT.md) and the [new 45-minute gated GPU plan](JR_SYCL_V0139_FASTFIX_P0_GPU_PLAN.md). The old maintenance command remains blocked. Current hashes are in `tools/fastfix/p0-candidate.json` and `p0-frozen.json`; no new GPU PASS or throughput result exists.

11 CPU lifecycle/readiness cases, 90 PLE oracle windows, existing reader/output/harness checks and 10 CPU maintenance/profile gates passed. The exact producer responsible for ring33 is still unresolved. New guards reject unready plans, retain GPU owners until verified completion, preserve first-timeout diagnostics and provide a supported T=1 no-Decode-drafting control. Default Spec4, ranking, cache layout and historical Docker runtime are preserved. RC1 stays active and unchanged. Fresh maintenance approval is required.


## Latest P0 GPU outcome — window closed (2026-10-09)

**FAIL: readiness timeout remains; no new GPU faults; RC1 restored.** [Full measured results and recovery](JR_SYCL_V0139_FASTFIX_P0_GPU_RESULTS.md) supersede the earlier “GPU pending” state. Seven GPU safety tests and the event probe passed. T=1 and MTP-on512-token controls passed at20.3 and27.9tok/s. The2,048-token request stopped after1,186 tokens with `A-plan ring47 layer46 observed40 skip0`, window896/T1/position1264. No successful sustained2,048-token result exists. Failed-prefix33.9tok/s is not accepted performance.

The controller suspended restoration for assessment; all experimental processes exited, B60 resources returned, no kernel fault or unsafe-drain marker appeared, and unchanged RC1 was restored and verified at330.09 seconds. RC1 engine199664, original32K configuration, active/enabled. The window is closed; do not rerun this failing candidate. Binary/hash/ranking/runtime remain unchanged. Full raw evidence and the initial restoration incident are preserved.
