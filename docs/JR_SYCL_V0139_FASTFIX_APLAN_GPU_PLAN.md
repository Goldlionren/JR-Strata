# A-plan diagnostic validation — not authorized or executed

This is a proposed **single15-minute diagnostic window**, expected8–10 minutes including restoration. Finish experimental teardown by minute10; reserve minutes10–15 for RC1. A full arm requires390 seconds of remaining experimental budget (120 startup +180 request +90 teardown), so its latest admission is minute3:30. Never reset the clock between arms. One captured handoff probe, then one adaptive-off control request; at most one matched adaptive-on request if the control passes, tears down cleanly and the deadline admits it. Do not repeat the historical acceptance/benchmark suite. No production promotion. If the observation does not recur, report inconclusive rather than immediately repeat it.

Purpose: first test whether disabling adaptive swaps preserves startup coverage and avoids the prior failure, then distinguish actual device-plan rejection (particularly an adaptive victim absent from the static mirror) from skip visibility or missing graph progress. Read `JR_SYCL_V0139_FASTFIX_APLAN_ANALYSIS.md`. The instrumentation changes timing and does not measure production throughput reliably.

## Before any authorized cutover

1. Record one monotonic start/deadline before preflight. Verify current branch/source and every hash in `tools/fastfix/adaptive-control-frozen.json`, including the unchanged engine/probe identities from `tools/fastfix/aplan-candidate.json`; the failed14db752… ELF is preserved at `dist/failed-p0-window-01/strata` and must never execute.
2. Verify idle/unqueued RC1 twice, running and disk frozen SHA256, original32K config/ranking/unit hashes. Use the existing operator-controlled checks: B60 `0000:07:00.0`, `8086:e211`, normal state, readable recent kernel journal with no unresolved faults, port18086 free, no conflicting container/workload. No ownership helper or privileged-policy changes.
3. Preserve the exact old runtime image ID and model/profile hashes. Require fresh evidence directory; never overwrite an earlier window.
4. Stop RC1 only with `systemctl --user stop jr-strata-sycl-rc1.service`. Record its server/engine PIDs first and verify both exit, no18083 listener, B60 resources released, at least22GiB free B60 and50GiB host available. No unrelated process termination. No autostart change.

## Diagnostic commands after new authorization and passed preflight

Run from `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix`. Do **not** execute the old `p0-maintenance.py --execute-authorized`: its historical frozen manifest and full benchmark sequence are deliberately not repurposed.

```bash
mkdir logs/fastfix/aplan-control-window-01
systemctl --user stop jr-strata-sycl-rc1.service
# STOP here unless recorded engine exit, GPU health and free-resource gates pass.
docker run --rm --name jr-fastfix-aplan-probe --device /dev/dri \
  -v /data/strata-lab:/work:ro \
  -e ONEAPI_DEVICE_SELECTOR=level_zero:0 -e SYCL_CACHE_PERSISTENT=0 \
  -e STRATA_HOST_UNCACHED=1 -e STRATA_ARENA_ALIAS_CHECK=1 \
  sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44 \
  'exec /work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/fastfix_handoff' \
  > logs/fastfix/aplan-control-window-01/probe.log 2>&1
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
  --config /data/strata-lab/JR-Strata-SYCL-v0139-FastFix/tools/fastfix/aplan-control-static.json \
  --host 127.0.0.1 --port 18086
```

Allow at most120s startup. Before generation verify the running Docker `/proc/1/exe` hash against the candidate manifest, actual loaded libraries, `/v1/models`, `/metrics`,10831 experts/17990MiB,13745 initial mirrored experts, at least512MiB loaded free VRAM, and `APLAN_CONFIG`. It must report device_plan1 and the actual allocation types. The uniform CLI grant remains8098; do not substitute10831 in that argument. Context131072, resident INT8 KV32768, prefill4096, reserve768MiB, Spec4/min-p0.5, PCIe fraction0.25, original ranking and PLE mode are unchanged. The first arm adds only `--adapt-swaps 0`; `adapt_every` remains4. It must use a fresh engine initialized from the original ranking, not a live engine that already swapped experts. The diagnostic records add16128 bytes mapped host memory, not expert-cache budget.

```bash
curl --fail --no-buffer --max-time 180 \
  http://127.0.0.1:18086/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary @tools/fastfix/aplan-request.json \
  > logs/fastfix/aplan-control-window-01/static-response.sse
```

Use only this archived garden-manual prompt, capped at1536 actual outputs, temperature0/seed42/thinkingoff. No extra warmup/acceptance set. The shorter startup history differs from the previous failing run; do not claim deterministic reproduction. If EOS occurs early, preserve it and mark trigger coverage incomplete. If curl times out, initiate native-server cancellation/graceful stop and verify engine completion; client disconnect is not proof of cleanup. Collect periodic `/metrics`, engine PID `/proc/io`, DRM memory, MemAvailable/swap, kernel diagnostics and complete text. Watch `APLAN_RESIDENCY` for coverage holes and `APLAN` for the failed route. Do not benchmark or retune based on these diagnostic rates.

Immediate STOP: readiness timeout, first invalid/nonfinite/corrupt output or abnormal punctuation, new GPU fault/reset, unexpected async error, unsafe teardown, surviving engine, conflicting workload or resource pressure. A coverage-hole report is source evidence, not a safety PASS. If it appears, do not initiate additional requests; retain the single bounded request's diagnostics or cancel on any correctness/safety failure. No repeat of either arm. A failed control blocks the adaptive arm; a failed adaptive arm ends experimental work.

## Optional matched adaptive arm

Only after the static request completes correctly, graceful engine shutdown/resource release pass and `elapsed+390<=600` seconds, restart the same transient unit with **only** this configuration argument changed:

```text
--config /data/strata-lab/JR-Strata-SYCL-v0139-FastFix/tools/fastfix/aplan-control-adaptive.json
```

All systemd arguments and environment remain as printed above; the original adaptive defaults are4/96. Do not change the unit or launch a simultaneous engine. Repeat the same frozen `aplan-request.json` curl command, writing `adaptive-response.sse`. Both arm logs are separate (`static-engine.log`, `adaptive-engine.log`). If insufficient time remains, skip this arm, restore RC1 and mark the matched causal comparison BLOCKED. No extra authorization/window is inferred from skipped work.

Admission examples: elapsed210s allows an arm ending no later than600s; elapsed211s refuses it. CPU-only preview and artifact verification:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/aplan-control-plan.py --verify
```

This command only verifies files and prints the plan. It never stops services, maps GPU devices or performs inference; execution follows the approval-gated procedure above.

## Teardown and restoration

```bash
systemctl --user stop jr-strata-fastfix-aplan-test.service
journalctl --user -u jr-strata-fastfix-aplan-test.service --no-pager \
  > logs/fastfix/aplan-control-window-01/server-journal.txt
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

## Frozen offline diagnostic build

Engine source commit: `ee3ab2dba75a9597d5ad2c76e8d8e5fb5f764907`. Build: **PASS**, CPU-only historical Docker build.

Experimental ELF: `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/build-fastfix/strata`

SHA256: `6b00ee839b6cf342fc85bdefa504e17fa80cc3fd94f766611e3707bf1120d6fe`

Captured handoff probe SHA256: `3237f2ced414e38d1695631b121dd6dcb54b30fd7a361da615f647323a1de4fa`. It is compiled, not GPU-tested.

Rebuild with `bash tools/fastfix/build.sh`; CPU checks with `bash tools/fastfix/cpu-tests.sh` and `python3 -B tools/fastfix/p0-harness-tests.py`. The manifest freezes the experimental binary, probe, profile, request, launcher and changed engine sources. Do not reuse an older maintenance manifest.

Final read-only RC1 check: 2026-10-09 09:22 AEDT, service active/enabled, server198898, engine199664, frozen SHA256 and32768 context, native status reachable, no kernel fault lines since08:52:18. No production lifecycle action or inference request was made. Evidence: `docs/jr-v0139-fastfix-evidence/aplan-offline/`.

## Adaptive-control interpretation

The existing15-minute window now prioritizes the static diagnostic control. `--adapt-swaps 0` disables the default adaptive activity through its existing serving gate; no inference source or binary was changed for this control. It retains the same10831/17990MiB startup expert tier and13745-expert mirror. Prefill borrowing and restoration remain enabled and must still pass actual coverage/ordering checks.

A correct1536-token static completion, by itself, supports further investigation of adaptation but does not prove the mirror hypothesis or general reliability. Disabling adaptation also removes swap DMA, event admission, usage tracking and a background thread; output rounding, MTP acceptance and Decode speed can consequently differ. Report actual output lengths and correctness separately; do not compare failed prefixes as performance.

If the adaptive arm emits coverage holes and the failed ring records the corresponding expert with `slot<0,mirror==0`, this establishes a direct missing-coverage path. If holes appear without timeout, the invariant defect is demonstrated but the archived ring47 cause remains unproven. If a static arm fails while its route is covered, investigate skip visibility/graph progress rather than calling adaptation the cause. A missing `APLAN_RESIDENCY` line in the static arm is expected (no pending swaps), and is not proof of coverage: use the actual per-ring planner observations, initial mirror counts and kernel diagnostics.
