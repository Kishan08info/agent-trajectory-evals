# Trajectory eval report — agent `stale`

Tasks: 12 (10 answerable, 2 unanswerable). All gates passed: **False**.

## Aggregate metrics

| Metric | Value |
| --- | --- |
| answer accuracy | 0.7 |
| abstention precision / recall / F1 | 1.0 / 1.0 / 1.0 |
| mean tool precision / recall / F1 | 1.0 / 1.0 / 1.0 |
| mean step accuracy | 1.0 |
| mean sequence similarity | 1.0 |
| mean args accuracy | 1.0 |
| mean judge total (/6) | 5.75 |
| mean steps per task | 1.0 |
| total extra tool calls | 0 |
| total missing tool calls | 0 |

## Gates

| Gate | Actual | Minimum | Result |
| --- | --- | --- | --- |
| answer_accuracy | 0.7 | 0.95 | FAIL |
| abstention_recall | 1.0 | 1.0 | PASS |
| mean_tool_f1 | 1.0 | 0.95 | PASS |
| mean_step_accuracy | 1.0 | 0.95 | PASS |
| mean_judge_total | 5.75 | 5.5 | PASS |

## Per-task results

| Task | Steps | Tool F1 | Step acc | Args acc | Judge /6 | Answer | Abstained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| t01 | 1/1 | 1.0 | 1.0 | 1.0 | 5 | wrong | no |
| t02 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t03 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t04 | 2/2 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t05 | 2/2 | 1.0 | 1.0 | 1.0 | 5 | wrong | no |
| t06 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t07 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t08 | 1/1 | 1.0 | 1.0 | 1.0 | 5 | wrong | no |
| t09 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t10 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t11 | 0/0 | 1.0 | 1.0 | 1.0 | 6 | — | yes |
| t12 | 0/0 | 1.0 | 1.0 | 1.0 | 6 | — | yes |
