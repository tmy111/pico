# pico

`pico` 是一个轻量级的本地 coding agent harness。它把模型客户端、仓库上下文、受控工具、会话状态、运行轨迹、记忆和 checkpoint 组合在一起，用来执行可复盘的工程任务。

它适合做代码排查、仓库结构梳理、测试修复、小步文件修改、运行记录审计，以及学习一个 coding agent 从最小循环到生产化运行时的完整构成。

## 核心能力

- 本地 CLI：`pico`
- Python 模块入口：`python -m pico`
- 本地可视化工作台：`pico-viewer`
- 受控工具白名单：列文件、读文件、搜索、执行 shell、写文件、补丁替换、只读子 agent 调查
- 会话和运行工件落盘：`.pico/sessions/`、`.pico/runs/<run_id>/`
- checkpoint / resume：记录恢复所需的任务状态、运行身份和工作区指纹
- 分层记忆：history、working memory、durable memory
- skill 扩展：内置 `repo-map`，用于仓库结构和执行流梳理
- provider 适配：`deepseek`、`openai`、`ollama`
- evaluation / benchmark 支持：指标、ablation、dashboard 复盘

## 安装

推荐使用 `uv` 在仓库根目录运行：

```bash
uv sync --dev
```

也可以用普通 editable install：

```bash
python -m pip install -e .
```

项目要求 Python 3.10 或更高版本。

## 快速开始

进入交互式模式：

```bash
uv run pico
```

执行一次性任务：

```bash
uv run pico "summarize this repository"
```

指定工作目录：

```bash
uv run pico --cwd path/to/repo "find likely test failures"
```

恢复最近一次 session：

```bash
uv run pico --resume latest
```

启用内置 skill：

```bash
uv run pico --skill repo-map "map this repository"
```

## Provider 配置

provider 选择优先级：

```text
--provider > PICO_PROVIDER > deepseek
```

默认 provider 是 `deepseek`。`pico` 会自动读取项目向上查找到的 `.env` 文件，并把其中的变量加载到当前进程。

### DeepSeek

```bash
PICO_PROVIDER=deepseek
PICO_DEEPSEEK_API_KEY="your-api-key"
PICO_DEEPSEEK_API_BASE="https://api.deepseek.com"
PICO_DEEPSEEK_MODEL="deepseek-v4-pro"
```

运行：

```bash
uv run pico --provider deepseek
```

### OpenAI-compatible

```bash
PICO_PROVIDER=openai
PICO_OPENAI_API_KEY="your-api-key"
PICO_OPENAI_API_BASE="https://www.right.codes/codex/v1"
PICO_OPENAI_MODEL="gpt-5.4"
```

运行：

```bash
uv run pico --provider openai
```

`openai` provider 使用 `/responses` 接口，并在支持的后端上启用 prompt cache 元数据记录。

### Ollama

先启动本地服务并准备模型：

```bash
ollama serve
ollama pull qwen3.5:4b
```

运行：

```bash
uv run pico --provider ollama --model qwen3.5:4b
```

默认 Ollama host 是 `http://127.0.0.1:11434`。

## 常用 CLI 参数

```bash
uv run pico --help
uv run pico --provider deepseek
uv run pico --provider openai --model gpt-5.4
uv run pico --provider ollama --model qwen3.5:4b
uv run pico --approval auto
uv run pico --max-steps 20 --max-new-tokens 4096
```

交互式命令：

```text
/help     查看帮助
/skills   列出或选择 skill
/memory   查看当前工作记忆
/session  输出当前 session 文件路径
/reset    清空当前 session 的历史和记忆
/exit     退出
```

## 本地可视化工作台

启动 dashboard：

```bash
uv run pico-viewer --cwd .
```

默认地址：

```text
http://127.0.0.1:8765/
```

工作台会读取当前工作区下的 `.pico/runs`、`.pico/sessions`、`benchmarks/results` 和 `assets`，展示 run 列表、流程事件、trace、report、session 预览和 benchmark 结果。也可以通过页面提交新任务：

```bash
uv run pico-viewer --cwd . --provider deepseek --approval never
```

如需自动打开浏览器：

```bash
uv run pico-viewer --cwd . --open
```

## 运行工件

每次 `ask()` 运行会在 `.pico/runs/<run_id>/` 下写入可复盘工件：

```text
task_state.json
trace.jsonl
report.json
```

session 会保存在：

```text
.pico/sessions/<session_id>.json
```

这些文件用于恢复任务、排查失败、观察工具调用过程，以及给 dashboard 和 benchmark 分析使用。

## 工具边界

模型不能直接访问文件系统或 shell，只能请求 runtime 暴露的工具：

| 工具 | 用途 | 是否高风险 |
| --- | --- | --- |
| `list_files` | 列出工作区文件 | 否 |
| `read_file` | 按行读取 UTF-8 文件 | 否 |
| `search` | 在工作区内搜索文本 | 否 |
| `run_shell` | 在仓库根目录执行 shell 命令 | 是 |
| `write_file` | 写入文本文件 | 是 |
| `patch_file` | 精确替换一个文本块 | 是 |
| `delegate` | 启动受限只读子 agent 调查 | 否 |

所有路径都会被限制在工作区内。高风险工具会经过 approval policy 控制：

```text
ask    执行前询问
auto   自动允许
never  拒绝高风险工具
```

## 项目结构

```text
pico/
  cli.py                  # CLI 参数解析、provider 选择、runtime 装配
  runtime.py              # Pico runtime facade，协调工具、记忆、session 和 checkpoint
  agent_loop.py           # 主 agent loop
  tools.py                # 工具规格、校验和实现
  tool_executor.py        # 工具执行护栏
  context_manager.py      # prompt 上下文预算、记忆和历史拼装
  checkpoint.py           # checkpoint / resume 逻辑
  run_store.py            # run 工件写入
  session_store.py        # session 存取
  dashboard.py            # 本地 dashboard 服务
  dashboard_frontend.py   # dashboard 前端 HTML
  providers/clients.py    # DeepSeek、OpenAI-compatible、Ollama 客户端
  features/memory.py      # 分层记忆
  evaluation/             # benchmark 和指标
  skills/                 # 内置 skill

docs/learn-pico/          # 从 0 构建 pico 的教程
examples/mini-pico/       # 教学用最小实现
tests/                    # 单元测试和契约测试
benchmarks/               # benchmark 任务与结果
```

## 开发命令

运行测试：

```bash
python -m pytest
```

只跑 mini-pico 教学实现测试：

```bash
python -m pytest examples/mini-pico/tests
```

语法检查：

```bash
python -m py_compile pico\cli.py pico\providers\clients.py
```

查看包入口是否可用：

```bash
uv run pico --help
uv run pico-viewer --help
```

## Python API

```python
from pico import Pico, SessionStore, WorkspaceContext, build_arg_parser, build_agent

args = build_arg_parser().parse_args(["--cwd", ".", "--approval", "auto"])
agent = build_agent(args)

answer = agent.ask("summarize this repository")
print(answer)
```

测试中可以使用 `FakeModelClient` 构造无网络的确定性 agent loop。

## 学习路径

- 先读 `examples/mini-pico/`：理解最小 agent loop、工具、workspace 和上下文拼装。
- 再读 `docs/learn-pico/`：按章节理解 guardrails、memory、checkpoint、provider、dashboard 和 evaluation。
- 最后读 `pico/`：看正式 runtime 如何把同一套机制生产化。
