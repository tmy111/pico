# s02 - Workspace + Tools：给模型一双受控的手

> 目标：实现工作区边界和最小工具集，让模型能看文件、搜代码、写补丁，但不能逃出仓库。

## 工具不是函数列表

在 agent harness 里，工具是能力白名单。每个工具至少要有：

- 给模型看的名字、描述、参数 schema。
- runtime 的参数校验。
- 真正执行的函数。
- 风险标记：只读还是需要审批。

Pico 当前工具在 `pico/tools.py`：

```text
list_files   只读，列目录
read_file    只读，按行读文件
search       只读，优先 rg 搜索
run_shell    risky，运行 shell
write_file   risky，写文件
patch_file   risky，精确替换
delegate     只读，启动受限子 agent
```

## 从 0 实现

第一步先做 `Workspace`：

```python
class Workspace:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def path(self, raw):
        candidate = (self.root / raw).resolve()
        candidate.relative_to(self.root)
        return candidate
```

关键点：所有文件路径都必须 `relative_to(root)` 成功，防止 `../` 或 symlink 逃逸。

第二步做工具规格表：

```python
TOOL_SPECS = {
    "read_file": {"risky": False, "schema": {"path": "str"}},
    "write_file": {"risky": True, "schema": {"path": "str", "content": "str"}},
}
```

第三步实现 `validate_tool()` 和 `run_tool()`。校验与执行分开，是为了在真正修改前就能拒绝错误参数。

## Pico 源码对应

- mini 版：`examples/mini-pico/mini_pico/tools.py`
- 正式版：`pico/tools.py`
- 路径锚定：`pico/runtime.py` 的 `Pico.path()`
- 工具上下文：`pico/tool_context.py`

正式版比 mini 多了这些边界：

- `read_file` 限制最大 1000 行。
- `patch_file` 要求 `old_text` 精确出现一次。
- `run_shell` 只能拿到过滤后的环境变量。
- `delegate` 受 `depth / max_depth` 限制，避免无限递归。

## 练习

1. 给 mini-pico 加一个 `get_file_info` 工具，返回大小和行数。
2. 写测试验证 `../secret.txt` 会被拒绝。
3. 对照 `tests/test_security.py` 和 `tests/test_tools.py`，补齐正式版安全边界理解。
