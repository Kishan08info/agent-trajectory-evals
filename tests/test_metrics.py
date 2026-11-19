"""Unit tests for the trajectory metrics and the rule-based judge."""

from traj.metrics import (
    GATES,
    aggregate,
    args_accuracy,
    check_gates,
    judge,
    keyword_in_text,
    lcs_length,
    multiset_f1,
    score_trajectory,
)


def test_lcs_length():
    assert lcs_length(["a", "b", "c"], ["a", "b", "c"]) == 3
    assert lcs_length(["a", "x", "b"], ["a", "b"]) == 2
    assert lcs_length(["b", "a"], ["a", "b"]) == 1
    assert lcs_length([], ["a"]) == 0
    assert lcs_length([], []) == 0


def test_multiset_f1():
    p, r, f = multiset_f1(["a", "b"], ["a", "b"])
    assert (p, r, f) == (1.0, 1.0, 1.0)
    # Extra call hurts precision, not recall.
    p, r, f = multiset_f1(["a", "b", "b"], ["a", "b"])
    assert p == 2 / 3 and r == 1.0 and abs(f - 0.8) < 1e-9
    # Missing call hurts recall.
    p, r, f = multiset_f1(["a"], ["a", "b"])
    assert p == 1.0 and r == 0.5
    # Empty vs empty is perfect; empty actual vs non-empty golden is 0.
    assert multiset_f1([], []) == (1.0, 1.0, 1.0)
    assert multiset_f1([], ["a"])[2] == 0.0


def test_args_accuracy():
    golden = [
        {"tool": "get_customer", "args": {"customer_id": "C0105"}},
        {"tool": "list_orders", "args": {"customer_id": "C0105", "status": "paid"}},
    ]
    actual = [
        {"tool": "get_customer", "args": {"customer_id": "C0105"}, "observation": ""},
        {"tool": "list_orders", "args": {"customer_id": "C0105", "status": "refunded"}, "observation": ""},
    ]
    assert args_accuracy(actual, golden) == 0.5
    assert args_accuracy([], []) == 1.0
    assert args_accuracy([{"tool": "search_docs", "args": {}, "observation": ""}], []) == 0.0


def test_keyword_in_text_word_boundary():
    # Bare number "2" must not match the "2" inside "2026-02".
    assert keyword_in_text("2", "placed 2 paid orders in 2026-02") is True
    assert keyword_in_text("2", "placed 0 paid orders in 2026-02") is False
    assert keyword_in_text("$99", "costs $99 per month") is True
    assert keyword_in_text("$99", "costs $199 per month") is False
    assert keyword_in_text("Growth", "the Growth plan") is True


def _task(**over):
    t = {
        "id": "tx",
        "question": "q",
        "answerable": True,
        "golden": [{"tool": "search_docs", "args": {"query": "x"}}],
        "answer_keywords": ["$99", "Growth"],
    }
    t.update(over)
    return t


def _traj(**over):
    tr = {
        "task_id": "tx",
        "agent": "test",
        "steps": [
            {"tool": "search_docs", "args": {"query": "x"},
             "observation": "Growth plan: $99 per month."}
        ],
        "answer": "Growth plan: $99 per month.",
        "abstained": False,
    }
    tr.update(over)
    return tr


def test_score_trajectory_perfect():
    rec = score_trajectory(_traj(), _task())
    assert rec["tool_f1"] == 1.0
    assert rec["step_accuracy"] == 1.0
    assert rec["args_accuracy"] == 1.0
    assert rec["answer_correct"] == 1
    assert rec["judge_total"] == 6


def test_score_trajectory_wrong_tool_order():
    tr = _traj(steps=[
        {"tool": "get_customer", "args": {"customer_id": "C1"}, "observation": ""},
        {"tool": "search_docs", "args": {"query": "x"}, "observation": ""},
    ])
    task = _task(golden=[
        {"tool": "search_docs", "args": {"query": "x"}},
        {"tool": "get_customer", "args": {"customer_id": "C1"}},
    ])
    rec = score_trajectory(tr, task)
    # Same tools, wrong order: F1 stays 1.0, step accuracy drops to 0.5.
    assert rec["tool_f1"] == 1.0
    assert rec["step_accuracy"] == 0.5


def test_score_trajectory_unanswerable_abstain():
    task = _task(answerable=False, golden=[], answer_keywords=[])
    rec = score_trajectory(_traj(steps=[], abstained=True, answer="I don't know."),
                           task)
    assert rec["tool_f1"] == 1.0
    assert rec["step_accuracy"] == 1.0
    assert rec["abstention_correct"] == 1
    assert rec["judge_total"] == 6


def test_score_trajectory_unanswerable_answered():
    task = _task(answerable=False, golden=[], answer_keywords=[])
    tr = _traj(steps=[
        {"tool": "search_docs", "args": {"query": "q"}, "observation": "Pricing."}
    ], abstained=False, answer="The CEO is Alice.")
    rec = score_trajectory(tr, task)
    assert rec["abstention_correct"] == 0
    assert rec["tool_f1"] == 0.0
    # Ungrounded (0) + incomplete (0) + 1 extra call -> efficiency 1.
    assert rec["judge_total"] == 1


def test_judge_grounds_in_observations_not_answer():
    # Answer right but evidence missing from observations -> groundedness 0.
    task = _task()
    tr = _traj(steps=[
        {"tool": "search_docs", "args": {"query": "x"},
         "observation": "Unrelated document text."}
    ])
    scores, reasons = judge(tr, task, tr["steps"][0]["observation"])
    assert scores["groundedness"] == 0
    assert scores["completeness"] == 2  # answer itself has the keywords
    assert any("groundedness 0/2" in r for r in reasons)


def test_aggregate_and_gates():
    records = [score_trajectory(_traj(), _task()) for _ in range(3)]
    summary = aggregate(records)
    assert summary["n_tasks"] == 3
    assert summary["answer_accuracy"] == 1.0
    assert summary["abstention_recall"] is None  # no unanswerable tasks
    gates = check_gates(summary)
    # Abstention gate has no value -> fails closed (None actual).
    assert gates["abstention_recall"][0] is False
    assert gates["answer_accuracy"][0] is True
    assert set(GATES) == {
        "answer_accuracy", "abstention_recall", "mean_tool_f1",
        "mean_step_accuracy", "mean_judge_total",
    }
