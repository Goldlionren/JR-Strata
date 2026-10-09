# Troubleshooting

- Hash mismatch: stop installation, preserve the unexpected file; never rebuild/substitute to pass the check.
- Same-named model fails hashes: see the documented public-origin mismatch. Acquire exact licensed backup assets;
  do not alter the production manifest or quantization.
- Missing Docker/permissions/DRM: arrange host prerequisites through the operator; installer changes no policies.
- Port occupied/GPU memory insufficient: leave unrelated services alone and resolve scheduling explicitly.
- Multiple B60s: pass --gpu-pci using sysfs/lspci identity; never assume LevelZero index across environments.
- Kernel diagnostics unreadable: operator must provide existing read-only journal access; do not bypass it with broad sudo.
- Unsafe teardown, Ring/A-plan timeout, mirror hole, GPU fault/reset or corrupt output: stop workload, preserve logs and
  kernel journal, assess hardware before restart. Safety markers block automatic restart. Do not restore RC1 automatically.
- No automatic startup: inspect user linger, Docker system-service boot availability, DRM permissions and user-manager
  logs. A user service cannot order a system Docker unit; host policy must ensure readiness. Do not enable lingering
  implicitly or run a reboot test against the production host during release packaging.
- Monitor VRAM/util missing: N/A is expected without trustworthy device-specific permission/accounting. API/Chat remain
  native Strata; no replacement telemetry/UI is installed.
- New source ELF differs: use the published prebuilt artifact for the qualified deployment. Build equivalence and
  second-host inference are separate acceptance tasks.
