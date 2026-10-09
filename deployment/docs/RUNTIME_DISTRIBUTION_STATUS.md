# Exact runtime distribution status

Local exact full OCI archive is verified:59f17cd2686b419c3590f82cfb4df5630b74a47a55a01d6184ad9e278add96de;
index989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44. It is preserved unchanged in the original release.
It includes a complete Intel SDK, not only runtime libraries. The bundled Developer Tools EULA grants distribution of
listed Redistributables as part of the product; its compiler credist list does not list compiler executable tools.
The original image also contains other SDK tools. See bundled license/credist evidence under docs/licenses.

Public redistribution permission for the entire unchanged SDK archive has not been established. Its public upload is
BLOCKED; no OCI registry/image is claimed published. A runtime-only reconstructed image would have a different identity
and would require separate validation, so no replacement/rebuild is performed during this freeze.

An operator entitled to use the original environment can retain/copy their licensed archive for their own recovery;
the release records exact digests and supplies `prepare-external-runtime.py` plus a transport-only distinct-tag loader.
It does not claim this gives a public redistribution right. Do not put SDK parts on a public endpoint without established
permission. Public ELF/prebuilt Python wheels/ggml source are published separately with their notices.

This limitation prevents mandatory remote-runtime retrievability from passing. Clean installation is reproducible from
published source/ELF plus authorized exact external runtime/model assets; a fully public from-zero download is BLOCKED.
Production itself is frozen/healthy and no live libraries or image layers have been changed.
