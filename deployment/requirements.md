# Host requirements

The tested host is Ubuntu24.04.4 x86-64, kernel7.0.0-34-generic, Intel xe driver reported17010844, Arc Pro B60
PCI8086:e211 with24GiB physical VRAM,64GiB physical RAM. B60 firmware/xe must already be supported and healthy.
Other kernels/driver combinations require hardware acceptance; the installer does not install or upgrade them.

Use an x86-64 AVX2/FMA/BMI2/F16C capable CPU and Python3.12 with `venv`, Docker Engine, zstd, curl, git, XPU-SMI
and readable kernel journal. Original compiler was2026.1.1; container runtime2026.1.0, UR0.12.0, LevelZero1.32.0,
Intel GPU userspace26.35.39758.10-0. The container is Ubuntu26.04; it carries its own userspace and does not downgrade
host oneAPI. Image architecture linux/amd64. The full package/library SHA inventory is under `manifests/`.

Need at least22GiB unloaded free B60 memory and32GiB host MemAvailable at startup; after load require at least512MiB
free VRAM. These are independent checks. Observed GPU expert cache17990MiB (10831 experts), complete host mirror22.40GiB
(13745 experts), resident INT8 KV32768 of131072 context. Host KV allocation and other pinned allocations need additional
RAM. The accepted2048-token run had minimum MemAvailable30.699GiB and peak DRM VRAM23.374GiB/GTT24.574GiB; GTT/RSS
are overlapping accounts, not additive physical RAM. Page-cache/PLE I/O and system swap activity are not eliminated.

Provide at least100GB data disk for exact model/pack/MTP assets (78,338,402,960 bytes verified), plus at least15GB for
runtime extraction, Release downloads, source and Python environment. A source build needs additional compiler/build space.
Use NVMe where practical. Do not allocate a26.82GiB all-RAM PLE table in this deployment.

User must have existing Docker permission and read/write access to the selected B60 card/render nodes. User-systemd
must work; for reboot startup without login, an administrator must explicitly arrange linger and ensure Docker.service
is enabled/available after boot. `loginctl show-user "$USER" -p Linger`, `systemctl is-enabled docker` and
`systemctl --user is-enabled jr-strata-sycl-fastfix.service` inspect prerequisites. The kit does not change host policy,
Docker groups, journal groups, drivers, firmware, sudoers or AppArmor. Docker access itself is privileged: arrange it
through the machine's normal administrative procedure, not a broad rule added by this kit.

A user manager cannot order itself against a system Docker unit. Ensure Docker and /dev/dri are ready before the user
service; startup refuses a missing daemon/device with bounded retries. For machines with a late Docker startup, the
operator must establish host-level ordering. No Docker restart policy is used; systemd is the sole supervisor.

The installer autodetects a single B60 or requires `--gpu-pci` when several exist, maps only its card/render nodes,
and uses LevelZero0 inside that restricted container. Runtime readiness verifies the B60 name, actual residency,
context/MTP and running ELF. Multiple-device configurations are not independently GPU-tested.
