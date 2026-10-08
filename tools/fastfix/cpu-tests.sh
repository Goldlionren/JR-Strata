#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p build-fastfix-cpu logs/fastfix
out=$(mktemp -d "$PWD/logs/fastfix/cpu-XXXXXX")
common=(src/kernels/ngram.cpp sycl/src/ngram/ple_reader.cpp sycl/src/platform/direct_file.cpp)
c++ -O2 -std=c++20 -pthread -Iinclude src/ngram/ple_reader_test.cpp "${common[@]}" -o build-fastfix-cpu/ple_reader_test
c++ -O2 -std=c++20 -pthread -Iinclude tools/fastfix/ple_staging.cpp "${common[@]}" -o build-fastfix-cpu/ple_staging
build-fastfix-cpu/ple_reader_test --selftest --dir "$out" > "$out/reader.log" 2>&1
build-fastfix-cpu/ple_staging "$out/staging.gguf" > "$out/staging.log" 2>&1
c++ -std=c++20 -Iinclude tools/fastfix/output_test.cpp -o build-fastfix-cpu/output_test
build-fastfix-cpu/output_test > "$out/output.log"
c++ -std=c++20 -Wall -Wextra -Werror -Iinclude tools/fastfix/lifecycle_test.cpp -o build-fastfix-cpu/lifecycle_test
build-fastfix-cpu/lifecycle_test > "$out/lifecycle.log"
python3 -B tools/fastfix/source_order_test.py > "$out/source-order.log"
cat "$out/reader.log" "$out/staging.log" "$out/output.log" "$out/source-order.log" "$out/lifecycle.log"
printf 'Evidence: %s\n' "$out"
