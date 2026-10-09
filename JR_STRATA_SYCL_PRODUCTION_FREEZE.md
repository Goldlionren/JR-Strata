# Production freeze —2026-10-09

Frozen release tag:jr-b60-sycl-fastfix-prod-20261009. Source identity is recorded by the annotated tag; packaging commits
are separate from engine sourcebe3105e7f66ef4f9668ef129a1938800954b1b3b, treedcb458f77d3f8370b72ab42cadc94ec41aa1e119.
The live deployment checkout remains0953f6eff9b288d84fea1b1e74905707ffa9ffaf and was not edited/switched/rebuilt/restarted.

Engine8d2ac886f3b8deb18b1bddb5925992317a02564d0a213aa0ad228328721ef04e; captured serverPID1749394,
enginePID1749505, container732842edcb139eae050ecb46e9538190ac4440ef682e635efb4bdbec76e849c6.
Systemd FastFix active/enabled, RC1 inactive/disabled. Endpoint127.0.0.1:18083. No new GPU inference test is required
or executed during freeze. Read-only status/metrics/models/UI and final identities are verified as release evidence.

Complete command, non-secret environment, exact installed launcher/unit, kernel/GPU identity, Docker image digests,
loaded-library hashes, model/pack/MTP/ranking hashes and Python/build dependencies are in `deployment/manifests/`.
Verified model assets total78,338,402,960 bytes, hashed once at idle CPU/I/O priority with stable file fingerprints.
Production libraries/runtime are unchanged. No automatic image/dependency upgrade or runtime switch is installed.

OCI index989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44; amd64manifestcdafd5ce1975e0449f51608d77fcd4bd7bda03374b1aed744c273d932d08f5fe;
configff4cac32a0d7642362f0efba05b4fb9ff27776ce63459924382c43b78807cb39. Complete archive59f17cd2686b419c3590f82cfb4df5630b74a47a55a01d6184ad9e278add96de.
Archive blobs/rootfs/base environment match the running image; credential/model-payload scan reviewed49855 paths. A zero-byte `.ssh/.wh..wh..opq` is a layer whiteout, not a credential. No runtime was rebuilt.

Qualification limits:25.3tok/s is one accepted2048-token generation plus bounded short follow-ups. It does not prove
long-term endurance, second-host compatibility or actual128K-prompt support for this ELF. PLE I/O and system swap
activity remain documented. The separate source-build path is not executed or claimed binary-identical.

Future development must use a separate branch/directory. Original/Vulkan/GB10/other Intel services/ComfyUI are protected.
Keep live dependencies and disabled recovery assets. See the final cleanup report for actual removals after remote release
and dependency verification. Do not restart RC1 as an automatic fallback.

Local packaging checks:9/9 PASS; original focused CPU numerical/lifecycle/state tests PASS. Isolated offline install imports native frontend/Intel server/tokenizer, generated systemd syntax PASS, native CPU mock routes PASS and SIGTERM exits0. No GPU test/production restart. Full SDK public upload remains BLOCKED; see runtime distribution status.
