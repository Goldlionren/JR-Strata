# Cleanup report

Cleanup is deferred until remote production release artifacts and portable dependencies are independently verified.
Production-required:live FastFix checkout,its dist ELF/build-fastfix frozen validation binaries,installed unit/launcher,
original Strata Python venv/ranking/GGML cache/common Git repository,shared model/pack/MTP and any live Docker layers.
Release/recovery-required:immutable production release and original20261006 backup; RC1 disabled recovery snapshot.
Obsolete candidates:unreferenced v0.1.41/PLEFix worktrees,failed/stale SYCL builds/test artifacts,subject to Git common-dir,
mount/unit/reference review and archival of dirty files/history/evidence first.
Unrelated projects:Vulkan,GB10,other Intel inference,ComfyUI,unrelated containers/images/volumes;never touch.

No cleanup is claimed completed in this immutable initial document. The final post-release operations report will record
actual removals,archives,retained dependencies and measured disk recovery. No broad Docker prune,parent-directory deletion,
force-kill or indiscriminate branch removal is permitted. Production remains uninterrupted and frozen.
