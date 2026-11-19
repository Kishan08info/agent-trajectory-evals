"""End-to-end CLI tests: run / score / compare, exit codes, reproducibility."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run_cli(*args, expect=0):
    proc = subprocess.run(
        [sys.executable, "-m", "traj", *args],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == expect, proc.stdout + proc.stderr
    return proc


def test_run_baseline_passes_and_stale_fails(tmp_path):
    out = tmp_path / "baseline"
    _run_cli("run", "--config", "configs/baseline.json", "--out-dir", str(out), expect=0)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["all_gates_passed"] is True
    assert (out / "report.md").exists()
    assert (out / "per_task.csv").exists()
    assert (out / "traces.jsonl").exists()
    assert len((out / "traces.jsonl").read_text().splitlines()) == 12

    out_stale = tmp_path / "stale"
    _run_cli("run", "--config", "configs/stale.json", "--out-dir", str(out_stale), expect=1)
    summary = json.loads((out_stale / "summary.json").read_text())
    assert summary["all_gates_passed"] is False
    assert summary["summary"]["answer_accuracy"] == 0.7


def test_score_replays_recorded_traces(tmp_path):
    run_dir = tmp_path / "run"
    _run_cli("run", "--config", "configs/baseline.json", "--out-dir", str(run_dir), expect=0)
    scored = tmp_path / "scored"
    _run_cli("score", "--traces", str(run_dir / "traces.jsonl"),
             "--out-dir", str(scored), expect=0)
    scored_summary = json.loads((scored / "summary.json").read_text())
    run_summary = json.loads((run_dir / "summary.json").read_text())
    assert scored_summary["summary"] == run_summary["summary"]


def test_compare_flags_regression_and_passes_identical(tmp_path):
    base = tmp_path / "base"
    _run_cli("run", "--config", "configs/baseline.json", "--out-dir", str(base), expect=0)
    chatty = tmp_path / "chatty"
    _run_cli("run", "--config", "configs/chatty.json", "--out-dir", str(chatty), expect=1)
    cmp_path = tmp_path / "cmp.md"
    _run_cli("compare", "--baseline", str(base / "summary.json"),
             "--current", str(chatty / "summary.json"),
             "--out", str(cmp_path), expect=1)
    assert "REGRESSION" in cmp_path.read_text()

    cmp_same = tmp_path / "cmp_same.md"
    _run_cli("compare", "--baseline", str(base / "summary.json"),
             "--current", str(base / "summary.json"),
             "--out", str(cmp_same), expect=0)
    assert "PASS" in cmp_same.read_text()


def test_from_scratch_re_run_is_identical(tmp_path):
    def run_once(name):
        out = tmp_path / name
        _run_cli("run", "--config", "configs/baseline.json",
                 "--out-dir", str(out), expect=0)
        return out

    first = run_once("first")
    second = run_once("second")
    # Summaries and per-task tables are byte-identical (no wall-clock data).
    assert (first / "summary.json").read_bytes() == (second / "summary.json").read_bytes()
    assert (first / "per_task.csv").read_bytes() == (second / "per_task.csv").read_bytes()
    # Traces differ only in latency_ms.
    def strip_latency(path):
        return [
            {k: v for k, v in json.loads(line).items() if k != "latency_ms"}
            for line in Path(path).read_text().splitlines()
        ]
    assert strip_latency(first / "traces.jsonl") == strip_latency(second / "traces.jsonl")
