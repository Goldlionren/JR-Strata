# Frozen FastFix production deployment

Use [INSTALL_FROM_ZERO.md](docs/INSTALL_FROM_ZERO.md) for the prebuilt installation. No C++ compilation is required.
The portable installer generates paths, a dedicated user service and a localhost-only native Strata server. It never starts,
stops or enables a service. This packaging does not modify the live installation from which the release was frozen.

Release: `jr-b60-sycl-fastfix-prod-20261009`. Engine SHA256:
`8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`.

The exact production OCI archive is preserved as a checksum-verified external licensed dependency. OCI index:
`sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44`.
Full SDK public redistribution is BLOCKED; see docs/RUNTIME_DISTRIBUTION_STATUS.md. See `docker/runtime-manifest.json`.

Model acquisition is an explicit external dependency: current upstream LFS metadata does not match the frozen production
shards. Do not substitute a same-named model. Obtain licensed exact assets from an authorized backup and verify every
hash in `manifests/assets.sha256`. Public-download byte-equivalence and second-host GPU inference remain unverified.

Files: `install.sh`, `verify.sh`, `healthcheck.sh`, `uninstall.sh`, `fetch-artifacts.sh`, `load-runtime.py`,
`build-source.sh`, `watch.sh`; configuration, systemd and immutable artifact manifests are included. Source build is a
separate optional path, not a replacement for the production-verified prebuilt ELF.
