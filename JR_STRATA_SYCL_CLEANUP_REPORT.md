# Completed focused cleanup

Executed after remote tag/source/ELF publication and download verification,local exact runtime/model dependency verification,
and complete source/log/history recovery archives. Production release/API remained running. Full public SDK availability
is separately BLOCKED; deletion did not remove its original archive or any dependency required for licensed recovery.

| Removed exact path | Allocated bytes removed | Method |
|---|---:|---|
|/data/strata-lab/JR-Strata-SYCL-v0.1.41|331329536|git worktree remove (no force)|
|/data/strata-lab/JR-Strata-SYCL-PLEFix|844890112|git worktree remove (no force)|
|/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/dist/failed-window-01|58667008|exact archived failed-artifact directory|
|/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/dist/failed-p0-window-01|58720256|exact archived failed-artifact directory|
|/data/strata-lab/JR-Strata-SYCL-v0139-FastFix/dist/aplan-control-window-01|58744832|exact archived failed-artifact directory|
|/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/local install check|355491840|CPU scratch only; state/hash report retained|
|/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/clean-install-check/installed|355647488|CPU scratch only; state/hash report retained|
|/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/artifacts/runtime.tar.zst.part00|943722496|unpublished duplicate split staging copy; original verified archive retained|
|/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/artifacts/runtime.tar.zst.part01|943722496|unpublished duplicate split staging copy; original verified archive retained|
|/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/artifacts/runtime.tar.zst.part02|943722496|unpublished duplicate split staging copy; original verified archive retained|
|/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/artifacts/runtime.tar.zst.part03|682364928|unpublished duplicate split staging copy; original verified archive retained|

Gross allocated bytes removed:5577023488; kept recovery archive allocation:120315904.
**Net artifact disk recovery:5456707584 bytes = 5.082GiB**.
This is removed-path allocation minus retained recovery archives,not a misleading whole-filesystem df delta from unrelated activity.

v0.1.41 and PLEFix were clean tracked worktrees,removed using **git worktree remove without force**. Their source and raw
logs/evidence were archived and every included file rehashed before removal. Disposable generated build caches were omitted;
branches/objects retained in the RC1 common Git repository,plus a verified full common-Git archive because that repository
is shallow. Three failed FastFix ELF snapshots were separately archived/hashed before exact-directory removal.
CPU-only install scratch state/hash/config reports are retained. Unpublished SDK split staging duplicates were removed
only after verifying the unchanged original whole archive59f17cd2…; original image and archive stay intact.

## Classification and retained dependencies

- **PRODUCTION REQUIRED —keep:** live FastFix checkout/current dist ELF/build-fastfix frozen tests/launcher/logs;
  original Strata Pythonvenv,ranking,GGMLcache,commonGit and known untracked backups; shared data/models/packs/MTP;
  installed FastFix unit and all running Docker layers. No frozen source/config/unit/runtime modification.
- **RELEASE / RECOVERY REQUIRED —keep:** current release/source/prebuilt/public artifacts/manifests; original20261006
  complete release and OCI archive; RC1 checkout/commonGit/dist/binary/config/unit retained INACTIVE/DISABLED;
  Strata-before-frozen-restore historical sourcebackup; verified recovery-archives under the production release root.
- **OBSOLETE EXPERIMENT —removed:** two unused experimental worktrees,the three failed/control ELFcopies,CPU install
  venv scratch and unpublished duplicate SDK staging parts listed above.
- **UNRELATED PROJECT —untouched:** JR-Strata-Vulkan and its builds/releases/zips; GB10,ComfyUI,other Intel services;
  music/Hindsight units/containers/images/volumes. Strata-broken-full uses vulkan-dev and was left untouched.
  Unclassified strata-broken historical backup retained conservatively; no parent-directory deletion.

No Git branch deletion,model deletion,volume/image pruning,container termination,systemd-unit deletion or broad pkill.
Inventory found no stale SYCL test container/unit requiring deletion; current FastFix and unrelated containers remain.
RC1 startup stays disabled; no automatic recovery to RC1. Existing Linger/Docker/FastFix enabled policy was not changed.

[Before inventory](docs/jr-production-freeze-evidence/cleanup-inventory-before.json),
[exact removals/classifications](docs/jr-production-freeze-evidence/cleanup-results.json),
[SHA256 recovery archives](docs/jr-production-freeze-evidence/recovery-archive-manifest.json).
Archive location:/data/strata-lab/releases/jr-b60-sycl-fastfix-prod-20261009/recovery-archives.
Future development requires a separate explicitly requested worktree; this task adds no experimentation/autostart framework.
