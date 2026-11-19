#!/usr/bin/env bash
set -euo pipefail

# Resolve paths relative to this script, even when called from another directory.
cd -- "$(dirname -- "$0")"
exec python3 myplayer.py "$@"
