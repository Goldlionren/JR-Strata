# FastFix mirror repair: narrow Adaptive ON validation

**NOT AUTHORIZED / NOT EXECUTED.** This plan needs a fresh operator maintenance decision. Earlier15/45-minute approvals are closed. RC1 remains running during preparation. No additional optimization, Adaptive OFF endurance arm, ranking training or runtime change belongs to this plan.

## Identity and offline gate

Worktree `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix`, branch `jr-b60-sycl-v0.1.39-fastfix`. Engine source: `be3105e` (full revision and final ELF/probe hashes in `tools/fastfix/mirror-repair-candidate.json`). Historical image exactly `sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`; existing compiler2026.1.1, stock image SYCL2026.1.0/UR0.12.0/LevelZero1.32.0. No host runtime mounts during execution.

CPU-only verification, safe while RC1 runs:

```bash
cd /data/strata-lab/JR-Strata-SYCL-v0139-FastFix
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/mirror-repair-plan.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/mirror_plan_test.py
```

This prints/verifies files and deadlines; it does **not** manage production or execute GPU work. Do not reuse `p0-maintenance.py` or `aplan-control-plan.py` as an execution controller for this new binary: their historical manifests remain frozen.

## Bounded window and stage admission

Propose **20 minutes total**, starting at recorded preflight timestamp, with experimental execution **and teardown finished by minute15** and the final5 minutes reserved for GPU assessment/restoration. Do not reset the clock. CPU plan constants:1200 total/900 experiment seconds. Admit work only if `elapsed + work_bound +90 <=900`; stop experimental admission when this fails. Bounds are ceilings, not observed new-binary durations.

| Stage | Bound | Gate |
|---|---:|---|
| Seven existing safety/numerical tests |120s combined|All pass; otherwise no model load|
| Existing captured readiness probe |30s|All readiness/dependency checks pass|
| New real GGUF mirror/payload probe |120s|Independent full-blob hashes, pending-alias rejection, repeated captured plans and per-layer payloads all pass|
| One Adaptive ON server startup |120s|Frozen binary/runtime, startup10831 experts/17.57GiB and13745/13745 mirror, at least512MiB loaded free VRAM|
| One2048-token long generation |240s|No coverage hole, invalid output, readiness failure or GPU error|
| Three subsequent short requests |90s combined|Cold/warm transitions and different output lengths; no configuration change|
| Experimental graceful shutdown |90s|Server QUIT, queue completion, container/engine/port gone|

Bounds sum810 seconds, leaving90 seconds of experimental slack for checks/measurement. Optional subsequent requests are skipped if admission fails; record incomplete coverage. If even mandatory stages cannot fit, restore RC1 and report BLOCKED. Do not repeat a failed workload or fit time by force-killing an engine. An unexpected hang/unsafe teardown is an incident; preserve evidence and assess hardware rather than restart blindly.

## Lightweight preflight and authorized production lifecycle

After future approval only, create a fresh `logs/fastfix/mirror-repair-window-01` evidence directory; refuse an existing nonempty directory. Record timestamp, RC1 service state/enabled policy, server/engine PID and frozen SHA256 `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`. Confirm `/status` busy=false,queued=0 immediately before stop; inspect `/metrics` active/queued counters too. Confirm B60 sysfs PCI0000:07:00.0 vendor0x8086/device0xe211 and exact LevelZero selection. Save kernel journal cursor/timestamp and current resource snapshots. Use the already accepted operator-controlled resource check; never require a global PID census or new sudo policy.

Check18086 free and no existing `jr-strata-fastfix-engine` or test unit. Unexplained substantial competing allocations or active production requests block the cutover; do not terminate unrelated processes. After graceful RC1 stop, require the known engine/server PIDs exited, release of its B60 allocation, adequate measured GPU free memory (at least23GiB before high-residency loading) and MemAvailable at least32GiB with no active swapping. This budget includes22.40GiB mirror,1.55GiB host KV,~1.11GiB GGUF ring and operating headroom. A small idle desktop allocation is allowed under the existing dedicated-host policy.

Stop RC1 exclusively through its unchanged unit:

```bash
systemctl --user stop jr-strata-sycl-rc1.service
```

Preserve the recorded Server QUIT/queue-drain journal. Do not disable/change installed units, drivers or runtime. All Docker model/pack/source mounts are read-only.

## Safety/probe commands

The verified image entrypoint is `["/bin/bash","-lc"]`, so pass its command as one string, as the historical wrapper does. Use the exact image ID and selected B60; each short probe runs alone after production resource release. The following loop is sequential. The outer approved controller/operator must enforce the combined stage deadline without SIGKILL; an unexpectedly surviving probe halts testing.

```bash
for test in fastfix_memory_safety kv_q8_parity kv_stream_parity iq_multi_parity native_grouped_parity quantize_act_parity fastfix_ple_staging; do
  command="exec /work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/$test"
  case "$test" in
    kv_q8_parity|kv_stream_parity|quantize_act_parity) command+=" --selftest";;
    fastfix_ple_staging) command+=" /tmp/fastfix-ple-mirror.gguf";;
  esac
  docker run --rm --name jr-fastfix-mirror-safety --device /dev/dri \
    -e ONEAPI_DEVICE_SELECTOR=level_zero:0 -e SYCL_CACHE_PERSISTENT=0 \
    -e STRATA_ARENA_ALIAS_CHECK=1 -e STRATA_HOST_UNCACHED=1 \
    -v /data/strata-lab:/work:ro \
    sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44 \
    "$command" \
    > "logs/fastfix/mirror-repair-window-01/$test.log" 2>&1 || exit 1
done
```

Run `build-fastfix/fastfix_handoff` with the same Docker/environment/mount arguments. Then run the **new** actual-source probe:

```bash
docker run --rm --name jr-fastfix-mirror-probe --device /dev/dri \
  -e ONEAPI_DEVICE_SELECTOR=level_zero:0 -e SYCL_CACHE_PERSISTENT=0 \
  -e STRATA_ARENA_ALIAS_CHECK=1 -e STRATA_HOST_UNCACHED=1 -e STRATA_APLAN_DIAG=1 \
  -v /data/strata-lab:/work:ro \
  sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44 \
  'exec /work/JR-Strata-SYCL-v0139-FastFix/build-fastfix/fastfix_adaptive_mirror /work/data/packs/swift-iq3_xxs /work/data/models/swift-IQ3_XXS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf' \
  > logs/fastfix/mirror-repair-window-01/adaptive-mirror-probe.log 2>&1
```

It loads three small GPU slots and three pinned slots on layers0/32/46, reads independent GGUF reference blobs, runs12 delayed ownership exchanges and reuses one captured resident-plan graph. It tests the production `GgufExpertSource` transaction, not just a similar fake swap. A controlled future holds the copy queue; pending alias access must reject before release. Both experts' full quantized weight hashes and device-plan coverage must match after every publication. Separate captured doorbell graphs validate delayed host consumption for T1/4/6, split/unsplit and changing windows. This establishes byte/capture ordering; the existing native arithmetic/parity tests cover computation separately. It does not certify the entire17.57GiB cache or every source of historical corruption.

## Adaptive ON inference

Use the existing native Python server and unchanged Docker wrapper. New profile arguments equal the archived original profile exactly; only log destination differs. Adaptive defaults remain4/96, original ranking and sized cache grant8098 (expected10831 actual expert slots), context131072/INT8 resident32768, prefill4096, reserve768MiB, Spec4/min-p0.5 and PCIe fraction0.25. PLE I/O, suffix/MTP and sampling semantics are unchanged. Keep original host loop enabled to exercise the independent payload repair; do not add `STRATA_VERIFY_NO_HOST` as a simultaneous experimental change.

```bash
systemd-run --user --unit jr-strata-fastfix-mirror-test.service --collect \
  --service-type=exec -p Restart=no -p KillMode=process -p KillSignal=SIGTERM \
  -p SendSIGKILL=no -p TimeoutStopSec=90 \
  --setenv=PYTHONDONTWRITEBYTECODE=1 --setenv=PYTHONUNBUFFERED=1 \
  --setenv=FASTFIX_P0=1 --setenv=FASTFIX_APLAN_DIAG=1 \
  --setenv=FASTFIX_NO_DRAFT=0 --setenv=FASTFIX_NO_HOST=0 \
  --working-directory=/data/strata-lab/JR-Strata-SYCL-v0139-FastFix \
  /data/strata-lab/Strata/.venv/bin/python -B \
  /data/strata-lab/JR-Strata-SYCL-v0139-FastFix/sycl/serve/server_intel.py \
  --engine strata \
  --config /data/strata-lab/JR-Strata-SYCL-v0139-FastFix/tools/fastfix/mirror-repair-runtime.json \
  --host 127.0.0.1 --port 18086
```

Before generation verify Docker `/proc/1/exe` against the **new candidate** hash, actual loaded libraries, correct B60 and initial expert/mirror/cache byte counts. Verify allocation alias guard enabled and actual GPU free memory. Reject a silent residency reduction. Save initial `/v1/models`, `/metrics`, `/status`, resource samples and process IO counters.

```bash
curl --fail --no-buffer --max-time 240 \
  http://127.0.0.1:18086/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary @tools/fastfix/mirror-repair-request.json \
  > logs/fastfix/mirror-repair-window-01/long-response.sse
```

This is the archived garden-manual prompt with only the output cap changed1536→2048; deterministic temperature0/seed42/thinkingoff. Count actual output tokens; early EOS is incomplete trigger coverage, not a2048-token PASS. Inspect complete decoded response and streamed IDs for corruption, invalid/nonfinite values, repetition and `!!!!!`/`root!!!!!`. Stop immediately on a correctness defect. No old defective output is a numerical oracle.

During generation sample `/metrics`, process `/proc/PID/io`, major faults, RAM/swap, B60 VRAM/GTT and kernel journal. Capture all `APLAN_EXCHANGE`, mirror/residency generation lines, coverage holes, first failure ring/layer/expected/observed/expert/mirror/event data and queue completion. Report actual swaps committed, not just configured ON. If no swaps occur, mark adaptive trigger coverage BLOCKED. Before/after and periodic samples must distinguish legitimate bounded buffers/page cache from progressive growth.

Only after clean long generation and admission, make three short sequential64-token functional requests (English, Chinese, deterministic arithmetic) on the same process; inspect actual answers. No additional lengthy benchmark, Adaptive OFF arm or fresh engine is admitted. Record Decode, prefill/TTFT, actual outputs, MTP proposed/accepted, verifier/host timings, residency/cache bytes/mirror bytes and I/O. Physical PCIe traffic remains N/A unless directly measured; do not infer it from logical copy bytes.

## STOP and restoration

Immediate STOP: first missing expert coverage, stale owner/generation, wrong probe bytes, invalid/corrupt output, readiness timeout, asynchronous error, GPU fault/reset, unexpected resource conflict, unsafe teardown or surviving experiment. Do not increase timeouts or disable alias/readiness protections. Preserve logs and timestamps; no retry of the failing arm.

On clean completion or ordinary cancellation, use only the native server lifecycle:

```bash
systemctl --user stop jr-strata-fastfix-mirror-test.service
journalctl --user -u jr-strata-fastfix-mirror-test.service --no-pager \
  > logs/fastfix/mirror-repair-window-01/server-journal.txt
```

Require SIGTERM→Server QUIT→completed queue drain, engine/container exit and18086 release; save full kernel diagnostics/resource release. A client timeout/disconnect is not proof of engine cleanup. No force-kill, broad pkill or unrelated process termination. If completion cannot be proven, suspend automatic restoration and assess hardware; `_Exit(86)` is an unsafe-teardown report, not a healthy exit.

After fault-free assessment and clean resource release only:

```bash
systemctl --user start jr-strata-sycl-rc1.service
systemctl --user show jr-strata-sycl-rc1.service -p ActiveState -p SubState -p MainPID
curl --fail --max-time 10 http://127.0.0.1:18083/v1/models
/home/james/.local/bin/jr-sycl-watch --json
```

Verify running RC1 ELF frozen SHA, original32K/ranking/mirror, native status/metrics/UI, one short arithmetic request and no new kernel fault. RC1's enabled policy remains unchanged. Complete recovery before minute20; do not admit more GPU work under unused time or promote FastFix.

Report separately probe/ownership, payload coherency, Adaptive ON sustained output, actual swap coverage, performance, memory, GPU faults, graceful shutdown and RC1 restoration. New failures stay FAIL; unexecuted/incomplete gates stay BLOCKED. Success is a narrow repair test, not a release qualification.
