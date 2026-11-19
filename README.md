# Agent Trajectory Evals

A small, dependency-free command-line harness that scores **multi-step agent
trajectories** — which tools an agent called, in what order, with which
arguments, and whether its final answer follows from what the tools actually
returned — not just whether the final answer looks right.

Single-answer evals (see [rag-eval-harness](https://github.com/Kishan08info/rag-eval-harness),
project 17) cannot see a wrong tool call that still lands on the right
answer, or a right tool sequence that fails at the final step. Trajectory
evals can, and they localize the failure: planning vs retrieval vs answering.

## Why this exists

AI Engineer postings keep asking for the same thing: **evaluation
infrastructure for agents** — not just for RAG answers. The Nov 19, 2026
pool is explicit about it: Guidewire's Junior AI Engineer (Applied AI) asks
for an "eval loop, golden sets, trajectory evaluation, LLM-as-judge" on a
production voice-AI claims agent; BlueCargo wants "evaluation pipelines" for
agentic systems; Rainbrand wants engineers to "build evaluations and feedback
loops"; Topsail wants "evals and observability" for agent runtimes. No
earlier project covered evaluating agent *behaviour* over multiple steps —
project 17 scores RAG answers, project 18 guards single answers, project 19
orchestrates agents but does not score their trajectories. This fills that
gap.

## What it measures

All metrics are plain fractions over the 12-task eval set — no LLM judge, no
hidden model, nothing to tune behind your back.

| Metric | What it means |
| --- | --- |
| `tool_precision` / `tool_recall` / `tool_f1` | Multiset overlap of tool *names* (order-insensitive): did it call the right tools at all? |
| `step_accuracy` | LCS length / len(golden): how much of the golden plan ran *in order* |
| `sequence_similarity` | Dice-style 2·LCS / (len(actual)+len(golden)) |
| `args_accuracy` | Fraction of golden steps whose matched call carries the right arguments |
| `answer_correct` | All expected keywords present in the final answer (answerable tasks) |
| `abstention_precision` / `recall` / `F1` | Did it refuse the unanswerable tasks, and only those? |
| `judge_total` (/6) | Rule-based rubric: groundedness (2) + completeness (2) + efficiency (2) |
| `extra_tool_calls` / `missing_tool_calls` | Raw counts |

The "judge" is a **deterministic rule-based stand-in for an LLM-as-judge**,
not a model: groundedness checks the expected keywords against the *tool
observations*, completeness checks them against the *answer*, efficiency
penalises extra calls. Every score carries its reasons in the per-task
record, so any score is auditable by reading the trace.

`run` exits 0 when all gates pass, 1 when a gate fails. `compare` exits 0
on PASS, 1 when the current run regresses any gate the baseline passed.
`score` replays traces recorded from any agent (including a real one) against
the task set, so the harness works as a CI gate for agent changes.

Gates (the set is small — 10 answerable tasks — so one wrong answer is a
10-point drop, and the bars are set accordingly): answer accuracy ≥ 0.95,
abstention recall = 1.0, mean tool F1 ≥ 0.95, mean step accuracy ≥ 0.95,
mean judge total ≥ 5.5/6.

## The demo agent

The bundled agent is a **rule-based stand-in, not an LLM**: keyword planning,
TF-IDF retrieval, template answers composed from tool observations. It exists
so the harness has real trajectories to score; the same CLI scores traces
from any real agent via `traj score`.

Five variants ship in `configs/`, each degrading the trajectory in one
specific way:

| Variant | What changes |
| --- | --- |
| `baseline` | Reference policy; freshness cutoff on; abstains when unanswerable |
| `chatty` | Repeats every tool call once to "double-check" |
| `sloppy` | Wrong first tool on multi-step tasks, drops the price lookup on t05, queries refunded instead of paid orders on t07 |
| `stale` | Retrieval without the freshness cutoff — the superseded 2024 pricing archive outranks the current price list |
| `no_abstain` | Answers unanswerable tasks from whatever the search returns |

## Quickstart

```bash
# No dependencies for the harness itself (Python 3.10+, standard library only).
# Tests need pytest: pip install -r requirements.txt

# Regenerate the seeded data, run all five variants, compare each to baseline:
bash run_demo.sh

# Or one run at a time:
python3 -m traj run --config configs/baseline.json --out-dir outputs/run_baseline
python3 -m traj compare --baseline outputs/run_baseline/summary.json \
    --current outputs/run_stale/summary.json --out outputs/comparison_stale.md

# Score traces from another agent (any JSONL with the same trace shape):
python3 -m traj score --traces my_agent_traces.jsonl --out-dir outputs/scored
```

## Results (real runs, seeded data)

12 tasks (10 answerable + 2 unanswerable) over a fictional "Northwind
Analytics" corpus (10 docs, incl. a stale June 2024 pricing archive) and a
48-order warehouse (8 customers, Jan–Jun 2026). Every expected answer is
computed from the generated data, never hand-typed.

| Variant | Answer acc | Abstention recall | Mean tool F1 | Mean step acc | Mean args acc | Mean judge /6 | Extra calls | Gates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6.00 | 0 | all pass |
| chatty | 1.00 | 1.00 | 0.72 | 1.00 | 1.00 | 5.00 | 12 | FAIL: tool F1, judge |
| sloppy | 0.80 | 1.00 | 0.98 | 0.96 | 0.88 | 5.42 | 1 | FAIL: answer, judge |
| stale | 0.70 | 1.00 | 1.00 | 1.00 | 1.00 | 5.75 | 0 | FAIL: answer |
| no_abstain | 1.00 | 0.00 | 0.83 | 0.83 | 0.83 | 5.17 | 2 | FAIL: abstention, tool F1, step, judge |

What each failure mode proves:

- **chatty — right answers, wasteful trajectory.** Answer accuracy stays
  1.00, but 12 extra tool calls drag tool F1 to 0.72 and the judge's
  efficiency dimension to 0. Answer-only evals would call this agent perfect;
  trajectory evals catch the doubled cost.
- **sloppy — planning and argument errors.** A junk first tool call, a
  dropped price lookup (t05 answers the plan but never its price), and a
  wrong `status` argument (t07 counts refunded orders as paid) drop answer
  accuracy to 0.80 and args accuracy to 0.88.
- **stale — retrieval failure, planning intact.** Tool F1, step accuracy and
  args accuracy stay 1.00 — the agent called exactly the right tools in the
  right order — but answer accuracy falls to 0.70: the Growth price comes
  back $49 (2024 archive) instead of $99, Starter $29 instead of $49. The
  split between trajectory metrics and answer metrics *localizes* the fault
  to retrieval (the freshness cutoff), not planning. This is the case
  answer-only evals cannot distinguish from a planning failure.
- **no_abstain — abstention failure.** Answers both unanswerable tasks (the
  CEO's name; 2025 revenue, which the data does not cover). Abstention
  recall 0.00; the judge scores both trajectories 1/6.

Reproducibility: deleting `data/` and `outputs/` and re-running
`run_demo.sh` reproduces every `summary.json`, `per_task.csv`, `report.md`
and comparison byte-identically; traces reproduce identically apart from
wall-clock `latency_ms`. 21/21 pytest checks pass.

## Limitations (honest)

- The demo agent is rule-based, not an LLM — its trajectories are simple by
  design. The harness itself is agent-agnostic (`traj score` takes any
  recorded traces).
- The judge is a deterministic rule-based stand-in, not an LLM-as-judge: it
  cannot catch attribution swaps or subtle misreadings, only keyword-level
  grounding/completeness. Swapping in a real LLM judge behind the same
  rubric is the natural next step.
- Answer correctness is keyword matching (bare numbers match on word
  boundaries, so "2" does not match inside "2026-02") — a deliberate fix
  after the first sloppy run scored a wrong count as correct. It is a
  proxy, not semantic equivalence.
- All data is synthetic (seed 42). Nothing here is production agent
  experience.
