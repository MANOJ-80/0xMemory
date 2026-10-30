import json
import os
import subprocess
import sys


def test_codex_usage_adapter_sums_and_preserves_turn_usage(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    codex = fake_bin / "codex"
    codex.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "if '--version' in sys.argv:\n"
        "    print('codex-test 1.0')\n"
        "else:\n"
        "    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'cached_input_tokens':4,'output_tokens':2}}))\n"
        "    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':8,'cached_input_tokens':1,'output_tokens':3,'reasoning_output_tokens':2}}))\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    repo = tmp_path / "repo"
    repo.mkdir()
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Do the task", encoding="utf-8")
    usage_file = tmp_path / "usage.json"
    adapter = (
        __import__("pathlib").Path(__file__).parents[1]
        / "evaluation" / "product-benchmark" / "codex_usage_adapter.py"
    )
    env = dict(os.environ, PATH=f"{fake_bin}:{os.environ['PATH']}")
    result = subprocess.run(
        [sys.executable, str(adapter), "--repo", str(repo), "--prompt-file",
         str(prompt_file), "--usage-file", str(usage_file), "--model", "pinned-model"],
        capture_output=True, text=True, env=env, check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(usage_file.read_text(encoding="utf-8"))
    assert report["granularity"] == "agent_turn"
    assert report["turns_completed"] == report["turns_with_usage"] == 2
    assert report["totals"] == {
        "input_tokens": 18,
        "cached_input_tokens": 5,
        "cache_write_input_tokens": None,
        "output_tokens": 5,
        "reasoning_output_tokens": 2,
    }

