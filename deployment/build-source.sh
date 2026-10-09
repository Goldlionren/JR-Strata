#!/usr/bin/env bash
set -euo pipefail
# Separately labeled source build; never replace bin/strata or production image.
[[ $# == 3 ]] || { echo "Usage: build-source.sh COMPILER_2026.1.1_ROOT EXTRACTED_GGML_ROOT NEW_BUILD_DIRECTORY" >&2; exit 2; }
compiler=$(realpath "$1"); ggml=$(realpath "$2"); build=$(realpath -m "$3")
source_root=$(realpath "$(dirname "$0")/..")
[[ ! -e "$build" ]] || { echo "Build directory must be new" >&2; exit 78; }
"$compiler/bin/icpx" --version | head -1 | grep -F '2026.1.1' >/dev/null
expected=be7fa7c3c74c2ba2b8e1b50b0a61e37986441727899e25f3545636bde157c083
actual=$(sha256sum "$compiler/bin/icpx"); actual=${actual%% *}
[[ "$actual" == "$expected" ]] || { echo "Compiler hash mismatch" >&2; exit 78; }
mkdir -p "$build"
image=jr-strata-sycl-fastfix-runtime:prod-20261009
# No /dev/dri, no GPU execution, no package downloads; compiler/source mounts read-only.
docker run --rm --restart no -v "$source_root:/source:ro" -v "$compiler:/compiler:ro" -v "$ggml:/ggml:ro" -v "$build:/build" "$image" \
 'set -e; cmake -S /source/sycl -B /build -G Ninja -DCMAKE_C_COMPILER=/compiler/bin/icx -DCMAKE_CXX_COMPILER=/compiler/bin/icpx -DSTRATA_SYCL_AOT=bmg-g21 -DSTRATA_GGML_DIR=/ggml; cmake --build /build -j2 --target strata'
sha256sum "$build/strata"
printf 'New source build; not automatically byte-identical or production-verified. Frozen ELF remains unchanged.\n'
