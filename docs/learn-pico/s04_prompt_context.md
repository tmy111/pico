# s04 - Prompt + Context：把该看的放进去，把噪音挡在外面

> 目标：实现稳定 prompt prefix、动态历史、工作记忆和上下文预算。

## Pico 的 prompt 分层

正式 Pico 的 prompt 由 `pico/context_manager.py` 组装：

```text
prefix           稳定规则、工具说明、workspace 摘要、active skill
memory           当前任务、最近文件、文件摘要、长期记忆主题
relevant_memory  和当前请求相关的少量笔记
history          最近对话与工具结果，旧内容会压缩
current_request  当前用户请求，永不裁剪
```

这个结构对应 `SECTION_ORDER`：

```python
("prefix", "memory", "relevant_memory", "history", "current_request")
```

## 从 0 实现

mini 版可以先不做预算，只拼一整段：

```python
prompt = f"""
Rules...

Tools:
{tool_signature()}

{workspace.snapshot_text()}

Transcript:
{render_history(history)}

Current request:
{user_message}
"""
```

等 loop 跑通后，再加预算：

1. 给每个 section 一个字符预算。
2. prompt 超预算时，按固定顺序缩小 section。
3. 当前请求不裁剪。
4. 旧工具结果优先摘要，最近工具结果优先保留。

## Pico 源码对应

- 稳定 prefix：`pico/prompt_prefix.py`
- prompt 预算：`pico/context_manager.py`
- 工作区摘要：`pico/workspace.py`
- prompt metadata：`Pico._build_prompt_and_metadata()`

`prompt_prefix.py` 还会给 prefix 算 hash。这个 hash 有两个用途：

- 判断 prefix 是否变化。
- 给支持 prompt cache 的 provider 当 cache key。

## 设计要点

1. 稳定内容放前面，动态内容放后面。
2. 工具说明和 workspace 摘要属于 prefix，尽量可缓存。
3. history 属于动态内容，不适合作为 cache key。
4. metadata 要记录每段 raw/rendered 长度，方便调试 prompt 为什么变短。

## 练习

1. 运行 `python -m pytest tests/test_context_manager.py tests/test_prompt_prefix.py`
2. 调小 `DEFAULT_TOTAL_BUDGET`，观察 `budget_reductions`。
3. 增加一个新的 section，比如 `runtime_notice`，并写入 metadata。
