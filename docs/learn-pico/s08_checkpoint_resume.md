# s08 - Checkpoint / Resume：让长任务能接着走

> 目标：保存恢复点，并判断恢复时上下文是否仍然可信。

## Checkpoint 解决什么

session history 能保存对话，但长任务恢复时还需要知道：

- 当前目标是什么？
- 已完成什么？
- 下一步是什么？
- 哪些关键文件参与过？
- 这些文件恢复时有没有变？
- runtime 配置有没有变？

这些由 `pico/checkpoint.py` 负责。

## Checkpoint 内容

`create_checkpoint()` 会保存：

```text
checkpoint_id
parent_checkpoint_id
schema_version
current_goal
completed
current_blocker
next_step
key_files + freshness hash
runtime_identity
summary
```

其中 `runtime_identity` 包括：

- cwd
- model / model_client
- approval_policy
- read_only
- max_steps / max_new_tokens
- feature_flags
- active_skill
- workspace_fingerprint
- tool_signature

## Resume 状态

`evaluate_resume_state()` 可能返回：

```text
no-checkpoint
full-valid
partial-stale
workspace-mismatch
schema-mismatch
```

如果关键文件 hash 变了，就是 `partial-stale`。如果工具签名、模型、工作区等运行指纹变了，就是 `workspace-mismatch`。

## 从 0 实现

第一版可以只做：

1. 每次工具执行后保存最近文件和当前目标。
2. 每次 run 结束保存 final answer。
3. 恢复时检查最近文件 hash。
4. 把 checkpoint 摘要注入下一轮 prompt。

## Pico 源码对应

- `pico/checkpoint.py`
- `Pico.create_checkpoint()`
- `Pico.render_checkpoint_text()`
- `ContextManager.build()` 会把 checkpoint 文本追加到 prefix。

## 练习

1. 运行 `python -m pytest tests/test_checkpoint.py tests/test_session_store.py`
2. 创建一次 session，修改关键文件，再 `--resume latest`，观察 resume status。
3. 给 checkpoint 增加 `last_error` 字段，帮助从模型错误恢复。
