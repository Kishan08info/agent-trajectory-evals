# Trajectory eval comparison

Baseline: `baseline` — all gates passed: True
Current: `sloppy` — all gates passed: False

## Metric deltas (current − baseline)

| Metric | Baseline | Current | Delta |
| --- | --- | --- | --- |
| answer_accuracy | 1.0 | 0.8 | -0.2 |
| abstention_recall | 1.0 | 1.0 | 0.0 |
| mean_tool_f1 | 1.0 | 0.9833 | -0.0167 |
| mean_step_accuracy | 1.0 | 0.9583 | -0.0417 |
| mean_sequence_similarity | 1.0 | 0.9417 | -0.0583 |
| mean_args_accuracy | 1.0 | 0.875 | -0.125 |
| mean_judge_total | 6.0 | 5.4167 | -0.5833 |
| mean_steps | 1.0 | 1.0833 | 0.0833 |
| total_extra_tool_calls | 0 | 1 | 1 |

## Gate changes

| Gate | Baseline | Current |
| --- | --- | --- |
| abstention_recall | PASS | PASS |
| answer_accuracy | PASS | FAIL **REGRESSION** |
| mean_judge_total | PASS | FAIL **REGRESSION** |
| mean_step_accuracy | PASS | PASS |
| mean_tool_f1 | PASS | PASS |

## Verdict: **FAIL — regressions vs baseline**
