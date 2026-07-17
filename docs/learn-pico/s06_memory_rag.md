# s06 - Memory / RAG：让上下文有层次

> 目标：实现工作记忆、长期记忆和相关召回。Pico 当前是透明关键词召回，不依赖 embedding。

## 三层记忆

Pico 当前有三种“记忆”：

| 层 | 存在哪里 | 用途 |
| --- | --- | --- |
| history | session json | 完整对话和工具结果 |
| working memory | session `memory` | 当前任务、最近文件、文件短摘要、过程笔记 |
| durable memory | `.pico/memory/` | 跨会话事实、偏好、项目约定 |

对应源码：`pico/features/memory.py`。

## 工作记忆怎么来

工具执行后，`Pico.update_memory_after_tool()` 会挑选高价值信息：

- `read_file`：记录最近文件，生成文件摘要。
- `write_file` / `patch_file`：让旧文件摘要失效。
- 失败或部分成功：写一条 process note。

这不是完整记录，完整记录在 history。memory 只保存下一轮决策最可能用到的压缩事实。

## 相关召回怎么做

当前实现是透明排序：

1. 把用户请求分词。
2. 对 episodic notes 和 durable notes 分词。
3. 按 tag 命中、关键词重叠、时间排序。
4. 取前 `RELEVANT_MEMORY_LIMIT=3` 条放进 prompt。

这在 `ContextManager._render_relevant_memory()` 里渲染。

## 长期记忆

用户明确说“记住/保存/记录”时，`Pico.promote_durable_memory()` 会从最终答案里识别这些格式：

```text
Project convention: ...
Decision: ...
Dependency: ...
Preference: ...
项目约定：...
决策：...
依赖：...
偏好：...
```

通过过滤后，默认不会立刻写入长期记忆，而是进入待确认队列：

```text
/memory pending      查看候选
/memory save all     确认保存
/memory drop all     丢弃候选
```

确认后写入：

```text
.pico/memory/MEMORY.md
.pico/memory/topics/project-conventions.md
.pico/memory/topics/key-decisions.md
.pico/memory/topics/dependency-facts.md
.pico/memory/topics/user-preferences.md
```

CLI 通过 `--memory-save ask|auto|never` 控制策略：`ask` 是默认确认流，`auto` 保持旧的自动写入行为，`never` 禁用长期记忆写入。

## 和传统 RAG 的关系

Pico 当前这层更像“可解释 memory RAG”：

- 优点：简单、可测试、可审计、不需要向量库。
- 缺点：语义召回弱，长文档检索能力有限。

下一步可以在不改主 loop 的情况下加 embedding：

```text
DurableMemoryStore
  -> index markdown notes
  -> optional vector index
  -> retrieval_candidates(query)
```

也就是说，扩展点仍然是 `retrieval_candidates()`，不是 agent loop。

## 练习

1. 运行 `python -m pytest tests/test_memory.py tests/test_context_manager.py`
2. 增加一个 durable topic，比如 `architecture-notes`。
3. 把 `retrieval_candidates()` 换成“关键词 + embedding fallback”的双路召回。
