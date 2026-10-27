#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
engine_root="$(cd -- "$script_dir/.." && pwd)"
if [[ -n "${PYTHON_BIN:-}" ]]; then
    bootstrap="$PYTHON_BIN"
elif [[ -x "$engine_root/.venv/bin/python" ]]; then
    bootstrap="$engine_root/.venv/bin/python"
else
    bootstrap=''
    for candidate in python3.12 python3.11 python3; do
        if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info[:2] in [(3,11),(3,12)] else 1)'; then
            bootstrap="$candidate"
            break
        fi
    done
    if [[ -z "$bootstrap" ]]; then
        printf 'Install Git and Python 3.12 with its venv package, or set PYTHON_BIN to Python 3.11/3.12. See QUICKSTART_DEMO.md.\n' >&2
        exit 1
    fi
fi
exec "$bootstrap" "$script_dir/demo_setup.py" "$@"
