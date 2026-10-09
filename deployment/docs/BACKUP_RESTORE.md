# Backup and recovery

Preserve the release tag, all Release artifacts and SHA256SUMS, exact licensed external assets, installed settings/runtime,
unit and logs. The OCI archive is split; keep every part and archive-parts.json. No automatic dependency upgrades.

On a clean host: clone tag, verify/download artifacts, verify external model/pack/MTP hashes, load runtime under the
release-specific alias, run installer dry-run and then install. Use the same safe graceful service lifecycle.
A portable installation is independent of development worktrees and uses its own Python environment and frontend.

To remove only this installation's service:

```bash
./deployment/uninstall.sh "$HOME/.local/share/jr-strata-sycl"
```

This gracefully stops only the named owned unit, verifies inactive, disables/removes only that unit, and retains installation,
Docker image and external assets. There is no volume/image prune or recursive model deletion. If teardown is unresolved,
uninstallation refuses to proceed. Keep archived RC1 disabled; it is a historical recovery artifact, not automatic fallback.
