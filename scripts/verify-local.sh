#!/usr/bin/env bash
# Ubuntu/Linux verification. Run with bash; activation is not required.
set -euo pipefail

skip_install=false
offline_models=false
for argument in "$@"; do
    case "$argument" in
        --skip-install) skip_install=true ;;
        --offline-models) offline_models=true ;;
        --help|-h)
            printf '%s\n' 'Usage: bash scripts/verify-local.sh [--skip-install] [--offline-models]' \
                'Creates .venv with PYTHON_BIN (default python3) if absent.' \
                'Use Python 3.11 or 3.12; cache model weights before offline mode.'
            exit 0 ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; exit 2 ;;
    esac
done

engine_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$engine_root"
python_path="$engine_root/.venv/bin/python"
command -v git >/dev/null || { printf 'Install Git first.\n' >&2; exit 1; }
if [[ ! -x "$python_path" ]]; then
    if "$skip_install"; then
        printf 'No Linux .venv/bin/python. Create and install the environment first.\n' >&2
        exit 1
    fi
    if [[ -e "$engine_root/.venv" ]]; then
        printf 'Existing .venv is not a usable Linux environment; use a fresh clone.\n' >&2
        exit 1
    fi
    bootstrap_python="${PYTHON_BIN:-python3}"
    "$bootstrap_python" -c 'import sys; assert sys.version_info[:2] in [(3,11),(3,12)], "Use Python 3.11 or 3.12 for this verification workflow"'
    "$bootstrap_python" -m venv .venv
fi
export PYTHONUTF8=1
if "$offline_models"; then
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
fi
if ! "$skip_install"; then
    "$python_path" -m pip install -e '.[dev]'
fi
"$python_path" -m pip check
"$python_path" -m oxmemory --help
run_dir="$(mktemp -d "$engine_root/.venv/verification.XXXXXX")"
"$python_path" scripts/smoke_memory_system.py --output "$run_dir/memory-system-smoke.json"
"$python_path" -m pytest tests/ -v --basetemp "$run_dir/pytest"
"$python_path" -m oxmemory.demo --output "$run_dir/demo-result.json"
"$python_path" -m oxmemory.evaluation --semantic --output "$run_dir/evaluation-semantic.json"
printf 'PASS: dependencies, architecture smoke, CLI, all tests, MCP, embeddings, and semantic evaluation.\n'
printf 'Verification artifacts: %s\n' "$run_dir"
