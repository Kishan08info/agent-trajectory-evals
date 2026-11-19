# Trajectory eval comparison

Baseline: `baseline` — all gates passed: True
Current: `stale` — all gates passed: False

## Metric deltas (current − baseline)

| Metric | Baseline | Current | Delta |
| --- | --- | --- | --- |
| answer_accuracy | 1.0 | 0.7 | -0.3 |
| abstention_recall | 1.0 | 1.0 | 0.0 |
| mean_tool_f1 | 1.0 | 1.0 | 0.0 |
| mean_step_accuracy | 1.0 | 1.0 | 0.0 |
| mean_sequence_similarity | 1.0 | 1.0 | 0.0 |
| mean_args_accuracy | 1.0 | 1.0 | 0.0 |
| mean_judge_total | 6.0 | 5.75 | -0.25 |
| mean_steps | 1.0 | 1.0 | 0.0 |
| total_extra_tool_calls | 0 | 0 | 0 |

## Gate changes

| Gate | Baseline | Current |
| --- | --- | --- |
| abstention_recall | PASS | PASS |
| answer_accuracy | PASS | FAIL **REGRESSION** |
| mean_judge_total | PASS | PASS |
| mean_step_accuracy | PASS | PASS |
| mean_tool_f1 | PASS | PASS |

## Verdict: **FAIL — regressions vs baseline**
