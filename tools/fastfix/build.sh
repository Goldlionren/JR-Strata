#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
image=sha256:989ceb3fe23df8c42d5fc37a1c8f2bfda668cb2f3b9fc1bcd14c76e9951d5d44
compiler=/opt/intel/oneapi/compiler/2026.1
cache=/data/strata-lab/Strata/build-sycl-aot/_deps/strata_llamacpp-src
# CPU-only compilation: no GPU device mapping. Use the historical binary's 2026.1.1 compiler;
# the preserved image still supplies MKL/Level Zero/build dependencies. Run with stock image later.
docker run --rm --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD,dst=$PWD" \
  --mount "type=bind,src=$compiler,dst=$compiler,readonly" \
  --mount "type=bind,src=$cache,dst=$cache,readonly" \
  --workdir "$PWD" --entrypoint /bin/bash "$image" -c '
  set -euo pipefail
  /opt/intel/oneapi/compiler/2026.1/bin/icpx --version
  cmake -S sycl -B build-fastfix -G Ninja \
    -DCMAKE_C_COMPILER=/opt/intel/oneapi/compiler/2026.1/bin/icx \
    -DCMAKE_CXX_COMPILER=/opt/intel/oneapi/compiler/2026.1/bin/icpx \
    -DSTRATA_SYCL_AOT=bmg-g21 -DSTRATA_GGML_DIR=/data/strata-lab/Strata/build-sycl-aot/_deps/strata_llamacpp-src
  cmake --build build-fastfix -j2 --target strata fastfix_handoff fastfix_memory_safety fastfix_ple_staging kv_q8_parity kv_stream_parity iq_multi_parity native_grouped_parity quantize_act_parity ple_parity
  '
sha256sum build-fastfix/strata
