# FastFix P0 narrow GPU validation — approval pending

No GPU testing has been performed for this candidate. This is a new window; previous approvals are not reused. Root-cause limits and offline evidence: [ring report](JR_SYCL_V0139_FASTFIX_RING_TIMEOUT.md).

## Exact commands

CPU-only preview (safe now):

```bash
cd /data/strata-lab/JR-Strata-SYCL-v0139-FastFix
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/p0-maintenance.py --out logs/fastfix/p0-window-01
```

Only after fresh focused maintenance approval:

```bash
cd /data/strata-lab/JR-Strata-SYCL-v0139-FastFix
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/fastfix/p0-maintenance.py   --execute-authorized --out logs/fastfix/p0-window-01
```

The old `maintenance.py` and failed executable remain blocked. New controller uses the exact current `p0-frozen.json`, including binary, tests, wrapper, runtime and harness hashes; any mismatch stops before RC1 shutdown. It cannot resume or reset a prior window clock. Nothing installs a service or changes autostart.

## Bounds and sequence

Request **one 45-minute window**, expected approximately 25–35 minutes including restoration. Clock starts before preflight. Each experiment's upper bound plus teardown allowance must fit before minute 30. Cleanup completes by minute 35; final ten minutes are reserved for RC1. If a required request cannot fit, report incomplete/BLOCKED rather than extend the window.

1. Verify idle/unqueued RC1 twice, frozen disk and running SHA256, original config/unit/ranking checksums, free port18086, historical Docker identity, B60 PCI `0000:07:00.0` / `8086:e211`, readable kernel journal and no unresolved faults. No global ownership helper or sudo policy work.
2. `systemctl --user stop jr-strata-sycl-rc1.service`; verify server and recorded child engine PIDs exited. Require B60 normal, at least22GiB device free and50GiB host available; block confirmed conflicts. Validate Docker selector by `sycl-ls --verbose` before inference. No unrelated processes are stopped.
3. Seven safety tests, in order: `fastfix_memory_safety`, `kv_q8_parity`, `kv_stream_parity`, `iq_multi_parity`, `native_grouped_parity`, `quantize_act_parity`, `fastfix_ple_staging`. Each has a150s external test timeout and175s controller bound. Stop on any failure.
4. One `fastfix_handoff` test: captured timeout/rejected-plan safety, readiness latch/skip behavior, controlled delayed DMA with event dependency, and completed host output visibility. Same timeout. Tests intentionally expired flags in an isolated small probe; unexpected faults/errors are never accepted.
5. Start fixed10,831-slot engine, full mirror, original model/pack/ranking/runtime, 131072 INT8/32768 resident KV, prefill4096, reserve768MiB, Spec4/min-p0.5, host-assisted path unchanged. `STRATA_ARENA_ALIAS_CHECK=1`, uncached handoff protection retained, `STRATA_VERIFY_TRACE=1`. T=1 control adds only `STRATA_TEST_VERIFY_NO_DRAFT=1`; run the four English/Chinese/Python/math tasks and one512-token fixed garden-manual continuation. Actual output must extend past306 tokens; preserve semantic and repetition review. Graceful shutdown must pass before next arm.
6. Repeat with ordinary historical Spec4 drafting (test switch absent), identical cache slots/settings, same functional tasks and same512-token prompt. Only after those pass, request one2,048-token continuation of the same fixed garden-manual workload. Keep full output, actual lengths, per-request metrics and resource samples; do not interpret an early EOS as full-length coverage. No retries of a failing workload.
7. Stop only the experimental systemd unit using SIGTERM → native server QUIT → queue drain, verify no container/listener/engine survives, then assess GPU health before restoring RC1.

MTP-off here means **no Decode drafting**, while retaining the historical server's supported verifier allocation and prefill initialization; it is not `--spec 0`. T=1 and speculative floating-point paths need correct semantic answers, not assumed bitwise identity. Short functional answers are reviewed against independent Python/math oracles. Natural-language and full long-response semantics require explicit review; automated keyword checks alone cannot certify correctness.

## Evidence and STOP gates

Retain precise kernel timestamps, full engine stderr, native server journal, readiness A/B/M first-failure values, layer/group/T/position/window, host and GPU trace breadcrumbs, queued/published DMA callbacks, Docker maps/identity and per-request JSON. Measure actual generated tokens, MTP counts, prefill/decode/TTFT, VRAM/GTT, host RAM/swap and disk reads. No performance claim from a failed prefix.

STOP further experiments on: any new page fault/reset/wedge; readiness timeout; invalid token/nonfinite/corrupt output; `!!!!!` or sustained abnormal repetition; failed numerical test; incomplete mirror; changed cache budget; resource conflict; engine hang; unsafe teardown or surviving container. Memory below4GiB host headroom during a request also stops the run. Admission limits stop further work before the recovery reserve.

`FASTFIX_UNSAFE_TEARDOWN`, exit86, a readiness failure or a serious driver fault blocks automatic restoration until hardware state is assessed. Preserve diagnostics and report immediately. Do not force-kill a stuck engine, blindly restart RC1, or launch another experiment. The five-second error-drain policy is bounded; a malfunction inside the SYCL runtime itself still relies on the outer watchdog/controller and must not be called a successful teardown.

## RC1 recovery

The controller restores unchanged RC1 only after clean experimental exit and fault/resource checks:

```bash
systemctl --user start jr-strata-sycl-rc1.service
systemctl --user show jr-strata-sycl-rc1.service -p ActiveState -p SubState -p MainPID
curl --fail http://127.0.0.1:18083/v1/models
/home/james/.local/bin/jr-sycl-watch --json
```

Verify the running engine `/proc/PID/exe` SHA256 is `cfb7ee7610c373260a5e4ec62cbb609666055bff01d721bd521f5192d68d0028`, context32768 and original9248-expert configuration/mirror, then one short32-token arithmetic API smoke request, native `/status` and `/metrics`, unchanged protected-file hashes, autostart state and kernel journal. RC1 remains running afterward. If a fault occurred, these commands are conditional on a separate recorded health assessment; the controller does not restart into uncertainty.

No promotion, new ranking, runtime replacement, C1/C2/C3 task or optimization is part of this window.


Budget detail: the preserved log grants **8,098 uniform max-blob slots**, then the existing variable-size native planner expands them into **10,831 profile-ordered experts / 17,990 MiB**. The new controller uses `--expert-cache 8098`, verifies exactly10,831 loaded experts and17,990 MiB with the unchanged ranking, full13,745-expert mirror, and at least512MiB remaining VRAM. Passing `10831` directly to this CLI would enlarge the byte budget and is deliberately avoided. This is the original planner and byte budget, not a new residency optimization.


Frozen new executable: `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/build-fastfix/strata`

SHA256: `14db752d630df2c1d992f77e0da71eb61852ffca0ab6c77ef71bda646af63434`

Final isolated build: **PASS** (`logs/fastfix/p0-final-build.log`). Engine source `47f505b`; controller/profile checks `5a9e576`. CPU lifecycle policy also passes ASan/UBSan. GPU tests have **not** been executed. Final read-only production check: server1586519, engine1587016, frozen RC1 hash, context32768, active/enabled; no new kernel faults in the 07:30–08:39 offline check interval.
