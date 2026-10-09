#!/usr/bin/env bash
set -euo pipefail
port=${1:-18083}
[[ "$port" =~ ^[0-9]+$ ]] || exit 2
for endpoint in v1/models status metrics; do
  curl --fail --silent --show-error --max-time 5 "http://127.0.0.1:$port/$endpoint"
  printf '\n'
done
curl --fail --silent --show-error --max-time 5 "http://127.0.0.1:$port/" >/dev/null
