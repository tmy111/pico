# s07 - Skills：把重复工作流做成可激活的 prompt profile

> 目标：理解 Pico 当前 skill 设计，并规划成 learn-claude-code 风格的 `SKILL.md` 按需加载。

## Pico 当前 skill 是什么

当前实现位于 `pico/skills/`：

```text
pico/skills/__init__.py
pico/skills/repo_map.py
```

`Skill` 是一个轻量 prompt profile：

```python
@dataclass(frozen=True)
class Skill:
    name: str
    title: str
    description: str
    instructions: str
```

它不会增加工具，只会改变 prompt prefix，让模型采用特定工作流。

## 当前使用路径

CLI：

```bash
uv run pico --skill repo-map "map this repository"
```

REPL：

```text
/skills
/skills repo-map
/skills none
```

runtime：

- `Pico.set_skill()` 激活 skill。
- `Pico.build_prefix()` 把 active skill instructions 拼进 prefix。
- `prompt_metadata["active_skill"]` 记录当前 skill。

## 从 0 实现

最小版只需要：

```python
BUILTIN_SKILLS = {
    "repo-map": Skill(...),
}

def render_skill_list(active):
    ...

def set_skill(name):
    active_skill = require_skill(name)
    rebuild_prompt_prefix()
```

## 下一步：文件化 Skill

如果要更像 learn-claude-code，可以新增：

```text
.pico/skills/
  code-review/SKILL.md
  mcp-builder/SKILL.md
```

`SKILL.md`：

```markdown
---
name: code-review
description: Review code for bugs, regressions, and missing tests.
allowed-tools: read_file, search
---

Use this workflow...
```

推荐两级加载：

1. 启动时只扫描 `name / description`，放进 skill catalog。
2. 模型需要时调用 `load_skill(name)`，再把完整 `SKILL.md` 注入上下文。

落点：

- skill registry：扩展 `pico/skills/__init__.py`
- tool spec：新增 `load_skill`
- prompt prefix：只放 catalog，不放所有正文
- ContextManager：把 loaded skill 内容作为动态 section 或 tool result

## 练习

1. 运行 `python -m pytest tests/test_allowed_tools.py tests/test_prompt_prefix.py`
2. 新增一个内置 skill：`test-fixer`。
3. 设计 `load_skill` 工具，但先只返回内置 skill 的 instructions。
