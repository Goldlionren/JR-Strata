# FastFix permanent production deployment

On 2026-10-09 the operator promoted the unchanged, GPU-validated Adaptive Mirror FastFix to production and deprecated RC1. **FastFix is ACTIVE/ENABLED; RC1 is INACTIVE/DISABLED.** There is no automatic RC1 fallback. Use [operations](JR_SYCL_V0139_FASTFIX_PRODUCTION_OPERATIONS.md) and [actual deployment results](JR_SYCL_V0139_FASTFIX_PRODUCTION_REPORT.md).

Validated checkout: `c6a8a55dbd2989dd51f5355e9a83eb76198fe832`; inference source: `be3105e7f66ef4f9668ef129a1938800954b1b3b`. The operational commit adds launch/supervision/evidence files; it does not rebuild or modify inference source. Running ELF SHA256:

`8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`

The 58,760,440-byte tested ELF is copied unchanged to `dist/jr-b60-sycl-v0139-fastfix-adaptive-mirror/strata` (mode0555). Original `build-fastfix/strata`, historical artifacts, RC1 binary/tag/profile/unit, model/pack/MTP/ranking, PLEFix/v0.1.41/Vulkan and host runtime/driver remain unchanged. `deploy/fastfix/manifest.json` pins the frozen artifact plus validated input/source files and production startup files. A mismatch refuses startup; no rebuild or substitute is attempted.

Runtime image remains exactly `sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`. Stock SYCL2026.1.0, UR0.12.0, LevelZero1.32.0; original build compiler2026.1.1. Live process mappings and container inspect are archived. GPU: B60 `0000:07:00.0`, `8086:e211`, selected `level_zero:0`; no host driver/oneAPI/package changes.

## Installed files and exact configuration

- Service: `jr-strata-sycl-fastfix.service`; installed at `/home/james/.config/systemd/user/jr-strata-sycl-fastfix.service` (mode0644), identical to `deploy/fastfix/jr-strata-sycl-fastfix.service`.
- Launch profile: `/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/deploy/fastfix/runtime.json`.
- Native server: original `sycl/serve/server_intel.py` importing original `serve/server.py` and `serve/web/`; host Python from `/data/strata-lab/Strata/.venv/bin/python`.
- Engine wrapper: `deploy/fastfix/engine-wrapper.py`; same Docker flags/environment as window02, only pinned executable pathname differs. Container `jr-strata-fastfix-engine`, `/dev/dri`, read-only `/data/strata-lab:/work`, original stock runtime.
- State/engine log: `logs/fastfix-production/current.json`, `ready.json`, `starts.jsonl`, `engine.log`; stdout/stderr in the systemd journal.

All inference argument values equal the validated `tools/fastfix/mirror-repair-runtime.json`. Changes are endpoint/log destination and production wrapper path. Paths inside the container:

| Setting | Preserved value |
|---|---|
| Pack | `/work/data/packs/swift-iq3_xxs` |
| Native GGUF / PLE GGUF | `/work/data/models/swift-IQ3_XXS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf`; existing second shard resolved normally |
| Expert ranking | `/work/Strata/data/expert-profile.bin` |
| MTP | `/work/data/mtp/rt`; Spec4, min-p0.5, original suffix semantics |
| GPU expert cache | Original `--expert-cache 8098` native-size grant produces10831 slots/17990MiB (17.57GiB); do not replace the CLI grant with10831 |
| Host Mirror | Full complement13745/13745,22.40GiB; repaired ownership exchange |
| Adaptive swaps | ON, original4/96 defaults; observed committed swaps |
| KV/context | INT8,131072 configured context,32768 resident KV |
| Prefill / VRAM reserve |4096 /768MiB |
| PCIe fraction |0.25 |
| Safety | Alias checking, uncached host handoff, verifier/device-plan and repaired per-layer payloads retained |
| API/UI | `127.0.0.1:18083` only |

Native metrics `spec=6` is maximum verifier capture T; `mtp_max=4` and CLI `--spec 4` identify the MTP setting. Preserve the validated host-assisted verifier path; do not enable `STRATA_VERIFY_NO_HOST` as an untested configuration change. No PLE I/O or expert-ranking tuning belongs to this deployment.

## Supervision and boot policy

The service uses Type=exec. `start.py` validates artifacts, original image, target device, health,32GiB host availability,22GiB unloaded VRAM, port and mutual exclusion, then **execs the unchanged native server**. `ready.py` checks the actual running Docker ELF/image, GPU name,10831 slots,13745 mirror coverage,131072/INT8/32768 KV, MTP and at least512MiB loaded headroom without inference.

SIGTERM goes to the native server MainPID; it sends QUIT and waits for engine cleanup. KillMode=process, SendSIGKILL=no, TimeoutStopSec180; no broad pkill or container force removal. The native server implementation and its validated ordinary shutdown are unchanged. A stuck engine must be treated as an incident; do not send the server's second-interrupt force-exit path.

Restart=on-failure,30s delay, at most3 starts per600s; startup refusals78 and unsafe86 are excluded from restart. Startup/engine-launch guards reject prior readiness/safety errors, surviving owned containers or new kernel faults. They do not silently start RC1. Normal intentional systemctl stop does not restart the service. Conflicts/After against RC1 enforce mutually exclusive service jobs; wrapper also refuses RC1 active/activating/deactivating, and the production server holds a process-lifetime lock.

FastFix's default.target symlink exists. Existing `Linger=yes` and Docker daemon ACTIVE/ENABLED were verified; no linger or Docker policy change was necessary. RC1's former default.target symlink was removed with `systemctl --user disable`. Its unit contents and all historical artifacts were preserved. Actual host reboot was not performed; boot configuration is verified, not a reboot test.

The installed initial cutover and two CPU-only harness corrections are fully preserved. No additional2048-token benchmark, seven-test repetition, inference rebuild or model change was performed. Permanent cutover smoke uses the same executable qualified by [window02](JR_SYCL_V0139_FASTFIX_MIRROR_GPU_RESULTS_WINDOW02.md).
