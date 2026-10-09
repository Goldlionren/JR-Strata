# GitHub production release

Target repository:https://github.com/Goldlionren/JR-Strata (public,original MIT attribution retained).
Release URL:https://github.com/Goldlionren/JR-Strata/releases/tag/jr-b60-sycl-fastfix-prod-20261009.
The immutable annotated tag records the packaging commit; its ancestry includes the exact engine source and deployment
commit listed in production-lock.json. No force push, unrelated branch rewrite or Vulkan-repository publication.

Release artifacts:exact production ELF `strata`, prebuilt-production.tar.gz (same ELF/offline Python wheels),
ggml-source-3cf03257.tar.gz, SHA256SUMS. Runtime part hashes are recorded for the separately supplied licensed archive. Checksums are committed under deployment/manifests.
Full SDK public redistribution / remote runtime retrieval is BLOCKED; see deployment/docs/RUNTIME_DISTRIBUTION_STATUS.md. No GHCR image publication is claimed.
No model weights, derived pack/MTP weights or credentials are included. Required external asset hashes and known public
origin mismatch are documented explicitly.

Publication verification will be recorded in the post-release handover/evidence: remote main/tag/reachability, release
and assets, independently downloaded ELF/archive hashes, fresh clone and install dry-run/CPU validation. A local tag alone
is not synchronization success. See JR_STRATA_SYCL_CLEAN_INSTALL_SOP.md for actual validation status.
