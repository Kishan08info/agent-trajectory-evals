"""Tests for the demo agent: each variant must behave as designed."""

from pathlib import Path

from traj.agent import Agent
from traj.dataset import load_tasks

DATA = Path(__file__).resolve().parent.parent / "data"


def _tasks():
    return load_tasks(DATA)


def _run(variant):
    agent = Agent(DATA, variant=variant)
    return {t["id"]: agent.run(t) for t in _tasks()}


def test_baseline_is_perfect():
    from traj.metrics import aggregate, score_trajectory

    tasks = _tasks()
    agent = Agent(DATA, variant="baseline")
    records = [score_trajectory(agent.run(t), t) for t in tasks]
    summary = aggregate(records)
    assert summary["answer_accuracy"] == 1.0
    assert summary["abstention_recall"] == 1.0
    assert summary["mean_tool_f1"] == 1.0
    assert summary["mean_step_accuracy"] == 1.0
    assert summary["mean_judge_total"] == 6.0
    assert summary["total_extra_tool_calls"] == 0


def test_baseline_answers_are_correct():
    runs = _run("baseline")
    assert "$99" in runs["t01"]["answer"] and "Growth" in runs["t01"]["answer"]
    assert "$995" in runs["t04"]["answer"]
    assert "$1643" in runs["t06"]["answer"]
    assert "2 paid orders" in runs["t07"]["answer"]
    assert runs["t11"]["abstained"] is True
    assert runs["t12"]["abstained"] is True


def test_stale_answers_pricing_from_the_2024_archive():
    runs = _run("stale")
    # Tool sequence is perfect; only the retrieved evidence (and the answer)
    # is wrong — that is the failure mode this variant exists to catch.
    assert "$49" in runs["t01"]["answer"]  # 2024 Growth price, not $99
    assert "$29" in runs["t08"]["answer"]  # 2024 Starter price, not $49
    assert runs["t01"]["steps"][0]["observation"].startswith("[d02]")
    assert "$49" in runs["t05"]["answer"]  # same stale lookup, via the plan step    # Non-pricing tasks are unaffected.
    assert "30 days" in runs["t02"]["answer"]
    assert runs["t11"]["abstained"] is True


def test_chatty_repeats_every_call_but_stays_correct():
    runs = _run("chatty")
    base = _run("baseline")
    for tid, tr in runs.items():
        assert len(tr["steps"]) == 2 * len(base[tid]["steps"])
        assert tr["answer"] == base[tid]["answer"]
        assert tr["abstained"] == base[tid]["abstained"]


def test_sloppy_drops_the_price_lookup_and_uses_wrong_args():
    runs = _run("sloppy")
    t05 = runs["t05"]
    assert [s["tool"] for s in t05["steps"]] == ["search_docs", "get_customer"]
    assert "$99" not in t05["answer"]  # price never looked up
    t07 = runs["t07"]
    assert t07["steps"][0]["args"]["status"] == "refunded"
    assert "0 paid orders" in t07["answer"]


def test_no_abstain_answers_the_unanswerable_tasks():
    runs = _run("no_abstain")
    assert runs["t11"]["abstained"] is False
    assert runs["t12"]["abstained"] is False
    assert runs["t01"]["answer"] == _run("baseline")["t01"]["answer"]


def test_runs_are_deterministic_apart_from_latency():
    a = _run("baseline")
    b = _run("baseline")
    for tid in a:
        assert {k: v for k, v in a[tid].items() if k != "latency_ms"} == {
            k: v for k, v in b[tid].items() if k != "latency_ms"
        }
