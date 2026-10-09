# GitHub production release — remote verified

Repository:[Goldlionren/JR-Strata](https://github.com/Goldlionren/JR-Strata). [Production Release](https://github.com/Goldlionren/JR-Strata/releases/tag/jr-b60-sycl-fastfix-prod-20261009), published,not draft.
Annotated tagjr-b60-sycl-fastfix-prod-20261009 points to **06bb157c26c6cb7ce96a275a5f815a40bb4209a5**, tag object453c5a20b6501a7108a60d6dcb07d6037895f681.
Engine sourcebe3105e7f66ef4f9668ef129a1938800954b1b3b, original deployment0953f6eff9b288d84fea1b1e74905707ffa9ffaf.

Remote tag/production branch/main are verified with git ls-remote and fresh clone. A standard merge retains old main
history; release commit is reachable from main. No force push or tag overwrite. Remote vulkan-dev remainsc488226185ae1ed50e8efe2cfadce455f738f9ff;
Goldlionren/JR-Strata-Vulkan was never targeted. README on main/tag documents the correct B60 settings, qualification
limits,prebuilt/source routes and original MIT attribution. Unmodified upstream README/copyright/license are retained.

| Published artifact | Bytes | SHA256 |
|---|---:|---|
|strata|58760440|8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e|
|prebuilt-production.tar.gz|72914388|ebcac13d3687f1440af2f3dc0816bef218200633bc977df8b71eef90746e1334|
|ggml-source-3cf03257.tar.gz|3568955|685a58c7097daaf7055bdd2f5827447a1e969cda1fb4e1d509d68eb19c5ecaa5|

SHA256SUMS is also published; full/public artifact inventories are committed. All three payloads were downloaded from the
remote Release and rehashed, including the exact production ELF8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e. GitHub's optional asset digest field was N/A;
independent downloaded-byte SHA256 is the evidence. Fresh source clone/tag/install/scripts/manifests were actually checked.

**Full runtime synchronization remains BLOCKED.** The unchanged SDK archive's OCI index989ceb3f…/archive59f17cd2… is
verified locally but not publicly uploaded: bundled Intel Developer Tools EULA/credist does not establish permission to
redistribute the full SDK tool executables. No GHCR/retrievable image is claimed. See
[Runtime distribution status](deployment/docs/RUNTIME_DISTRIBUTION_STATUS.md), included license/credist and exact digest manifest.
Do not describe local runtime identity as remote availability. Operator-provided licensed exact archive is supported.

Model/derived weights and credentials are not uploaded. Exact assets are external; original model API advertises different
LFS hashes, so public download byte-equivalence is BLOCKED. Full hashes for all15 external files are documented. The existing
upstream control-vector file was already part of remote history; no new model weights were introduced in this release.

The immutable tag describes the packaged release; this post-publication operations report updates actual cleanup/validation
results on main without moving the tag or changing binaries/runtime. All final evidence is in docs/jr-production-freeze-evidence/.
