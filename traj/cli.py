"""CLI: run an agent variant over the task set, score recorded traces,
or compare two runs.

Usage:
    python -m traj run --config configs/baseline.json --out-dir outputs/run_baseline
    python -m traj score --traces outputs/run_baseline/traces.jsonl --out-dir outputs/scored
    python -m traj compare --baseline outputs/run_baseline/summary.json \\
        --current outputs/run_stale/summary.json --out outputs/comparison_stale.md

``run`` exits 0 when all gates pass, 1 when a gate fails. ``compare`` exits
0 on PASS, 1 when the current run regresses any gate the baseline passed.
"""

import argparse
import json
import sys
from pathlib import Path

from .agent import Agent
from .dataset import load_config, load_tasks
from .metrics import aggregate, check_gates, score_trajectory
from .report import write_comparison, write_outputs


def cmd_run(args):
    config = load_config(args.config)
    data_dir = Path(__file__).resolve().parent.parent / "data"
    tasks = load_tasks(data_dir)
    agent = Agent(data_dir, variant=config["agent"])
    trajectories = [agent.run(t) for t in tasks]
    records = [score_trajectory(tr, t) for tr, t in zip(trajectories, tasks)]
    summary = aggregate(records)
    payload = write_outputs(args.out_dir, config["agent"], config,
                            trajectories, records, summary)
    print(f"agent: {config['agent']}")
    print(f"tasks: {summary['n_tasks']} "
          f"({summary['n_answerable']} answerable, "
          f"{summary['n_unanswerable']} unanswerable)")
    print(f"answer accuracy: {summary['answer_accuracy']}")
    print(f"abstention recall: {summary['abstention_recall']}")
    print(f"mean tool F1: {summary['mean_tool_f1']}")
    print(f"mean step accuracy: {summary['mean_step_accuracy']}")
    print(f"mean judge total: {summary['mean_judge_total']}/6")
    print(f"total extra tool calls: {summary['total_extra_tool_calls']}")
    print(f"all gates passed: {payload['all_gates_passed']}")
    return 0 if payload["all_gates_passed"] else 1


def cmd_score(args):
    data_dir = Path(__file__).resolve().parent.parent / "data"
    tasks = {t["id"]: t for t in load_tasks(data_dir)}
    with open(args.traces) as f:
        trajectories = [json.loads(line) for line in f if line.strip()]
    records = []
    for tr in trajectories:
        task = tasks[tr["task_id"]]
        records.append(score_trajectory(tr, task))
    summary = aggregate(records)
    config = {"agent": trajectories[0].get("agent", "external") if trajectories else "external",
              "scored_from": args.traces}
    payload = write_outputs(args.out_dir, config["agent"], config,
                            trajectories, records, summary)
    print(f"scored {len(records)} traces from {args.traces}")
    print(f"answer accuracy: {summary['answer_accuracy']}")
    print(f"mean tool F1: {summary['mean_tool_f1']}")
    print(f"all gates passed: {payload['all_gates_passed']}")
    return 0 if payload["all_gates_passed"] else 1


def cmd_compare(args):
    with open(args.baseline) as f:
        baseline = json.load(f)
    with open(args.current) as f:
        current = json.load(f)
    verdict, regressed = write_comparison(args.out, baseline, current)
    print(f"baseline: {baseline['agent']} (gates passed: {baseline['all_gates_passed']})")
    print(f"current: {current['agent']} (gates passed: {current['all_gates_passed']})")
    print(f"verdict: {verdict}")
    if regressed:
        print("regressed gates: " + ", ".join(regressed))
    return 0 if verdict == "PASS" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="traj", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run an agent variant over the task set")
    p_run.add_argument("--config", required=True)
    p_run.add_argument("--out-dir", required=True)
    p_run.set_defaults(func=cmd_run)

    p_score = sub.add_parser("score", help="score recorded traces against the task set")
    p_score.add_argument("--traces", required=True)
    p_score.add_argument("--out-dir", required=True)
    p_score.set_defaults(func=cmd_score)

    p_cmp = sub.add_parser("compare", help="compare two runs for regressions")
    p_cmp.add_argument("--baseline", required=True)
    p_cmp.add_argument("--current", required=True)
    p_cmp.add_argument("--out", required=True)
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
