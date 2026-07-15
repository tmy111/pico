# pico

`pico` 是一个轻量的本地 coding agent。它运行在当前仓库里，会读取工作区、调用受控工具、保存 session/run 状态，并把运行痕迹落到本地 `.pico/` 目录。

它适合做代码排查、仓库结构梳理、测试修复、小步文件修改，以及可复盘的一次性工程任务。

## 主要能力

- CLI 命令：`pico`
- 模块入口：`python -m pico`
- session 保存：`.pico/sessions/`
- run 保存：`.pico/runs/<run_id>/`
- 本地可视化：`pico-viewer`
- 支持的模型后端：`deepseek`、`openai`、`ollama`

## 快速开始

安装依赖后在仓库根目录运行：

```bash
uv run pico
```

默认 provider 是 `deepseek`。常规情况下只需要在 `.env` 里配置 DeepSeek key：

```bash
PICO_PROVIDER=deepseek
PICO_DEEPSEEK_API_KEY="your-api-key"
PICO_DEEPSEEK_API_BASE="https://api.deepseek.com"
PICO_DEEPSEEK_MODEL="deepseek-v4-pro"
```

如果要临时覆盖模型或接口地址：

```bash
uv run pico --model deepseek-v4-pro --base-url https://api.deepseek.com
```

DeepSeek 当前走 `/v1/chat/completions` 路径，项目里对应的是 `DeepSeekModelClient`。

## Provider 配置

Provider 选择优先级：

```text
--provider > PICO_PROVIDER > deepseek
```

可用 provider：

| provider | base URL | API key | model |
| --- | --- | --- | --- |
| `deepseek` | `PICO_DEEPSEEK_API_BASE`，回退 `DEEPSEEK_API_BASE`，默认 `https://api.deepseek.com` | `PICO_DEEPSEEK_API_KEY`，回退 `DEEPSEEK_API_KEY` | `PICO_DEEPSEEK_MODEL`，回退 `DEEPSEEK_MODEL`，默认 `deepseek-v4-pro` |
| `openai` | `PICO_OPENAI_API_BASE`，回退 `OPENAI_API_BASE`，默认 `https://www.right.codes/codex/v1` | `PICO_OPENAI_API_KEY`，回退 `OPENAI_API_KEY`、`PICO_RIGHT_CODES_API_KEY`、`RIGHT_CODES_API_KEY` | `PICO_OPENAI_MODEL`，回退 `OPENAI_MODEL`，默认 `gpt-5.4` |
| `ollama` | `--host`，默认 `http://127.0.0.1:11434` | 不需要 | `--model`，默认 `qwen3.5:4b` |

OpenAI-compatible 服务示例：

```bash
uv run pico --provider openai
```

本地 Ollama 示例：

```bash
ollama serve
ollama pull qwen3.5:4b
uv run pico --provider ollama --model qwen3.5:4b
```

## 本地可视化页面

启动只读 dashboard：

```bash
uv run pico-viewer --workspace .
```

页面会读取当前工作区下的 `.pico/runs`、`.pico/sessions`、`benchmarks/results` 和截图摘要，方便查看 run 列表、流程图、trace 时间线和 report。

如果只想打开静态页面，可以直接查看：

```text
pico-local-viewer.html
```

## 常用命令

```bash
uv run pico --help
uv run pico --provider deepseek
uv run pico --provider openai
uv run pico --provider ollama --model qwen3.5:4b
```

运行测试：

```bash
python -m pytest
```

语法检查：

```bash
python -m py_compile pico\cli.py pico\providers\clients.py
```
