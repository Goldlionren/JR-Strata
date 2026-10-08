# A-plan diagnostic validation — not authorized or executed

This is a proposed **single15-minute diagnostic window**, expected8–10 minutes including restoration. Stop admitting work at minute7, finish experimental teardown by minute10, reserve minutes10–15 for RC1. One captured handoff probe and one inference request only; do not repeat the historical acceptance/benchmark suite. No production promotion. If the observation does not recur, report inconclusive rather than immediately repeat it.

Purpose: distinguish actual device-plan rejection (particularly an adaptive victim absent from the static mirror) from skip visibility or missing graph progress. Read `JR_SYCL_V0139_FASTFIX_APLAN_ANALYSIS.md`. The instrumentation changes timing and does not measure production throughput reliably.

## Before any authorized cutover

1. Record one monotonic start/deadline before preflight. Verify current branch/source and every hash in `tools/fastfix/aplan-candidate.json`; the failed14db752… ELF is preserved at `dist/failed-p0-window-01/strata` and must never execute.
2. Verify idle/unqueued RC1 twice, running and disk frozen SHA256, original32K config/ranking/unit hashes. Use the existing operator-controlled checks: B60 `0000:07:00.0`, `8086:e211`, normal state, readable recent kernel journal with no unresolved faults, port18086 free, no conflicting container/workload. No ownership helper or privileged-policy changes.
3. Preserve the exact old runtime image ID and model/profile hashes. Require fresh evidence directory; never overwrite an earlier window.
4. Stop RC1 only with `systemctl --user stop jr-strata-sycl-rc1.service`. Record its server/engine PIDs first and verify both exit, no18083 listener, B60 resources released, at least22GiB free B60 and50GiB host available. No unrelated process termination. No autostart change.

## Diagnostic commands after new authorization and passed preflight

Run from `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix`. Do **not** execute the old `p0-maintenance.py --execute-authorized`: its historical frozen manifest and full benchmark sequence are deliberately not repurposed.

```bash
mkdir logs/fastfix/aplan-window-01
systemctl --user stop jr-strata-sycl-rc1.service
# STOP here unless recorded engine exit, GPU health and free-resource gates pass.
docker run --rm --name jr-fastfix-aplan-probe --device /dev/dri \
  -v /data/strata-lab:/work:ro \
  -e ONEAPI_DEVICE_SELECTOR=level_zero:0 -e SYCL_CACHE_PERSISTENT=0 \
  -e STRATA_HOST_UNCACHED=1 -e STRATA_ARENA_ALIAS_CHECK=1 \
  sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44 \
  'exec /work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/fastfix_handoff' \
  > logs/fastfix/aplan-window-01/probe.log 2>&1
```

Confirm the historical selector resolves to B60 in this image before the probe, using its existing `sycl-ls --verbose` identity check. Probe expected<30s, admission budget60s. It contains only small bounded waits/captured plan tests; four new route generations must validate mixed device/mirror coverage, missing/invalid-route observations and graph reuse. Existing delayed-DMA/rejected-plan checks remain. On any probe failure, stop; do not start inference. Do not SIGKILL a stuck probe to fit the deadline; an unexpected hang is an incident requiring GPU assessment.

Start the original native server under a transient, nonrestarting unit; no installed unit changes:

```bash
systemd-run --user --unit jr-strata-fastfix-aplan-test.service --collect \
  --service-type=exec -p Restart=no -p KillMode=process -p KillSignal=SIGTERM \
  -p SendSIGKILL=no -p TimeoutStopSec=90 \
  --setenv=PYTHONDONTWRITEBYTECODE=1 --setenv=PYTHONUNBUFFERED=1 \
  --setenv=FASTFIX_P0=1 --setenv=FASTFIX_APLAN_DIAG=1 \
  --setenv=FASTFIX_NO_DRAFT=0 --setenv=FASTFIX_NO_HOST=0 \
  --working-directory=/data/strata-lab/JR-Strata-SYCL-v0139-FastFix \
  /data/strata-lab/Strata/.venv/bin/python -B \
  /data/strata-lab/JR-Strata-SYCL-v0139-FastFix/sycl/serve/server_intel.py \
  --engine strata \
  --config /data/strata-lab/JR-Strata-SYCL-v0139-FastFix/tools/fastfix/aplan-runtime.json \
  --host 127.0.0.1 --port 18086
```

Allow at most180s startup. Before generation verify the running Docker `/proc/1/exe` hash against the candidate manifest, actual loaded libraries, `/v1/models`, `/metrics`,10831 experts/17990MiB,13745 initial mirrored experts, at least512MiB loaded free VRAM, and `APLAN_CONFIG`. It must report device_plan1 and the actual allocation types. The uniform CLI grant remains8098; do not substitute10831 in that argument. Context131072, resident INT8 KV32768, prefill4096, reserve768MiB, Spec4/min-p0.5, PCIe fraction0.25, original ranking, PLE mode and adaptive defaults are unchanged. The diagnostic records add16128 bytes mapped host memory, not expert-cache budget.

```bash
curl --fail --no-buffer --max-time 180 \
  http://127.0.0.1:18086/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary @tools/fastfix/aplan-request.json \
  > logs/fastfix/aplan-window-01/response.sse
```

Use only this archived garden-manual prompt, capped at1536 actual outputs, temperature0/seed42/thinkingoff. No extra warmup/acceptance set. The shorter startup history differs from the previous failing run; do not claim deterministic reproduction. If EOS occurs early, preserve it and mark trigger coverage incomplete. If curl times out, initiate native-server cancellation/graceful stop and verify engine completion; client disconnect is not proof of cleanup. Collect periodic `/metrics`, engine PID `/proc/io`, DRM memory, MemAvailable/swap, kernel diagnostics and complete text. Watch `APLAN_RESIDENCY` for coverage holes and `APLAN` for the failed route. Do not benchmark or retune based on these diagnostic rates.

Immediate STOP: readiness timeout, first invalid/nonfinite/corrupt output or abnormal punctuation, new GPU fault/reset, unexpected async error, unsafe teardown, surviving engine, conflicting workload or resource pressure. A coverage-hole report is source evidence, not a safety PASS. If it appears, do not initiate additional requests; retain the single bounded request's diagnostics or cancel on any correctness/safety failure. No second inference run.

## Teardown and restoration

```bash
systemctl --user stop jr-strata-fastfix-aplan-test.service
journalctl --user -u jr-strata-fastfix-aplan-test.service --no-pager \
  > logs/fastfix/aplan-window-01/server-journal.txt
```

SIGTERM goes only to the native server, which sends QUIT and lets the engine drain its queues. Verify the recorded engine PID, `jr-strata-fastfix-engine` container and18086 listener are gone; preserve full kernel journal from window start, engine stderr and resource release. A readiness error or `FASTFIX_UNSAFE_TEARDOWN` suspends automatic restoration until recorded assessment confirms process exit, normal B60 and no outstanding fault. Never release memory or force-kill an uncompleted GPU command merely to meet a clock.

Only after clean teardown and GPU assessment:

```bash
systemctl --user start jr-strata-sycl-rc1.service
systemctl --user show jr-strata-sycl-rc1.service -p ActiveState -p SubState -p MainPID
curl --fail --max-time 10 http://127.0.0.1:18083/v1/models
/home/james/.local/bin/jr-sycl-watch --json
```

Verify the running RC1 `/proc/ENGINE_PID/exe` SHA256 equals `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`,32768 context, original9248-expert profile and mirror, native `/status` and `/metrics`, then one short32-token arithmetic generation. Recheck protected hashes, service startup state and kernel faults. Leave RC1 running. If health is uncertain, report the incident instead of restarting either engine.

The report must distinguish: probe PASS/FAIL; coverage loss observed/not observed; exact failed expert captured/not captured; skip publication/visibility contradiction; graph completion; output status; and RC1 restoration. A single nonfailure is not a repair or production qualification.
