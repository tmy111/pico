# s01 - Agent Loop：先把循环跑起来

> 目标：从 0 写出最小 Pico。它只做一件事：让模型返回 `<tool>` 或 `<final>`，runtime 解析后继续循环。

## 为什么先做 loop

Coding agent 的核心不是多复杂的流程图，而是一个稳定反馈回路：

```text
user request
  -> build prompt
  -> model complete
  -> parse response
  -> tool? execute and append result
  -> final? stop
```

在 Pico 里，这个骨架有两个版本：

- 教学版：`examples/mini-pico/mini_pico/agent_loop.py`
- 正式版：`pico/agent_loop.py`

## 从 0 实现

最小对象需要 5 个能力：

1. `model_client.complete(prompt, max_new_tokens)`：给 prompt，拿文本。
2. `parse(raw)`：把模型文本解析成 `tool`、`final` 或 `retry`。
3. `execute_tool(name, args)`：执行工具并返回文本。
4. `record(item)`：把用户、工具结果、最终答案写入历史。
5. `context_manager.build(user_message)`：组装下一轮 prompt。

伪代码：

```python
while tool_steps < max_steps:
    prompt, metadata = context_manager.build(user_message)
    raw = model_client.complete(prompt, max_new_tokens)
    kind, payload = parse(raw)

    if kind == "tool":
        result = execute_tool(payload["name"], payload.get("args", {}))
        record({"role": "tool", "content": result.content})
        continue

    if kind == "final":
        record({"role": "assistant", "content": payload})
        return payload

    record({"role": "assistant", "content": retry_notice})
```

## Pico 源码对应

`examples/mini-pico/mini_pico/agent_loop.py` 已经是最小教学实现。正式版 `pico/agent_loop.py` 在同一条循环上增加了：

- `TaskState`：记录尝试次数、工具步数、停止原因。
- `RunStore`：写 `task_state.json`、`trace.jsonl`、`report.json`。
- `checkpoint`：每次工具执行或结束后创建恢复点。
- `prompt cache`：如果 provider 支持，传入稳定 prefix 的 hash。
- `finalization_turn`：工具步数耗尽后，再给模型一次只返回最终答案的机会。

## 测试切入点

读 `examples/mini-pico/tests/test_agent_loop.py`。这个测试用 `FakeModelClient` 固定返回：

1. 一次 `read_file` 工具调用。
2. 一次 `<final>Done.</final>`。

它验证了一个完整回路：

- 模型被调用两次。
- 第二次 prompt 里包含第一次工具结果。
- run 目录里写出了 `task_state.json`、`trace.jsonl`、`report.json`。

## 练习

1. 只运行 mini 测试：`python -m pytest examples/mini-pico/tests/test_agent_loop.py`
2. 在 mini loop 里加一个新的 trace 事件，比如 `loop_iteration_started`。
3. 对照正式版 `pico/agent_loop.py`，找出哪些逻辑是“核心 loop”，哪些是“生产化护栏”。
