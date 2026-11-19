"""Trajectory metrics.

Everything is a plain fraction over the task set — no LLM, no hidden model.

Per-task metrics (actual trajectory vs the task's golden trajectory):

* ``tool_precision`` / ``tool_recall`` / ``tool_f1`` — multiset overlap of
  tool *names* (order-insensitive: did it call the right tools at all?).
* ``step_accuracy`` — LCS length / len(golden): how much of the golden plan
  was executed *in order*.
* ``sequence_similarity`` — Dice-style 2*LCS / (len(actual)+len(golden)).
* ``args_accuracy`` — for each golden step, the first unmatched actual step
  with the same tool name: fraction whose key arguments match the golden.
* ``extra_tool_calls`` / ``missing_tool_calls`` — raw counts.
* ``answer_correct`` — all expected keywords present in the final answer
  (answerable tasks only; a wrong abstention scores 0).
* ``abstention_correct`` — unanswerable tasks only.

Judge (rule-based stand-in for an LLM-as-judge — labelled as such
everywhere it appears): three 0–2 rubric dimensions, scored from the
trajectory itself, never from a model:

* ``groundedness`` — expected keywords present in the *observations*
  (2 all, 1 some, 0 none). An abstention on an unanswerable task scores 2:
  refusing to claim what is not in evidence is grounded.
* ``completeness`` — expected keywords present in the *answer*.
* ``efficiency`` — 2 if no extra calls, 1 if one extra, 0 if two or more.

``judge_total`` is the sum, out of 6. The judge is deterministic and
auditable: ``judge_reasons`` lists exactly which check produced each score.
"""

from collections import Counter
import re


def lcs_length(a, b):
    """Length of the longest common subsequence of two sequences."""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def multiset_f1(actual, golden):
    """Precision/recall/F1 over multisets of tool names."""
    if not actual and not golden:
        return 1.0, 1.0, 1.0
    if not actual:
        return 0.0, 0.0, 0.0
    if not golden:
        return 0.0, 1.0, 0.0
    inter = sum((Counter(actual) & Counter(golden)).values())
    precision = inter / len(actual)
    recall = inter / len(golden)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def args_accuracy(actual_steps, golden_steps):
    """Fraction of golden steps whose first unmatched same-tool actual step
    carries identical arguments (compared on the golden step's arg keys)."""
    if not golden_steps:
        return 1.0 if not actual_steps else 0.0
    remaining = list(actual_steps)
    matched = 0
    for g in golden_steps:
        for i, a in enumerate(remaining):
            if a["tool"] == g["tool"]:
                remaining.pop(i)
                if all(a["args"].get(k) == v for k, v in g["args"].items()):
                    matched += 1
                break
    return matched / len(golden_steps)


def keyword_in_text(keyword, text):
    """Case-insensitive keyword match. Bare numbers match on word boundaries
    so that the expected count "2" does not match the "2" inside "2026-02"."""
    text = text or ""
    if keyword.isdigit():
        return re.search(r"\b" + re.escape(keyword) + r"\b", text) is not None
    return keyword.lower() in text.lower()


def _keywords_present(keywords, text):
    return [k for k in keywords if keyword_in_text(k, text)]


def judge(trajectory, task, observations_text):
    """Rule-based judge. Returns (scores dict, reasons list)."""
    keywords = task.get("answer_keywords") or []
    extra = max(0, len(trajectory["steps"]) - len(task["golden"]))
    reasons = []

    if not task["answerable"]:
        if trajectory["abstained"]:
            scores = {"groundedness": 2, "completeness": 2}
            reasons.append("abstained on an unanswerable task (grounded)")
            reasons.append("abstention is the complete correct response")
        else:
            scores = {"groundedness": 0, "completeness": 0}
            reasons.append("answered an unanswerable task (ungrounded)")
            reasons.append("answer cannot be complete: no correct answer exists")
    else:
        in_obs = _keywords_present(keywords, observations_text)
        in_ans = _keywords_present(keywords, trajectory["answer"])
        g = 2 if len(in_obs) == len(keywords) else (1 if in_obs else 0)
        c = 2 if len(in_ans) == len(keywords) else (1 if in_ans else 0)
        scores = {"groundedness": g, "completeness": c}
        reasons.append(
            f"groundedness {g}/2: {len(in_obs)}/{len(keywords)} expected "
            f"keywords in observations"
        )
        reasons.append(
            f"completeness {c}/2: {len(in_ans)}/{len(keywords)} expected "
            f"keywords in answer"
        )
    eff = 2 if extra == 0 else (1 if extra == 1 else 0)
    scores["efficiency"] = eff
    reasons.append(f"efficiency {eff}/2: {extra} extra tool call(s)")
    scores["total"] = sum(scores.values())
    return scores, reasons


def score_trajectory(trajectory, task):
    """Score one recorded trajectory against one task. Returns a dict."""
    actual = [s["tool"] for s in trajectory["steps"]]
    golden = [g["tool"] for g in task["golden"]]
    precision, recall, f1 = multiset_f1(actual, golden)
    lcs = lcs_length(actual, golden)
    step_acc = lcs / len(golden) if golden else (1.0 if not actual else 0.0)
    seq_sim = (
        2 * lcs / (len(actual) + len(golden))
        if actual or golden
        else 1.0
    )
    obs_text = "\n".join(s["observation"] for s in trajectory["steps"])
    judge_scores, judge_reasons = judge(trajectory, task, obs_text)

    rec = {
        "task_id": task["id"],
        "answerable": task["answerable"],
        "n_steps": len(actual),
        "n_golden_steps": len(golden),
        "tool_precision": round(precision, 4),
        "tool_recall": round(recall, 4),
        "tool_f1": round(f1, 4),
        "step_accuracy": round(step_acc, 4),
        "sequence_similarity": round(seq_sim, 4),
        "args_accuracy": round(args_accuracy(trajectory["steps"], task["golden"]), 4),
        "extra_tool_calls": max(0, len(actual) - len(golden)),
        "missing_tool_calls": max(0, len(golden) - len(actual)),
        "judge_groundedness": judge_scores["groundedness"],
        "judge_completeness": judge_scores["completeness"],
        "judge_efficiency": judge_scores["efficiency"],
        "judge_total": judge_scores["total"],
        "judge_reasons": judge_reasons,
        "abstained": trajectory["abstained"],
        "answer": trajectory["answer"],
    }
    if task["answerable"]:
        kws = task.get("answer_keywords") or []
        rec["answer_correct"] = int(
            all(keyword_in_text(k, trajectory["answer"]) for k in kws)
        )
        rec["abstention_correct"] = None
    else:
        rec["answer_correct"] = None
        rec["abstention_correct"] = int(bool(trajectory["abstained"]))
    return rec


def aggregate(records):
    """Aggregate per-task records into a summary dict."""
    ans = [r for r in records if r["answerable"]]
    unans = [r for r in records if not r["answerable"]]
    abstained = [r for r in unans if r["abstained"]]
    false_abstentions = [r for r in ans if r["abstained"]]

    def mean(key, rows):
        return round(sum(r[key] for r in rows) / len(rows), 4) if rows else None

    summary = {
        "n_tasks": len(records),
        "n_answerable": len(ans),
        "n_unanswerable": len(unans),
        "answer_accuracy": mean("answer_correct", ans),
        "abstention_precision": (
            round(len(abstained) / (len(abstained) + len(false_abstentions)), 4)
            if abstained or false_abstentions
            else None
        ),
        "abstention_recall": (
            round(len(abstained) / len(unans), 4) if unans else None
        ),
        "mean_tool_f1": mean("tool_f1", records),
        "mean_tool_precision": mean("tool_precision", records),
        "mean_tool_recall": mean("tool_recall", records),
        "mean_step_accuracy": mean("step_accuracy", records),
        "mean_sequence_similarity": mean("sequence_similarity", records),
        "mean_args_accuracy": mean("args_accuracy", records),
        "mean_judge_total": mean("judge_total", records),
        "mean_steps": mean("n_steps", records),
        "total_extra_tool_calls": sum(r["extra_tool_calls"] for r in records),
        "total_missing_tool_calls": sum(r["missing_tool_calls"] for r in records),
    }
    summary["abstention_f1"] = (
        round(
            2 * summary["abstention_precision"] * summary["abstention_recall"]
            / (summary["abstention_precision"] + summary["abstention_recall"]),
            4,
        )
        if summary["abstention_precision"] is not None
        and summary["abstention_recall"] is not None
        and summary["abstention_precision"] + summary["abstention_recall"] > 0
        else None
    )
    return summary


GATES = {
    # metric -> (minimum, description). The set is small (10 answerable
    # tasks), so one wrong answer is a 10-point drop: the bars below mean
    # "no wrong answers, no missed abstentions, no sloppy trajectories".
    "answer_accuracy": (0.95, "answer accuracy >= 0.95"),
    "abstention_recall": (1.0, "abstention recall == 1.0"),
    "mean_tool_f1": (0.95, "mean tool F1 >= 0.95"),
    "mean_step_accuracy": (0.95, "mean step accuracy >= 0.95"),
    "mean_judge_total": (5.5, "mean judge total >= 5.5 / 6"),
}


def check_gates(summary):
    """Return {gate: (passed, actual, minimum)} for every gate."""
    out = {}
    for metric, (minimum, _) in GATES.items():
        actual = summary.get(metric)
        out[metric] = (actual is not None and actual >= minimum, actual, minimum)
    return out
