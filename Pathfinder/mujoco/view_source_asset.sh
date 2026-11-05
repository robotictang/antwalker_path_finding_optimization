#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export DISPLAY="${DISPLAY:-:1}"
exec python3 preview_source_asset.py "$@"
