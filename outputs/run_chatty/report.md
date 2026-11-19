# Trajectory eval report — agent `chatty`

Tasks: 12 (10 answerable, 2 unanswerable). All gates passed: **False**.

## Aggregate metrics

| Metric | Value |
| --- | --- |
| answer accuracy | 1.0 |
| abstention precision / recall / F1 | 1.0 / 1.0 / 1.0 |
| mean tool precision / recall / F1 | 0.5833 / 1.0 / 0.7222 |
| mean step accuracy | 1.0 |
| mean sequence similarity | 0.7222 |
| mean args accuracy | 1.0 |
| mean judge total (/6) | 5.0 |
| mean steps per task | 2.0 |
| total extra tool calls | 12 |
| total missing tool calls | 0 |

## Gates

| Gate | Actual | Minimum | Result |
| --- | --- | --- | --- |
| answer_accuracy | 1.0 | 0.95 | PASS |
| abstention_recall | 1.0 | 1.0 | PASS |
| mean_tool_f1 | 0.7222 | 0.95 | FAIL |
| mean_step_accuracy | 1.0 | 0.95 | PASS |
| mean_judge_total | 5.0 | 5.5 | FAIL |

## Per-task results

| Task | Steps | Tool F1 | Step acc | Args acc | Judge /6 | Answer | Abstained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| t01 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t02 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t03 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t04 | 4/2 | 0.6667 | 1.0 | 1.0 | 4 | correct | no |
| t05 | 4/2 | 0.6667 | 1.0 | 1.0 | 4 | correct | no |
| t06 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t07 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t08 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t09 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t10 | 2/1 | 0.6667 | 1.0 | 1.0 | 5 | correct | no |
| t11 | 0/0 | 1.0 | 1.0 | 1.0 | 6 | — | yes |
| t12 | 0/0 | 1.0 | 1.0 | 1.0 | 6 | — | yes |
