# Trajectory eval report — agent `sloppy`

Tasks: 12 (10 answerable, 2 unanswerable). All gates passed: **False**.

## Aggregate metrics

| Metric | Value |
| --- | --- |
| answer accuracy | 0.8 |
| abstention precision / recall / F1 | 1.0 / 1.0 / 1.0 |
| mean tool precision / recall / F1 | 0.9722 / 1.0 / 0.9833 |
| mean step accuracy | 0.9583 |
| mean sequence similarity | 0.9417 |
| mean args accuracy | 0.875 |
| mean judge total (/6) | 5.4167 |
| mean steps per task | 1.0833 |
| total extra tool calls | 1 |
| total missing tool calls | 0 |

## Gates

| Gate | Actual | Minimum | Result |
| --- | --- | --- | --- |
| answer_accuracy | 0.8 | 0.95 | FAIL |
| abstention_recall | 1.0 | 1.0 | PASS |
| mean_tool_f1 | 0.9833 | 0.95 | PASS |
| mean_step_accuracy | 0.9583 | 0.95 | PASS |
| mean_judge_total | 5.4167 | 5.5 | FAIL |

## Per-task results

| Task | Steps | Tool F1 | Step acc | Args acc | Judge /6 | Answer | Abstained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| t01 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t02 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t03 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t04 | 3/2 | 0.8 | 1.0 | 1.0 | 5 | correct | no |
| t05 | 2/2 | 1.0 | 0.5 | 0.5 | 4 | wrong | no |
| t06 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t07 | 1/1 | 1.0 | 1.0 | 0.0 | 2 | wrong | no |
| t08 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t09 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t10 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t11 | 0/0 | 1.0 | 1.0 | 1.0 | 6 | — | yes |
| t12 | 0/0 | 1.0 | 1.0 | 1.0 | 6 | — | yes |
