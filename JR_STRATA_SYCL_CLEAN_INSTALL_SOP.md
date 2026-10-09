# Clean install — actual verification and handover

[Exact instructions](deployment/docs/INSTALL_FROM_ZERO.md), [requirements](deployment/requirements.md),
[operations](deployment/docs/OPERATIONS.md), [recovery](deployment/docs/BACKUP_RESTORE.md).

## New compatible host: preferred prebuilt path

```bash
git clone https://github.com/Goldlionren/JR-Strata.git
cd JR-Strata
git checkout jr-b60-sycl-fastfix-prod-20261009
./deployment/fetch-artifacts.sh "$HOME/jr-fastfix-artifacts"
# External prerequisites: exact licensed SDK archive and exact model/pack/MTP data.
python3 -B deployment/prepare-external-runtime.py --archive /path/to/strata-sycl-dev.tar.zst --artifact-dir "$HOME/jr-fastfix-artifacts"
python3 -B deployment/load-runtime.py --artifact-dir "$HOME/jr-fastfix-artifacts" --verify-only
export DATA=/path/to/verified/data
./deployment/install.sh --data-dir "$DATA" --artifact-dir "$HOME/jr-fastfix-artifacts" --dry-run
python3 -B deployment/load-runtime.py --artifact-dir "$HOME/jr-fastfix-artifacts"
./deployment/install.sh --data-dir "$DATA" --artifact-dir "$HOME/jr-fastfix-artifacts"
./deployment/verify.sh --install-dir "$HOME/.local/share/jr-strata-sycl"
# On this new host only, after GPU/host resources and boot prerequisites are confirmed:
systemctl --user enable --now jr-strata-sycl-fastfix.service
./deployment/healthcheck.sh 18083
```

Data/install paths,port,B60 PCI selection and user-unit name are configurable. BDF/username are not hardcoded in general
installer/startup. Dry-run installs/starts/enables/loads nothing. Existing conflicting installation/unit/alias is refused.
No system packages,drivers,policy changes or broad privilege rules. User must explicitly arrange Docker permission,
readable journal,DRM access,linger and system Docker boot availability. No dual Docker/systemd restart policy.
The prebuilt route requires no C++ compiler/rebuild. Separate source build pins2026.1.1 and ggml3cf03257; it is not run
or declared byte-identical to the production ELF. Toolchain acquisition is an external build-only prerequisite.

## Executed during this freeze

| Check | Result | Evidence / scope |
|---|---|---|
| Fresh clone of remote production tag |PASS|commit06bb157c26c6cb7ce96a275a5f815a40bb4209a5; no shared local Git object reference|
| Public remote artifacts downloaded/hashed |PASS|ELF/prebuilt/ggml; fresh-install-validation.json|
| Original whole OCI archive/parts verified |PASS locally|external retained licensed original,not public download; no Docker load|
| External model/pack/MTP hashes |PASS locally|15files/78,338,402,960B full SHA once; same physical files rechecked inode/size/mtime|
| CPU correctness/lifecycle regressions |PASS|independent PLE reference90windows,T1/4/6,11lifecycle cases,16A-plan,16mirror,6payload +source guards|
| Portable packaging tests |PASS|9/9 on local and fresh remote tag|
| Isolated offline prebuilt install |PASS|own CPython3.12 venv/wheels;--no-systemd; no C++ build|
| Native server/Intel frontend/tokenizer imports |PASS|new install app/venv,independent original development paths|
| Native Chat/Monitor/About routes |PASS CPU mock|root/status/metrics/models; SIGTERM exit0; not a GPU acceptance test|
| Generated profile/systemd syntax |PASS|spaces/port/device paths,fixed settings,systemd-analyze --user verify; synthetic user default-target boot dependency check exit0|
| Installation file/checksum verification |PASS|installed-files inventory and frozen ELF|
| Full public SDK/model acquisition |BLOCKED|redistribution/origin limitations documented; no silent substitution|
| Fresh source rebuild |NOT EXECUTED|separate optional path with pinned flags/compiler|
| Second-host inference/boot lifecycle |NOT YET VERIFIED|no second B60 host available|

Validation scratch venvs/staged duplicate SDK parts were removed after evidence retention. Remote clone/public artifacts
remain under releases/jr-b60-sycl-fastfix-prod-20261009/clean-install-check. Current production PID/config remained intact.

For final hardware acceptance on another compatible host, run the documented short English/Chinese/Python/math checks,
a bounded2048-token valid response with Adaptive ON/MTP4 and >=20tok/s sustained Decode, confirm10831GPU/13745mirror,
loaded headroom>=512MiB,no faults/corruption,graceful Server QUIT/drain and fresh startup. Stop/assess on serious faults.
No such additional GPU experiment was performed on the working production host for packaging.

Public-download installation from literally zero assets remains BLOCKED: acquire exact licensed external runtime/model
assets first; do not assume same-named upstream GGUFs match. See all hashes and original/pinned source instructions.
