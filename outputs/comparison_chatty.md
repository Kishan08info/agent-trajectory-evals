# Trajectory eval comparison

Baseline: `baseline` — all gates passed: True
Current: `chatty` — all gates passed: False

## Metric deltas (current − baseline)

| Metric | Baseline | Current | Delta |
| --- | --- | --- | --- |
| answer_accuracy | 1.0 | 1.0 | 0.0 |
| abstention_recall | 1.0 | 1.0 | 0.0 |
| mean_tool_f1 | 1.0 | 0.7222 | -0.2778 |
| mean_step_accuracy | 1.0 | 1.0 | 0.0 |
| mean_sequence_similarity | 1.0 | 0.7222 | -0.2778 |
| mean_args_accuracy | 1.0 | 1.0 | 0.0 |
| mean_judge_total | 6.0 | 5.0 | -1.0 |
| mean_steps | 1.0 | 2.0 | 1.0 |
| total_extra_tool_calls | 0 | 12 | 12 |

## Gate changes

| Gate | Baseline | Current |
| --- | --- | --- |
| abstention_recall | PASS | PASS |
| answer_accuracy | PASS | PASS |
| mean_judge_total | PASS | FAIL **REGRESSION** |
| mean_step_accuracy | PASS | PASS |
| mean_tool_f1 | PASS | FAIL **REGRESSION** |

## Verdict: **FAIL — regressions vs baseline**
