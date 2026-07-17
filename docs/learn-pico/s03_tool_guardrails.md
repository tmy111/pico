# s03 - Tool Guardrails：执行前后都要有护栏

> 目标：把“模型想做什么”和“平台允许做什么”分开。

## 工具执行流水线

正式 Pico 的工具执行入口是 `pico/tool_executor.py`。一条工具调用会经过：

```text
allowed_tools allowlist
  -> tool 是否存在
  -> validate_tool 参数校验
  -> redundant_tool_call 重复调用拦截
  -> risky 工具审批
  -> capture before snapshot
  -> run tool
  -> capture after snapshot
  -> diff summary
  -> update memory
  -> return ToolExecutionResult
```

这意味着模型永远不会直接碰底层函数。它只能提交意图，runtime 决定是否执行。

## 从 0 实现

先定义统一返回值：

```python
@dataclass(frozen=True)
class ToolExecutionResult:
    content: str
    metadata: dict
```

然后让失败也走同一种返回路径：

```python
if tool is None:
    return ToolExecutionResult(
        content="error: unknown tool",
        metadata={"tool_status": "rejected", "tool_error_code": "unknown_tool"},
    )
```

不要让工具异常直接炸出 loop。工具失败本身就是下一轮模型可以消费的观察结果。

## Pico 源码对应

- `ToolExecutor.execute()`：护栏总闸口。
- `Pico.approve()`：`ask / auto / never` 三种审批策略。
- `Pico.redundant_tool_call()`：重复工具调用拦截。
- `Pico.capture_workspace_snapshot()` + `diff_workspace_snapshots()`：risky 工具前后对比。
- `Pico.record_process_note_for_tool()`：失败或部分成功时写过程笔记。

## 设计要点

1. risky 工具默认需要审批，除非 `--approval auto`。
2. 只读子 agent 使用 `approval_policy="never"` 和 `read_only=True`。
3. `run_shell` 失败但改了文件时，是 `partial_success`，不是简单 error。
4. metadata 要进入 trace/report，方便复盘工具为什么被拒绝。

## 练习

1. 运行 `python -m pytest tests/test_tool_executor.py tests/test_security.py`
2. 给 `run_shell` 增加一个 deny-list 实验，比如拒绝明显危险命令。
3. 在 report 里统计 `tool_status=rejected` 的次数。
