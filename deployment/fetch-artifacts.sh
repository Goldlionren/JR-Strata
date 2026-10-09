#!/usr/bin/env bash
set -euo pipefail
# gh authentication is unnecessary for public release assets when curl is used.
dest=${1:?Usage: fetch-artifacts.sh ARTIFACT_DIRECTORY}
mkdir -p "$dest"
base=https://github.com/Goldlionren/JR-Strata/releases/download/jr-b60-sycl-fastfix-prod-20261009
manifest="$(dirname "$0")/manifests/public-artifacts.sha256"
while read -r sha name; do
  if [[ -e "$dest/$name" ]]; then
    actual=$(sha256sum "$dest/$name"); actual=${actual%% *}
    [[ "$actual" == "$sha" ]] || { echo "Existing artifact mismatch: $name" >&2; exit 78; }
    continue
  fi
  curl --fail --location --retry 3 --connect-timeout 15 --max-time 1800 "$base/$name" --output "$dest/$name.partial"
  actual=$(sha256sum "$dest/$name.partial"); actual=${actual%% *}
  [[ "$actual" == "$sha" ]] || { echo "Checksum failed: $name" >&2; exit 78; }
  mv "$dest/$name.partial" "$dest/$name"
done < "$manifest"
printf "Public artifacts verified. Exact SDK runtime is external: supply your licensed archive using prepare-external-runtime.py.\n"
