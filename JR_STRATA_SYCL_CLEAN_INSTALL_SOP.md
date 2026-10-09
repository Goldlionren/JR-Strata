# Clean-install validation and operator SOP

Follow [INSTALL_FROM_ZERO](deployment/docs/INSTALL_FROM_ZERO.md) and [host requirements](deployment/requirements.md).
Preferred path uses the exact prebuilt ELF/runtime/wheels and has no source compilation dependency.
The kit contains complete launch/config/service/frontend files and explicit hashes for every external asset.

Validation during freeze:CPU packaging tests and original focused CPU correctness/lifecycle tests; after publication,
fresh clone of the remote tag, remote artifact downloads/checksums, runtime archive verification, script syntax checks,
full external-asset hashes reused with unchanged physical file fingerprints, generated-config/service dry-run and isolated
--no-systemd installation. It must not use original development worktrees, Python environment or GGML cache.
Actual completed statuses will be added to the final handover after execution; pending steps are not PASS.

Second-host full GPU startup/inference/shutdown and actual boot sequencing:NOT YET VERIFIED. No second B60 host is
available; current production is not interrupted to simulate one. Existing host user linger=yes,Docker active/enabled,
FastFix enabled/default.target; no reboot is performed. Exact public model download reproduction is BLOCKED because
upstream advertised hashes differ. A compatible host with authorized exact assets can follow the documented install
and final hardware acceptance commands.

Exact full SDK public retrieval:BLOCKED. Isolated validation can reuse the locally preserved original archive, but does not claim it was downloaded from the Release. Public ELF/prebuilt/ggml downloads and original archive checks are separate evidence.
