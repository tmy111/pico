# s05 - State + Trace：每次运行都能复盘

> 目标：把一次 `ask()` 变成可审计的 run，而不是一串消失在终端里的文本。

## Pico 的两类状态

```text
session
  保存可恢复的会话状态：history、memory、active_skill、checkpoints

run
  保存一次用户请求的审计工件：task_state、trace、report
```

正式 Pico 把它们分开：

- `pico/session_store.py`
- `pico/run_store.py`

## Run 工件

每次 `ask()` 都会创建 `.pico/runs/<run_id>/`：

```text
task_state.json  当前任务状态快照
trace.jsonl      逐事件时间线
report.json      运行结束摘要
```

trace 里常见事件：

```text
run_started
prompt_built
model_requested
model_parsed
tool_executed
checkpoint_created
run_finished
model_error
```

## 从 0 实现

最小 `TaskState` 需要记录：

- `run_id`
- `user_request`
- `attempts`
- `tool_steps`
- `status`
- `stop_reason`
- `final_answer`
- `last_tool`

最小 `RunStore` 需要：

```python
start_run(task_state)
write_task_state(task_state)
append_trace(task_state, event)
write_report(task_state, report)
```

写 JSON 时尽量用原子写：先写临时文件，再 replace。

## Pico 源码对应

- `pico/task_state.py`
- `pico/run_store.py`
- `Pico.emit_trace()`
- `Pico.build_report()`
- dashboard 消费这些工件：`pico/dashboard.py`、`pico/dashboard_frontend.py`

## 练习

1. 运行 `python -m pytest tests/test_task_state.py tests/test_run_store.py`
2. 手动跑一次 `uv run pico "list files"`，查看 `.pico/runs/<run_id>/trace.jsonl`。
3. 给 `report.json` 增加一个 `duration_ms` 汇总字段。
