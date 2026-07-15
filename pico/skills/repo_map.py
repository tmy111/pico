"""Repo-map skill definition."""

NAME = "repo-map"
TITLE = "Repository map"
DESCRIPTION = "Map a repository's structure, major files, functions, methods, and execution flow."

INSTRUCTIONS = """\
Active skill: repo-map

Use this workflow when the user asks to understand, summarize, or document a repository:
- Start from the repository surface: README, pyproject/package/config files, entrypoints, and top-level directories.
- Prefer list_files and search to build a file inventory before using read_file.
- Use read_file selectively for entrypoints, core modules, and files that search results show are central. Do not try to read every file in a large repository.
- Do not reread the same file range. If you already inspected a file, use the remembered evidence unless you need a clearly new line range.
- When the tool budget is half spent, switch from broad discovery to targeted confirmation. When the budget is nearly spent, stop reading and prepare the final repository map.
- Focus on production/source files first. Treat tests, generated artifacts, benchmark results, screenshots, and docs as supporting context unless the user asks for them.
- Summarize functions and methods as `name: logic`, keeping the logic concrete enough that another engineer can navigate the code quickly.
- Preserve module boundaries. Group the final answer by file or package, not by a loose global list.
- Call out the main execution flow, extension points, and any unclear areas you did not inspect.
- If the user asks you to write the map to a file and the path is clear, create or update that file instead of only describing the map in chat.
- Do not invent files, function names, dependencies, or behavior that did not appear in tool results.

Recommended final shape:
- Scope covered
- Repository overview
- Main files and responsibilities
- Functions/methods as name + logic
- Execution flow
- Extension points or follow-up reading
"""
