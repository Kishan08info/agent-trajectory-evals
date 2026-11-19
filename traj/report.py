"""Write run outputs: summary.json, per_task.csv, report.md, traces.jsonl."""

import csv
import json
from pathlib import Path

from .metrics import check_gates

PER_TASK_COLUMNS = [
    "task_id", "answerable", "n_steps", "n_golden_steps", "tool_precision",
    "tool_recall", "tool_f1", "step_accuracy", "sequence_similarity",
    "args_accuracy", "extra_tool_calls", "missing_tool_calls",
    "judge_groundedness", "judge_completeness", "judge_efficiency",
    "judge_total", "abstained", "answer_correct", "abstention_correct",
]


def write_outputs(out_dir, agent_name, config, trajectories, records, summary):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gates = check_gates(summary)

    with open(out_dir / "traces.jsonl", "w") as f:
        for t in trajectories:
            f.write(json.dumps(t, sort_keys=True) + "\n")

    with open(out_dir / "per_task.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PER_TASK_COLUMNS)
        w.writeheader()
        for r in records:
            w.writerow({c: r.get(c) for c in PER_TASK_COLUMNS})

    payload = {
        "agent": agent_name,
        "config": config,
        "summary": summary,
        "gates": {
            k: {"passed": bool(v[0]), "actual": v[1], "minimum": v[2]}
            for k, v in gates.items()
        },
        "all_gates_passed": all(v[0] for v in gates.values()),
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")

    lines = [
        f"# Trajectory eval report — agent `{agent_name}`",
        "",
        f"Tasks: {summary['n_tasks']} "
        f"({summary['n_answerable']} answerable, "
        f"{summary['n_unanswerable']} unanswerable). "
        f"All gates passed: **{payload['all_gates_passed']}**.",
        "",
        "## Aggregate metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| answer accuracy | {summary['answer_accuracy']} |",
        f"| abstention precision / recall / F1 | "
        f"{summary['abstention_precision']} / {summary['abstention_recall']} / "
        f"{summary['abstention_f1']} |",
        f"| mean tool precision / recall / F1 | "
        f"{summary['mean_tool_precision']} / {summary['mean_tool_recall']} / "
        f"{summary['mean_tool_f1']} |",
        f"| mean step accuracy | {summary['mean_step_accuracy']} |",
        f"| mean sequence similarity | {summary['mean_sequence_similarity']} |",
        f"| mean args accuracy | {summary['mean_args_accuracy']} |",
        f"| mean judge total (/6) | {summary['mean_judge_total']} |",
        f"| mean steps per task | {summary['mean_steps']} |",
        f"| total extra tool calls | {summary['total_extra_tool_calls']} |",
        f"| total missing tool calls | {summary['total_missing_tool_calls']} |",
        "",
        "## Gates",
        "",
        "| Gate | Actual | Minimum | Result |",
        "| --- | --- | --- | --- |",
    ]
    for metric, (passed, actual, minimum) in gates.items():
        lines.append(
            f"| {metric} | {actual} | {minimum} | "
            f"{'PASS' if passed else 'FAIL'} |"
        )
    lines += [
        "",
        "## Per-task results",
        "",
        "| Task | Steps | Tool F1 | Step acc | Args acc | Judge /6 | "
        "Answer | Abstained |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in records:
        ans = (
            "correct" if r["answer_correct"] == 1
            else ("wrong" if r["answer_correct"] == 0 else "—")
        )
        lines.append(
            f"| {r['task_id']} | {r['n_steps']}/{r['n_golden_steps']} | "
            f"{r['tool_f1']} | {r['step_accuracy']} | {r['args_accuracy']} | "
            f"{r['judge_total']} | {ans} | "
            f"{'yes' if r['abstained'] else 'no'} |"
        )
    lines.append("")
    with open(out_dir / "report.md", "w") as f:
        f.write("\n".join(lines))
    return payload


def write_comparison(out_path, baseline, current):
    """Markdown regression report: baseline summary vs current summary."""
    b, c = baseline["summary"], current["summary"]
    b_gates = baseline["gates"]
    c_gates = current["gates"]
    rows = []
    for key in [
        "answer_accuracy", "abstention_recall", "mean_tool_f1",
        "mean_step_accuracy", "mean_sequence_similarity",
        "mean_args_accuracy", "mean_judge_total", "mean_steps",
        "total_extra_tool_calls",
    ]:
        bv, cv = b.get(key), c.get(key)
        delta = (
            round(cv - bv, 4)
            if isinstance(bv, (int, float)) and isinstance(cv, (int, float))
            else "—"
        )
        rows.append((key, bv, cv, delta))
    lines = [
        "# Trajectory eval comparison",
        "",
        f"Baseline: `{baseline['agent']}` — all gates passed: "
        f"{baseline['all_gates_passed']}",
        f"Current: `{current['agent']}` — all gates passed: "
        f"{current['all_gates_passed']}",
        "",
        "## Metric deltas (current − baseline)",
        "",
        "| Metric | Baseline | Current | Delta |",
        "| --- | --- | --- | --- |",
    ]
    for key, bv, cv, delta in rows:
        lines.append(f"| {key} | {bv} | {cv} | {delta} |")
    lines += [
        "",
        "## Gate changes",
        "",
        "| Gate | Baseline | Current |",
        "| --- | --- | --- |",
    ]
    for metric in b_gates:
        bp = "PASS" if b_gates[metric]["passed"] else "FAIL"
        cp = "PASS" if c_gates[metric]["passed"] else "FAIL"
        flag = " **REGRESSION**" if bp == "PASS" and cp == "FAIL" else ""
        lines.append(f"| {metric} | {bp} | {cp}{flag} |")
    regressed = [
        m for m in b_gates
        if b_gates[m]["passed"] and not c_gates[m]["passed"]
    ]
    verdict = "FAIL — regressions vs baseline" if regressed else "PASS"
    lines += ["", f"## Verdict: **{verdict}**", ""]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    return verdict, regressed
