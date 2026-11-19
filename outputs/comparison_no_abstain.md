# Trajectory eval comparison

Baseline: `baseline` — all gates passed: True
Current: `no_abstain` — all gates passed: False

## Metric deltas (current − baseline)

| Metric | Baseline | Current | Delta |
| --- | --- | --- | --- |
| answer_accuracy | 1.0 | 1.0 | 0.0 |
| abstention_recall | 1.0 | 0.0 | -1.0 |
| mean_tool_f1 | 1.0 | 0.8333 | -0.1667 |
| mean_step_accuracy | 1.0 | 0.8333 | -0.1667 |
| mean_sequence_similarity | 1.0 | 0.8333 | -0.1667 |
| mean_args_accuracy | 1.0 | 0.8333 | -0.1667 |
| mean_judge_total | 6.0 | 5.1667 | -0.8333 |
| mean_steps | 1.0 | 1.1667 | 0.1667 |
| total_extra_tool_calls | 0 | 2 | 2 |

## Gate changes

| Gate | Baseline | Current |
| --- | --- | --- |
| abstention_recall | PASS | FAIL **REGRESSION** |
| answer_accuracy | PASS | PASS |
| mean_judge_total | PASS | FAIL **REGRESSION** |
| mean_step_accuracy | PASS | FAIL **REGRESSION** |
| mean_tool_f1 | PASS | FAIL **REGRESSION** |

## Verdict: **FAIL — regressions vs baseline**
