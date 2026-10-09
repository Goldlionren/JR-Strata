# JR-Strata-SYCL — frozen Intel Arc Pro B60 production

Production release: **jr-b60-sycl-fastfix-prod-20261009**. This is the v0.1.39-derived FastFix with the focused PLE,
queue/lifecycle, adaptive GGUF mirror and payload-lifetime repairs. The running engine is frozen byte-for-byte;
this release adds deployment packaging, not new kernels or inference settings.

| Setting | Qualified production |
|---|---|
| GPU | Intel Arc Pro B60 24GiB,8086:e211 |
| Model | Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS |
| GPU experts |10831 /17990MiB (17.57GiB)|
| Host Mirror |13745/13745 missing experts,22.40GiB|
| Adaptive / MTP |ON4/96 /Spec4|
| Context / KV |131072 configured /INT8,32768 resident|
| Prefill / VRAM reserve |4096 /768MiB|
| API / native Chat,Monitor,About |127.0.0.1:18083|
| Supervision |user-systemd, bounded restart, graceful Server QUIT /SYCL drain|

A correctness-qualified2048-token workload measured **25.3 Decode tok/s** with Adaptive ON and no GPU fault/reset.
This is one sustained workload, not a universal speed or endurance guarantee. Short-prompt rates vary.
128K capacity is configured; this FastFix binary has not independently passed a real near128K prompt acceptance.
Direct PLE disk reads remain and are not claimed eliminated.

**[Clean install: prebuilt production runtime](deployment/docs/INSTALL_FROM_ZERO.md)** ·
[Requirements](deployment/requirements.md) · [Operations](deployment/docs/OPERATIONS.md) ·
[Production freeze](JR_STRATA_SYCL_PRODUCTION_FREEZE.md) · [GitHub release](JR_STRATA_SYCL_GITHUB_RELEASE.md)

The GitHub Release supplies the exact ELF, offline Python wheels and pinned ggml source. Exact full SDK runtime is an external licensed archive, not publicly uploaded.
Model/derived weights are external and are not redistributed. The official model's currently advertised LFS hashes
differ from the frozen shards; exact licensed backup acquisition is required until this is resolved.
Second-host GPU inference and public-download model equivalence are **NOT YET VERIFIED**. Installation scripts
support configurable data/install directories, local port, target B60 selection, dry-run and user-service installation.

Engine SHA256: `8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e`.
Engine source: `be3105e7f66ef4f9668ef129a1938800954b1b3b`.
Original deployment source: `0953f6eff9b288d84fea1b1e74905707ffa9ffaf`.
Runtime: oneAPI2026.1.0 /UR0.12.0 /LevelZero1.32.0; build compiler2026.1.1.
No rebuild or benchmark was performed to create this release. RC1 is deprecated and remains archived/disabled.

Strata is originally by [Niko1221 and Strata contributors](https://github.com/Niko1221/Strata).
Original [MIT copyright/license](LICENSE), source attribution and [upstream README](README.upstream.md) are preserved.
Intel runtime licenses remain in the unchanged runtime archive; ggml licenses are included in its pinned source archive.
Model licenses are separate; review upstream terms before obtaining/redistributing weights.
