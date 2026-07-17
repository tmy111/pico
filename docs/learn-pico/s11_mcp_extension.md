# s11 - MCP Extension：把外部能力接进同一个工具池

> 目标：设计 Pico 的 MCP 扩展路线。MCP 不应该改 agent loop，而应该扩展工具池。

## 目标形态

参考 learn-claude-code 的设计，MCP 工具进入 Pico 后应当和内置工具一样：

```text
BUILTIN_TOOLS
  + discovered MCP tools
  -> assemble_tool_pool()
  -> prompt prefix / tool signature
  -> ToolExecutor
  -> trace / report
```

工具命名建议：

```text
mcp__{server}__{tool}
```

例如：

```text
mcp__docs__search
mcp__github__get_issue
mcp__deploy__status
```

## 从 0 实现的最小 MCP

第一版可以先 mock，不接真实 JSON-RPC：

```python
class MCPClient:
    def __init__(self, name):
        self.name = name
        self.tools = []
        self.handlers = {}

    def call_tool(self, tool_name, args):
        return self.handlers[tool_name](**args)
```

然后增加：

```python
def connect_mcp(name): ...
def assemble_tool_pool(): ...
def normalize_mcp_name(name): ...
```

## Pico 落点

建议新增模块：

```text
pico/mcp.py
```

需要改动的位置：

- `Pico.__init__`：初始化 `self.mcp_clients = {}`。
- `Pico.build_tools()`：从 `tools.py` 的内置工具 + MCP discovered tools 组装。
- `tools.py`：新增 `connect_mcp` 工具规格。
- `ToolExecutor`：识别 `mcp__` 工具，走 MCP call。
- `prompt_prefix.py`：工具签名包含 MCP schema。
- `checkpoint.py`：runtime_identity 加入 connected MCP servers。

## 权限策略

MCP 工具应该带 annotations：

```python
{
    "readOnlyHint": True,
    "destructiveHint": False,
}
```

映射到 Pico：

- read-only MCP 工具：默认 low risk。
- destructive MCP 工具：需要 approval。
- 未声明风险的 MCP 工具：保守视为 risky。

## 测试清单

1. 连接 mock docs server 后，prompt prefix 出现 `mcp__docs__search`。
2. 两个 server 都有 `search` 时，命名不冲突。
3. server/tool 名里的特殊字符会被规范化。
4. destructive MCP tool 在 `approval=never` 下被拒绝。
5. checkpoint 的 `tool_signature` 会因 MCP 工具变化而变化。

## 练习

先做 mock server：

```text
docs.search(query) -> "[docs] ..."
docs.get_version() -> "v1"
```

再把真实 MCP transport 放进 `MCPClient` 内部。这样 agent loop 不需要知道 transport 细节。
