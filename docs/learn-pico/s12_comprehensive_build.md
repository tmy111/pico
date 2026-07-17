# s12 - Comprehensive Build：从 mini-pico 走到完整 pico

> 目标：给出一张实现清单，帮助你从空目录一步步构建当前 Pico。

## Phase 1：最小 agent

1. 建包结构：`pico/__init__.py`、`pico/__main__.py`、`pico/cli.py`。
2. 写 `FakeModelClient`。
3. 写 `Workspace.path()`，确保路径不能逃逸。
4. 写 `tools.py`：`list_files`、`read_file`。
5. 写 `ContextManager.build()`。
6. 写 `AgentLoop.run()`。
7. 写第一个测试：工具调用后 final。

对应 mini 源码：`examples/mini-pico/`。

## Phase 2：受控工具

1. 加 `search`、`write_file`、`patch_file`。
2. 加 `ToolExecutor`。
3. 加 risky / safe 标记。
4. 加 approval policy。
5. 加重复调用拦截。
6. 加工具 metadata。

对应正式源码：`pico/tools.py`、`pico/tool_executor.py`。

## Phase 3：状态与复盘

1. 加 `TaskState`。
2. 加 `SessionStore`。
3. 加 `RunStore`。
4. 每个 run 写 `task_state.json`、`trace.jsonl`、`report.json`。
5. dashboard 先读这些 JSON，不急着做复杂 UI。

对应源码：`pico/task_state.py`、`pico/session_store.py`、`pico/run_store.py`。

## Phase 4：上下文工程

1. 拆 `prompt_prefix.py`。
2. 给工具集合算 `tool_signature`。
3. 给 workspace 算 fingerprint。
4. `ContextManager` 按 section 预算组 prompt。
5. prompt metadata 写入 trace/report。

对应源码：`pico/prompt_prefix.py`、`pico/context_manager.py`。

## Phase 5：记忆与恢复

1. 加 working memory：当前任务、最近文件、文件摘要。
2. 加 relevant memory：按当前请求召回少量 notes。
3. 加 durable memory：`.pico/memory/MEMORY.md` 和 topics。
4. 加 checkpoint：目标、下一步、关键文件 hash、runtime_identity。
5. resume 时检查 freshness 和 runtime mismatch。

对应源码：`pico/features/memory.py`、`pico/checkpoint.py`。

## Phase 6：模型后端

1. 保持统一 `complete()` 接口。
2. 接 Ollama。
3. 接 OpenAI-compatible `/responses`。
4. 接 DeepSeek `/chat/completions`。
5. 统一 usage/cache metadata。

对应源码：`pico/providers/clients.py`、`pico/cli.py`。

## Phase 7：高级扩展

1. Skills：从内置 prompt profile 扩成文件化 `SKILL.md`。
2. MCP：外部工具发现后合入工具池。
3. Context compact：大工具结果落盘，旧 history 摘要化。
4. Evaluation：跑 benchmark 验证 harness 改动。
5. Dashboard：让 run 证据可视化。

## 最小 Definition of Done

一个从 0 构建的 Pico，至少应该满足：

- `FakeModelClient` 能跑完整 loop 测试。
- 文件工具不能访问 workspace 外。
- risky 工具默认需要审批。
- 每次 run 有 task_state、trace、report。
- prompt metadata 能解释上下文如何组装。
- memory 能记录最近文件和短摘要。
- checkpoint 能检测关键文件变化。
- provider 差异不泄漏到 `AgentLoop`。

## 推荐测试顺序

```bash
python -m pytest examples/mini-pico/tests
python -m pytest tests/test_agent_loop.py tests/test_tools.py tests/test_tool_executor.py
python -m pytest tests/test_context_manager.py tests/test_memory.py tests/test_checkpoint.py
python -m pytest tests/test_public_api_contract.py tests/test_dashboard.py tests/test_evaluator.py
```

## 继续演进

如果你接下来要把 Pico 做成更像 Claude Code 的完整 harness，优先顺序建议是：

1. 文件化 skill：最容易落地，收益直接。
2. MCP mock：先打通动态工具池，不急着接真实 transport。
3. 大工具结果落盘：解决上下文膨胀。
4. Memory side-query：比关键词召回更准，但仍可解释。
5. Worktree isolation：并行子任务之前再做。
