# Learn Pico - 从 0 构建一个本地 Coding Agent

这个目录是一套面向 `pico` 的 harness 教程，写法参考 `learn-claude-code`：每一章只增加一个机制，始终围绕一个稳定的 agent loop。

`pico` 的核心不是“写一个聪明的 agent”，而是给模型搭一个可控的本地工作环境：

```text
Pico = 模型客户端
     + 工作区感知
     + 受控工具
     + prompt / context 管理
     + session / run 工件
     + memory / checkpoint
     + CLI / dashboard / evaluation
```

## 学习路线

建议先读 `examples/mini-pico/`，它是教学骨架；再对照 `pico/`，看正式 runtime 如何把同一套设计生产化。

| 章节 | 主题 | 从 0 构建什么 |
| --- | --- | --- |
| [s01](./s01_agent_loop.md) | Agent Loop | 最小感知-决策-行动循环 |
| [s02](./s02_workspace_and_tools.md) | Workspace + Tools | 工作区边界、读文件、搜索、写文件 |
| [s03](./s03_tool_guardrails.md) | Tool Guardrails | 参数校验、审批、重复调用拦截 |
| [s04](./s04_prompt_context.md) | Prompt + Context | 稳定前缀、历史、预算裁剪 |
| [s05](./s05_state_trace.md) | State + Trace | session、task_state、trace、report |
| [s06](./s06_memory_rag.md) | Memory / RAG | 工作记忆、长期记忆、相关召回 |
| [s07](./s07_skills.md) | Skills | prompt profile 与文件化 skill 扩展 |
| [s08](./s08_checkpoint_resume.md) | Checkpoint / Resume | 恢复点、文件新鲜度、运行指纹 |
| [s09](./s09_providers_cache.md) | Providers + Cache | DeepSeek/OpenAI/Ollama 适配与 prefix cache |
| [s10](./s10_dashboard_evaluation.md) | Dashboard + Eval | 本地可视化、基准任务、指标 |
| [s11](./s11_mcp_extension.md) | MCP Extension | 把外部能力并入同一个工具池 |
| [s12](./s12_comprehensive_build.md) | Comprehensive Build | 从 mini-pico 走到完整 pico 的实现清单 |

## 读源码顺序

```text
examples/mini-pico/
  mini_pico/agent_loop.py       # 最小循环
  mini_pico/tools.py            # 最小工具白名单
  mini_pico/context_manager.py  # 最小 prompt 组装
  tests/test_agent_loop.py      # 一条完整工具调用路径

pico/
  runtime.py                    # 正式 runtime facade
  agent_loop.py                 # 生产化控制循环
  tools.py                      # 工具规格与实现
  tool_executor.py              # 工具执行护栏
  context_manager.py            # 上下文预算与相关记忆
  features/memory.py            # 工作记忆 + 长期记忆
  prompt_prefix.py              # 稳定 prompt prefix
  checkpoint.py                 # checkpoint / resume
  providers/clients.py          # 模型后端适配
  run_store.py                  # run 工件落盘
```

## 核心原则

1. 主循环保持稳定：新增能力尽量接在 prompt 组装、工具池、工具执行前后、run 工件里。
2. 工具是动作边界：模型只能申请工具，真正执行必须经过 runtime。
3. 记忆分层：history 保存完整事件，working memory 保存短摘要，durable memory 保存跨会话事实。
4. 工件可复盘：每次 `ask()` 都应该能留下 task_state、trace、report。
5. 先做透明规则，再做智能召回：Pico 当前记忆召回用关键词和 tag，足够可解释；之后再升级 embedding/RAG。

## 最小运行方式

```bash
python -m pytest examples/mini-pico/tests
python -m pytest tests
uv run pico --help
uv run pico --skill repo-map "map this repository"
uv run pico-viewer --cwd .
```

## 和 learn-claude-code 的对应关系

| learn-claude-code 机制 | Pico 当前位置 | 下一步可扩展 |
| --- | --- | --- |
| Agent loop | `pico/agent_loop.py` | 保持主循环稳定 |
| Tools | `pico/tools.py` + `pico/tool_executor.py` | 增加 MCP 动态工具池 |
| Permission | `ToolExecutor` + `Pico.approve()` | 更细粒度策略、按工具注解审批 |
| Context compact | `ContextManager` section budgets | 工具结果落盘、摘要压缩 |
| Memory/RAG | `features/memory.py` | side-query / embedding 召回 |
| Skills | `pico/skills/` | 文件化 `SKILL.md`、按需加载 |
| Checkpoint | `checkpoint.py` | 跨分支/worktree 恢复 |
| Run artifacts | `run_store.py` | dashboard 和 benchmark 汇总 |
| MCP | 还未内置 | 见 [s11](./s11_mcp_extension.md) |
