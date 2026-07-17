# s09 - Providers + Cache：把后端差异关在适配层里

> 目标：让 runtime 只依赖 `complete()`，不用关心 DeepSeek、OpenAI-compatible、Ollama 的协议差异。

## 统一接口

Pico 的模型客户端都暴露：

```python
complete(prompt, max_new_tokens, **kwargs) -> str
```

runtime 只调用这个接口。HTTP 路径、响应解析、usage 字段、SSE 兼容、prompt cache 参数都留在 `pico/providers/clients.py`。

## 当前 provider

| provider | client | 路径 |
| --- | --- | --- |
| deepseek | `DeepSeekModelClient` | `/v1/chat/completions` |
| openai | `OpenAICompatibleModelClient` | `/v1/responses` |
| ollama | `OllamaModelClient` | `/api/generate` |
| test | `FakeModelClient` | 固定输出 |

CLI 装配在 `pico/cli.py` 的 `_build_model_client()`。

## Prompt Cache

Pico 的 cache 思路是：不要缓存整段 prompt，而是缓存稳定 prefix。

稳定 prefix hash 来自 `pico/prompt_prefix.py`：

```python
prefix_hash = sha256(prefix_text)
```

如果 provider 支持：

```python
model_client.complete(
    prompt,
    max_new_tokens,
    prompt_cache_key=prompt_metadata["prompt_cache_key"],
    prompt_cache_retention="in_memory",
)
```

当前 `OpenAICompatibleModelClient` 只在明确支持的 host 上启用。

## 从 0 实现

1. 先写 `FakeModelClient`，所有 loop 测试都用它。
2. 再接本地 Ollama，调试最方便。
3. 最后接 OpenAI-compatible / DeepSeek。
4. usage/cache metadata 统一放进 `last_completion_metadata`。

## 练习

1. 运行 `python -m pytest tests/test_public_api_contract.py tests/test_pico.py`
2. 写一个新的 mock provider，模拟 500 后重试。
3. 在 report 里观察 `cached_tokens` 和 `cache_hit`。
