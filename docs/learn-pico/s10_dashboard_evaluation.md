# s10 - Dashboard + Evaluation：把 agent 变成可观察系统

> 目标：用 dashboard 和 benchmark 判断 harness 改动有没有变好。

## 本地工作台

启动：

```bash
uv run pico-viewer --cwd .
```

相关源码：

- `pico/dashboard.py`
- `pico/dashboard_frontend.py`

工作台读取：

```text
.pico/runs/
.pico/sessions/
benchmarks/results/
assets/screenshots/
```

它展示 run 列表、流程图、trace 时间线、report 和 benchmark 摘要。

## Evaluation

评估相关源码：

```text
pico/evaluation/metrics.py
pico/evaluation/evaluator.py
benchmarks/coding_tasks.json
scripts/run_provider_experiments.py
scripts/run_large_scale_experiments.py
scripts/collect_resume_metrics.py
```

测试覆盖：

```text
tests/test_evaluator.py
tests/test_metrics.py
tests/test_dashboard.py
```

## 从 0 实现

最小 dashboard 不需要先做漂亮 UI。先做到：

1. 扫描 `.pico/runs`。
2. 读取每个 run 的 `task_state.json`、`trace.jsonl`、`report.json`。
3. 按时间排序展示。
4. 能点击查看 trace。

最小 evaluation 需要：

1. 一组任务。
2. 一套 fake 或真实 provider。
3. 对最终答案、工具步数、停止原因做指标统计。

## 设计要点

1. 不要只看“回答对不对”，也要看工具步数、失败类型、是否触发 checkpoint。
2. 每个 harness 机制都应该能在 trace/report 里看到证据。
3. 做 MCP、skill、memory 改动前后，要跑同一组 benchmark。

## 练习

1. 运行 `python -m pytest tests/test_dashboard.py tests/test_evaluator.py tests/test_metrics.py`
2. 新增一个 benchmark 任务，要求 agent 读 README 后回答。
3. 给 dashboard 增加一个 `tool_status` 汇总小表。
