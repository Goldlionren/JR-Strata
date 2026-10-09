# Install the frozen production runtime from zero

This is for a new compatible host. Do not execute startup commands against an already occupied production B60.
Read [host requirements](../requirements.md). No engine build or dependency upgrades are required for path A.

## A. Prebuilt production deployment

```bash
git clone https://github.com/Goldlionren/JR-Strata.git
cd JR-Strata
git checkout jr-b60-sycl-fastfix-prod-20261009
./deployment/fetch-artifacts.sh "$HOME/jr-fastfix-artifacts"
# Provide your own exact licensed original SDK archive (public redistribution is blocked).
python3 -B deployment/prepare-external-runtime.py --archive /path/to/strata-sycl-dev.tar.zst --artifact-dir "$HOME/jr-fastfix-artifacts"
python3 -B deployment/load-runtime.py --artifact-dir "$HOME/jr-fastfix-artifacts" --verify-only
```

All public downloaded artifacts are checked against the tag's committed hashes. The exact full Intel SDK archive is an external licensed prerequisite; public retrieval is BLOCKED. See RUNTIME_DISTRIBUTION_STATUS.md. `strata` is the actual frozen ELF, also
included in `prebuilt-production.tar.gz` with the offline CPython3.12 wheels and MIT license. The archive parts combine
into the exact original `strata-sycl-dev.tar.zst`, SHA25659f17cd2686b419c3590f82cfb4df5630b74a47a55a01d6184ad9e278add96de.
The loader changes only transport tag annotations, preserving all OCI blobs/digests. It loads under a distinct alias
`jr-strata-sycl-fastfix-runtime:prod-20261009`; it never overwrites `strata-sycl-dev:latest`. On classic Docker the ID
may be the pinned platform config digest instead of the OCI index; both require matching architecture, rootfs and env.

Obtain the following external assets with applicable model licenses. We do not redistribute model/derived weights:

```text
DATA/models/swift-IQ3_XXS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf
DATA/models/swift-IQ3_XXS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf
DATA/packs/swift-iq3_xxs/{dense.bin,index.txt,native_experts.txt,conversions.json,tokenizer/*}
DATA/mtp/rt/{dense.bin,dense.txt,experts.bin,draft_vocab.bin}
```

Every required file, byte count and hash is in `deployment/manifests/assets.json`. Preferred exact acquisition is an
authorized copy of the frozen assets. Source model repository is
[ukisai Swift1.5 GGUF](https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-GSQ-RCO-GGUF), original pinned revision
b22d729eae29b5796f76fb70f91aef549b9fc52c, Swift Open License1.0 as identified by upstream. IMPORTANT: its API currently
advertises LFS SHA2563bddaa…/b0b15f… rather than production d815c9…/953b8b…. Same names and sizes do not establish equality.
Public-download byte reproduction is BLOCKED pending a matching authorized origin; do not call it verified or adjust
expected hashes. A newly downloaded model must pass the full hash check before installation/startup.

If rebuilding derived assets from exact accepted GGUFs is necessary, extract `ggml-source-3cf03257.tar.gz`, use the pinned
Python environment and original tools. On a new host only:

```bash
export STRATA_GGUF_PY=/path/to/extracted/ggml-source/gguf-py
python tools/iq_pack.py --gguf "$DATA/models/swift-IQ3_XXS/Swift-Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf" --out "$DATA/packs/swift-iq3_xxs"
python tools/mtp_fetch.py fetch --out "$DATA/mtp"
python tools/mtp_fetch.py verify --out "$DATA/mtp"
python tools/mtp_pack.py --src "$DATA/mtp" --experts q2_0 --out "$DATA/mtp/mtp-q2_0.gguf"
python tools/mtp_rt.py --gguf "$DATA/mtp/mtp-q2_0.gguf" --out "$DATA/mtp/rt"
cp data/draft_vocab.bin "$DATA/mtp/rt/draft_vocab.bin"
```

MTP source pin is Qwen/Qwen3.8-Flash-Next revisionde4b8e4d43b917e7706784d8bb445c9af86a3540. Do not accept a fallback to
new main without matching final hashes. Acquisition/conversion requires network and enough temporary disk; regenerated
assets are not qualified until all final hashes match. Copying the exact pack/MTP backup avoids conversion entirely.

```bash
export DATA=/path/to/verified/data
(cd "$DATA" && sha256sum -c /path/to/JR-Strata/deployment/manifests/assets.sha256)
./deployment/install.sh --data-dir "$DATA" --artifact-dir "$HOME/jr-fastfix-artifacts"   --install-dir "$HOME/.local/share/jr-strata-sycl" --port 18083 --dry-run
# Add --gpu-pci BDF only when autodetection is ambiguous; do not copy the original host's BDF.
python3 -B deployment/load-runtime.py --artifact-dir "$HOME/jr-fastfix-artifacts"
./deployment/install.sh --data-dir "$DATA" --artifact-dir "$HOME/jr-fastfix-artifacts"   --install-dir "$HOME/.local/share/jr-strata-sycl" --port 18083
./deployment/verify.sh --install-dir "$HOME/.local/share/jr-strata-sycl"
```

Install creates its own frozen offline venv, copies the original native frontend, binds127.0.0.1, and registers only a
user unit. It does not start or enable it. Confirm GPU/resource availability and host startup prerequisites, then:

```bash
systemctl --user enable --now jr-strata-sycl-fastfix.service
./deployment/healthcheck.sh 18083
systemctl --user status jr-strata-sycl-fastfix.service --no-pager
```

On that new host, final hardware acceptance must check READY log for10831GPU/13745mirror, Adaptive4/96, MTP4, context131072,
INT8/32768 resident and >=512MiB headroom; run one short English/Chinese/Python/math check, then a bounded2048-token valid
response with >=20tok/s sustained Decode and no corruption/readiness errors/faults; verify SIGTERM→QUIT→queue drain and
fresh startup. Stop on fault/unsafe teardown, preserve journal/logs, assess hardware before restart. This is NOT YET
VERIFIED on a second host and was not rerun during the production freeze.

## B. Separate reproducible source build

Checkout the same release tag and use the bundled ggml source pin3cf03257f219afbe7334045ff7c6a06ac68c627d. Install the
Intel DPC++ compiler2026.1.1 (2026.1.1.20260724) separately through Intel's official distribution; do not replace the
frozen Docker runtime2026.1.0. Compare its icpx SHA against `manifests/build-dependencies.json`. Do not silently use the
image's2026.1.0 compiler. AVX2 CPU specialization is host dependent; original CPU/flags are recorded in the build manifest.

```bash
tar -xzf "$HOME/jr-fastfix-artifacts/ggml-source-3cf03257.tar.gz" -C /path/to/dependencies
./deployment/build-source.sh /opt/intel/oneapi/compiler/2026.1 /path/to/dependencies/ggml-source /path/to/new-build
# CPU-only numerical/lifecycle tests, not production GPU benchmarks:
bash tools/fastfix/cpu-tests.sh
python3 -B deployment/test_packaging.py
```

Build uses bmg-g21 AOT, precise FP, subgroup32, frozen CMake/ggml source, read-only compiler mounts and -j2. Build output
is a new ELF and SHA, separately labeled; it is NOT automatically byte-identical, production-qualified, or a replacement
for the published ELF. Full source rebuilding was not performed during this freeze. Intel toolchain acquisition remains
an external build-only prerequisite; path A carries the complete runtime and needs no compiler installation.
