# Production freeze —2026-10-09

**FastFix ACTIVE/ENABLED; RC1 INACTIVE/DISABLED. Production was not restarted or reconfigured.**
Final read-only verification:2026-10-09T15:09:24.958875+11:00. Server PID1749394; engine PID1749505. Container732842edcb139eae050ecb46e9538190ac4440ef682e635efb4bdbec76e849c6
started2026-10-09T02:14:07.620265402Z throughout this task, systemd NRestarts0.

| Identity | Frozen value |
|---|---|
| Release tag |jr-b60-sycl-fastfix-prod-20261009 (annotated; never moved)|
| Tag / packaging commit |06bb157c26c6cb7ce96a275a5f815a40bb4209a5|
| Engine source commit |be3105e7f66ef4f9668ef129a1938800954b1b3b|
| Engine source tree |dcb458f77d3f8370b72ab42cadc94ec41aa1e119|
| Live deployment checkout |0953f6eff9b288d84fea1b1e74905707ffa9ffaf (clean; branch unchanged)|
| Running / published engine ELF |8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e|
| Installed systemd unit SHA256 |d96ec3656d2298b5fc33519d5629e3f67978ddefea0536e9fc650162fd61e0c5 (unchanged)|
| OCI index/image |sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44|
| OCI amd64 manifest |sha256:cdafd5ce1975e0449f51608d77fcd4bd7bda03374b1aed744c273d932d08f5fe|
| OCI config |sha256:ff4cac32a0d7642362f0efba05b4fb9ff27776ce63459924382c43b78807cb39|
| Original complete archive |59f17cd2686b419c3590f82cfb4df5630b74a47a55a01d6184ad9e278add96de|

Engine source, deployment checkout and packaging commit are distinct. Follow-up publication merges/operations docs on main
leave the tag/ELF/source tree unchanged. A normal merge preserves the remote's two earlier documentation commits;
no force push/history overwrite. Inference source under src/include/sycl remains byte-identical to the engine source.

Runtime:oneAPI2026.1.0-235/UR0.12.0/LevelZero loader1.32.0/IntelGPU userspace26.35.39758.10-0. Build compiler2026.1.1
(2026.1.1.20260724), independently labeled. Image Linux/amd64,Ubuntu26.04. Host Ubuntu24.04.4, kernel7.0.0-34-generic,
xe version17010844, B60 PCI8086:e211. Actual mapped-library hashes/package inventories/complete non-secret environment,
command, installed launcher/unit and model/pack/MTP/ranking hashes are in `deployment/manifests/`.
The archived OCI blobs/rootfs/env match the running image. No library, image, compiler,driver or kernel was changed.

Production stays10831GPU experts/17990MiB (17.57GiB),13745/13745 mirror (22.40GiB),Adaptive4/96,MTP CLI4,
131072 configured context,INT8 KV32768 resident,prefill4096,reserve768MiB,original ranking8f59b4aa….
INFO spec6 is the graph capture maximum; mtp_max4 and CLI Spec4 are the configured MTP behavior.
[Native UI/API](http://127.0.0.1:18083/) is HTTP200 with original Chat/Monitor/About; models reports131072, metrics match
residency/KV/MTP, live state idle at the final sample. No generation/benchmark was requested during this freeze.
Kernel journal since production startup contains **zero new GPU faults/resets**; XPU-SMI device state normal.
XPU-SMI supplemental DMI access warns permission unavailable; this is recorded, not bypassed.

Existing user linger=yes,Docker enabled,FastFix user default.target link enabled; RC1 disabled. Actual reboot was not
performed. Config/unit/launchers have identical before/after hashes, PIDs/container start unchanged. Docker restart=no;
systemd sole supervisor retains SIGTERM→Server QUIT→SYCL drain and SendSIGKILL=no. No automatic dependency/image upgrades,
runtime switches,RC1 fallback or experimental service installation were added.

## Acceptance and distribution status

| Check | Result | Evidence |
|---|---|---|
| Running version frozen without restart |PASS|final-production-health.json,unchanged unit/launcher hashes|
| Source/tag/Release published |PASS|remote tag06bb157,main ancestry,actual Release assets|
| Downloaded ELF matches production |PASS|fresh-install-validation.json; full independent SHA256|
| Full local exact runtime identity |PASS|OCI blob/rootfs/env +archive SHA; original archive preserved|
| Public full OCI SDK retrieval |BLOCKED|full SDK redistribution permission not established; no registry/archive upload|
| Exact official model download |BLOCKED|official pinned LFS hashes differ from frozen shards|
| Portable CPU deployment |PASS|fresh remote-tag clone/offline install/native imports/unit generation/tests|
| Second-host GPU/boot acceptance |NOT YET VERIFIED|no second host; production not disturbed|
| Cleanup with recovery/history preserved |PASS|cleanup-results.json; verified archived sources/logs|

Previous accepted2048-token Adaptive ON workload measured25.3 Decode tok/s; it is one workload plus bounded follow-ups,
not a guarantee of every-prompt rate/endurance or real128K-prompt acceptance on this FastFix ELF. Direct PLE I/O remains.
No new throughput result is invented and no separate source build is claimed byte-identical/qualified.
Public ELF/source packaging is published, but **fully public from-zero runtime/model reproduction is not complete**.
Future development must happen outside the live frozen FastFix directory. RC1 remains archived/deprecated/disabled.
