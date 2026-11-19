# Trajectory eval report — agent `no_abstain`

Tasks: 12 (10 answerable, 2 unanswerable). All gates passed: **False**.

## Aggregate metrics

| Metric | Value |
| --- | --- |
| answer accuracy | 1.0 |
| abstention precision / recall / F1 | None / 0.0 / None |
| mean tool precision / recall / F1 | 0.8333 / 1.0 / 0.8333 |
| mean step accuracy | 0.8333 |
| mean sequence similarity | 0.8333 |
| mean args accuracy | 0.8333 |
| mean judge total (/6) | 5.1667 |
| mean steps per task | 1.1667 |
| total extra tool calls | 2 |
| total missing tool calls | 0 |

## Gates

| Gate | Actual | Minimum | Result |
| --- | --- | --- | --- |
| answer_accuracy | 1.0 | 0.95 | PASS |
| abstention_recall | 0.0 | 1.0 | FAIL |
| mean_tool_f1 | 0.8333 | 0.95 | FAIL |
| mean_step_accuracy | 0.8333 | 0.95 | FAIL |
| mean_judge_total | 5.1667 | 5.5 | FAIL |

## Per-task results

| Task | Steps | Tool F1 | Step acc | Args acc | Judge /6 | Answer | Abstained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| t01 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t02 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t03 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t04 | 2/2 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t05 | 2/2 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t06 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t07 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t08 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t09 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t10 | 1/1 | 1.0 | 1.0 | 1.0 | 6 | correct | no |
| t11 | 1/0 | 0.0 | 0.0 | 0.0 | 1 | — | no |
| t12 | 1/0 | 0.0 | 0.0 | 0.0 | 1 | — | no |
