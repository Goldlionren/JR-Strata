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
