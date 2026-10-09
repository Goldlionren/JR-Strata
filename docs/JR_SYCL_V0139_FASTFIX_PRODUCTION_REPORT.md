# FastFix production cutover results — PASS

Final operator decision enacted on2026-10-09: FastFix **ACTIVE/ENABLED**, RC1 **INACTIVE/DISABLED**. No RC1 fallback or restoration occurred. FastFix remains running for interactive use at **http://127.0.0.1:18083/**.

Final server PID **1749394**, Docker engine host PID **1749505**; container `jr-strata-fastfix-engine`. Actual running engine SHA256:

`8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`

Configuration: `deploy/fastfix/runtime.json`; frozen ELF `dist/jr-b60-sycl-v0139-fastfix-adaptive-mirror/strata`, hash-identical to the validated build, no rebuild. Docker image `sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`; live mappings confirm stock SYCL/UR/LevelZero. Engine source `be3105e7f66ef4f9668ef129a1938800954b1b3b`; validated checkout `c6a8a55dbd2989dd51f5355e9a83eb76198fe832`. Later operational/docs commit is not a new compiled engine.

## Acceptance

| Requirement | Result | Evidence |
|---|---|---|
| Exact qualified ELF/runtime/model/ranking/settings | PASS |38 validated input hashes plus production manifest; running Docker ELF/image inspected; inference args byte-for-byte equal |
| RC1 idle and graceful stop | PASS |Two idle samples; native stopped; server/engine gone, GPU22.485607GiB free |
| RC1 deprecated startup policy | PASS |INACTIVE/DISABLED, default.target symlink removed; original unit/profile/binary/ranking hashes unchanged |
| Permanent FastFix startup | PASS |ACTIVE/running, server1749394, engine1749505; loaded B60 confirmed |
| Context/KV/MTP | PASS |131072 configured context, INT8/32768 resident, CLI Spec4/min-p0.5; native maximum captureT6/MTPmax4 |
| Residency/full Mirror | PASS |10831 slots/17990MiB (17.57GiB);13745/13745 mirror/22.40GiB |
| Loaded headroom | PASS |**655MiB**, above512MiB; prior successful initial production startup reported649MiB |
| Adaptive ON with repaired ownership | PASS |Current successful smoke **1344 swaps/14 committed generations**, original4/96, zero holes |
| Native Chat/API functional | PASS, scoped |English generation, correct complete Chinese answer and42 arithmetic; English capped at64 tokens, not a complete-answer PASS |
| Native Monitor/About dependencies | PASS |`/status`, `/metrics`, `/health`, `/config`, `/settings`, `/v1/models` HTTP200; original Chat/Monitor/About markup and upstream assets unchanged |
| MTP drafting | PASS |Current smoke106 proposed/58 accepted,54.72% aggregate MTP+suffix; separate MTP-only is N/A |
| Clean candidate teardown/fresh restart | PASS |Initial production engine started with correct identity, ordinary reasoning-only smoke reached its cap, then native SIGTERM/QUIT stopped cleanly; final fresh startup passed |
| Zero new GPU faults/reset | PASS |Full operation kernel journal; no readiness/ownership/payload/unsafe markers; no force-kill |
| Boot autostart configuration | PASS |FastFix ENABLED/default.target symlink; existing Linger=yes; Docker daemon ACTIVE/ENABLED; policies unchanged except Strata service cutover |
| Actual reboot test | NOT RUN |Host reboot not needed/authorized as validation; no claim of executed reboot |
| New2048-token performance/128K prompt test | NOT RUN |Operator explicitly excluded another long benchmark; prior qualified25.3tok/s/2048 evidence retained |

Current smoke measurements (short cold/new prompts, not matched sustained benchmarks):

| Request | Prompt/output | Decode tok/s | Draft accepted/offered | Finish/quality |
|---|---:|---:|---:|---|
| English freezing-point explanation |25/64|13.6|33/68|LENGTH_CAPPED; correct initial explanation, second sentence incomplete |
| Traditional Chinese explanation |32/44|14.8|22/35|Normal EOS; complete and coherent |
|6×7|26/3|7.2|3/3|Normal EOS;42 correct |

The historical qualified garden-manual **25.3tok/s over2048 actual tokens** is unchanged evidence for this ELF/settings. It is not a new deployment measurement or a universal rate. No RC1 comparison, kernel tuning, expert-ranking change or long benchmark was added. Decode-time PLE I/O and untested long endurance/real128K coverage limitations remain recorded in window02.

## Preserved cutover corrections

The operation began at 2026-10-09T13:10:02.526529+11:00; final ACTIVE/ENABLED verification completed after **273.240s**, using the original operation epoch across continuations. RC1 was never restarted after its authorized stop.

1. The initial lightweight port probe omitted SO_REUSEADDR and rejected stale TCP TIME_WAIT after clean RC1 shutdown. Targeted `ss` showed **no listener**; bind with native Linux SO_REUSEADDR succeeded. Only the CPU launch preflight was corrected to match `serve/server.py`'s existing `Server.allow_reuse_address`. Two CPU regressions prove completed connections are accepted and active listeners still rejected. No engine/runtime change.
2. The first smoke request used unsupported top-level `thinking:false`;64 generated tokens were ordinary reasoning and no final answer before its cap. This was **LENGTH_CAPPED**, not repeated punctuation, invalid GPU state or corruption. Evidence/response is preserved. The responsive candidate was gracefully stopped without a fault. Final smoke uses the archived supported `chat_template_kwargs.enable_thinking=false`. Production model/engine defaults remain unchanged.

Eight CPU deployment cases and systemd syntax verification pass. The unrelated existing music unit's executable-permission warning was left untouched. XPU-SMI optional MEI/DMI diagnostics report permission limitations; target device accounting/normal state works and no policy/sudo/driver change was made.

## Evidence and operational state

Installed unit `/home/james/.config/systemd/user/jr-strata-sycl-fastfix.service` matches the repository unit. FastFix and RC1 cannot be active together through their systemd conflict/order relationship; launch also checks RC1 state and existing owned containers. Bounded restart30s/3-per600s refuses safety/hash/resource incidents; no RC1 fallback logic exists. No automatic trial shutdown is installed.

Logs: `logs/fastfix-production/`; service stdout/stderr: `journalctl --user -u jr-strata-sycl-fastfix.service`. Preserved evidence and SHA inventory: `docs/jr-v0139-fastfix-evidence/production-cutover-20261009/`, including both CPU harness interruptions, clean shutdown, final responses/config/image/maps, native assets, boot policy and full kernel diagnostics. RC1 frozen files and unrelated Docker containers remain intact.

Use [the production operations SOP](JR_SYCL_V0139_FASTFIX_PRODUCTION_OPERATIONS.md). On genuine corruption or hardware fault, stop/assess/repair FastFix and preserve diagnostics; temporary unavailability is accepted. RC1 is historical, **not a recommended or automatic recovery service**. No push, published release, driver/package change or further experiment occurred.
