"""Local browser workbench for Pico artifacts and task runs."""

from __future__ import annotations

import argparse
import json
import mimetypes
import posixpath
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


try:
    from .dashboard_frontend import INDEX_HTML as WORKBENCH_HTML
except ImportError:  # pragma: no cover - supports direct script execution.
    from dashboard_frontend import INDEX_HTML as WORKBENCH_HTML

INDEX_HTML = WORKBENCH_HTML

TEST_STEPS = [
    {
        "id": "start",
        "event": "run_started",
        "title": "接收任务",
        "detail": "记录用户请求并创建 run/task 状态。",
    },
    {
        "id": "prompt",
        "event": "prompt_built",
        "title": "构建上下文",
        "detail": "刷新工作区、记忆、历史和恢复状态，生成模型 prompt。",
    },
    {
        "id": "model",
        "event": "model_requested",
        "title": "请求模型",
        "detail": "让模型决定下一步是工具调用、重试还是最终答案。",
    },
    {
        "id": "parse",
        "event": "model_parsed",
        "title": "解析输出",
        "detail": "把模型文本解析成受控的 tool/final/retry 动作。",
    },
    {
        "id": "tool",
        "event": "tool_executed",
        "title": "执行工具",
        "detail": "校验参数、审批风险工具、执行并写入 trace。",
    },
    {
        "id": "checkpoint",
        "event": "checkpoint_created",
        "title": "保存检查点",
        "detail": "记录恢复所需的目标、进度、阻塞点和工作区指纹。",
    },
    {
        "id": "finish",
        "event": "run_finished",
        "title": "完成报告",
        "detail": "写入 task_state、trace 和 report，供前端复盘。",
    },
]


class DashboardTaskRunner:
    def __init__(self, agent_factory, runtime_options=None):
        self._agent_factory = agent_factory
        self._runtime_options = dict(runtime_options or {})
        self.agent = None
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._current = {
            "status": "idle",
            "phase": "",
            "prompt": "",
            "run_id": "",
            "answer": "",
            "error": "",
        }
        self._sequence = 0

    def _agent_metadata(self) -> dict:
        agent = self.agent
        if agent is None:
            return {
                "initialized": False,
                "approval": str(self._runtime_options.get("approval", "")),
                "model": str(self._runtime_options.get("model", "")),
                "provider": str(self._runtime_options.get("provider", "")),
            }
        return {
            "initialized": True,
            "approval": getattr(agent, "approval_policy", ""),
            "model": getattr(getattr(agent, "model_client", None), "model", ""),
            "provider": type(getattr(agent, "model_client", None)).__name__.replace("ModelClient", ""),
        }

    def snapshot(self) -> dict:
        with self._lock:
            current = dict(self._current)
            running = bool(self._thread and self._thread.is_alive())
            agent = self.agent
        task_state = getattr(agent, "current_task_state", None)
        if task_state is not None and current.get("status") == "running":
            current["run_id"] = getattr(task_state, "run_id", current.get("run_id", ""))
            current["task_status"] = getattr(task_state, "status", "")
        current["busy"] = running
        current.update(self._agent_metadata())
        return current

    def start(self, prompt: str) -> dict:
        prompt = str(prompt or "").strip()
        if not prompt:
            raise ValueError("prompt must not be empty")
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("another task is already running")
            self._sequence += 1
            sequence = self._sequence
            self._current = {
                "status": "running",
                "phase": "initializing" if self.agent is None else "running",
                "prompt": prompt,
                "run_id": "",
                "answer": "",
                "error": "",
            }
            self._thread = threading.Thread(target=self._run, args=(sequence, prompt), daemon=True)
            self._thread.start()
        return self.snapshot()

    def _run(self, sequence: int, prompt: str) -> None:
        try:
            agent = self.agent
            if agent is None:
                agent = self._agent_factory()
                with self._lock:
                    self.agent = agent
                    if sequence == self._sequence:
                        self._current["phase"] = "running"
            answer = agent.ask(prompt)
            task_state = getattr(agent, "current_task_state", None)
            run_id = getattr(task_state, "run_id", "")
            task_status = getattr(task_state, "status", "completed")
            status = "completed" if task_status == "completed" else "failed"
            update = {
                "status": status,
                "phase": "",
                "prompt": prompt,
                "run_id": run_id,
                "answer": answer,
                "error": "",
                "task_status": task_status,
            }
        except Exception as exc:  # pragma: no cover - defensive around unexpected runtime failures.
            update = {
                "status": "failed",
                "phase": "",
                "prompt": prompt,
                "run_id": "",
                "answer": "",
                "error": str(exc),
            }
        with self._lock:
            if sequence == self._sequence:
                self._current.update(update)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _read_trace(path: Path) -> list[dict]:
    events: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return events
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = {"event": "unparsed", "raw": line}
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _clip(value: object, limit: int = 500) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _flow_detail(event: dict) -> str:
    name = str(event.get("event") or "")
    if name == "run_started":
        return _clip(event.get("user_request"), 220)
    if name == "prompt_built":
        metadata = event.get("prompt_metadata") or {}
        parts = []
        if metadata.get("prompt_chars") is not None:
            parts.append(f"prompt {metadata.get('prompt_chars')} chars")
        if metadata.get("resume_status"):
            parts.append(f"resume {metadata.get('resume_status')}")
        if metadata.get("budget_reductions"):
            parts.append("context reduced")
        return ", ".join(parts) or "Prompt assembled for the model."
    if name == "model_requested":
        return f"attempt {event.get('attempts', '-')}, tool steps {event.get('tool_steps', '-')}"
    if name == "model_parsed":
        return f"model output parsed as {event.get('kind', '-')}"
    if name == "tool_executed":
        return f"{event.get('name', '-')}: {_clip(event.get('result'), 180)}"
    if name == "checkpoint_created":
        return f"{event.get('checkpoint_id', '-')}, trigger {event.get('trigger', '-')}"
    if name == "runtime_identity_mismatch":
        return f"fields: {', '.join(str(item) for item in event.get('fields', []))}"
    if name == "run_finished":
        return f"{event.get('status', '-')}, {event.get('stop_reason', '-')}"
    return _clip(json.dumps(event, ensure_ascii=False, sort_keys=True), 220)


def _flow_title(event: dict) -> str:
    titles = {
        "run_started": "收到任务",
        "prompt_built": "构建上下文",
        "model_requested": "请求模型",
        "model_parsed": "解析模型输出",
        "tool_executed": "执行工具",
        "checkpoint_created": "保存检查点",
        "runtime_identity_mismatch": "检测到工作区漂移",
        "run_finished": "运行结束",
        "unparsed": "未解析事件",
    }
    name = str(event.get("event") or "event")
    if name == "tool_executed" and event.get("name"):
        return f"执行工具：{event.get('name')}"
    return titles.get(name, name)


def _build_flow(trace: list[dict], task_state: dict, report: dict) -> list[dict]:
    if not trace:
        status = report.get("status") or task_state.get("status")
        user_request = report.get("user_request") or task_state.get("user_request")
        if not user_request and not status:
            return []
        return [
            {"kind": "run_started", "title": "收到任务", "detail": _clip(user_request, 220)},
            {
                "kind": "run_finished",
                "title": "运行状态",
                "detail": f"{status or 'unknown'}, {report.get('stop_reason') or task_state.get('stop_reason') or '-'}",
            },
        ]
    flow = []
    for event in trace:
        name = str(event.get("event") or "event")
        flow.append({"kind": name, "title": _flow_title(event), "detail": _flow_detail(event)})
    return flow


def _load_runs(workspace_root: Path) -> list[dict]:
    runs_root = workspace_root / ".pico" / "runs"
    if not runs_root.exists():
        return []
    runs: list[dict] = []
    for run_dir in sorted((path for path in runs_root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True):
        task_state = _read_json(run_dir / "task_state.json")
        report_path = run_dir / "report.json"
        report = _read_json(report_path)
        trace = _read_trace(run_dir / "trace.jsonl")
        run_id = str(report.get("run_id") or task_state.get("run_id") or run_dir.name)
        raw_status = str(report.get("status") or task_state.get("status") or "")
        has_report = report_path.exists()
        status = raw_status
        stop_reason = str(report.get("stop_reason") or task_state.get("stop_reason") or "")
        if raw_status == "running" and not has_report:
            status = "interrupted"
            stop_reason = "missing_report"
        runs.append(
            {
                "run_id": run_id,
                "path": _relative(run_dir, workspace_root),
                "updated_at": run_dir.stat().st_mtime,
                "status": status,
                "raw_status": raw_status,
                "has_report": has_report,
                "user_request": report.get("user_request") or task_state.get("user_request") or "",
                "tool_steps": int(report.get("tool_steps", task_state.get("tool_steps", 0)) or 0),
                "attempts": int(report.get("attempts", task_state.get("attempts", 0)) or 0),
                "last_tool": report.get("last_tool") or task_state.get("last_tool") or "",
                "stop_reason": stop_reason,
                "final_answer": report.get("final_answer") or task_state.get("final_answer") or "",
                "checkpoint_id": report.get("checkpoint_id") or task_state.get("checkpoint_id") or "",
                "resume_status": report.get("resume_status") or task_state.get("resume_status") or "",
                "task_state": task_state,
                "report": report,
                "trace": trace,
                "flow": _build_flow(trace, task_state, report),
            }
        )
    return runs


def _session_history_preview(history: list[object]) -> list[dict]:
    messages: list[dict] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "message")
        message = {
            "role": role,
            "content": _clip(item.get("content"), 4000),
            "created_at": str(item.get("created_at") or ""),
        }
        if role == "tool":
            message["name"] = str(item.get("name") or "tool")
            message["args"] = item.get("args") if isinstance(item.get("args"), dict) else {}
        messages.append(message)
    return messages


def _load_sessions(workspace_root: Path) -> list[dict]:
    sessions_root = workspace_root / ".pico" / "sessions"
    if not sessions_root.exists():
        return []
    sessions: list[dict] = []
    for path in sorted(sessions_root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _read_json(path)
        history = payload.get("history") if isinstance(payload.get("history"), list) else []
        memory = payload.get("memory") if isinstance(payload.get("memory"), dict) else {}
        notes = memory.get("notes") if isinstance(memory.get("notes"), list) else []
        checkpoints = payload.get("checkpoints") if isinstance(payload.get("checkpoints"), dict) else {}
        checkpoint_items = checkpoints.get("items") if isinstance(checkpoints.get("items"), dict) else {}
        last_message = history[-1] if history else {}
        last_text = ""
        if isinstance(last_message, dict):
            last_text = f"{last_message.get('role', 'message')}: {last_message.get('content', '')}"
        sessions.append(
            {
                "id": str(payload.get("id") or path.stem),
                "path": _relative(path, workspace_root),
                "cwd": payload.get("cwd") or "",
                "updated_at": path.stat().st_mtime,
                "message_count": len(history),
                "note_count": len(notes),
                "checkpoint_count": len(checkpoint_items),
                "last_message": _clip(last_text, 800),
                "history": _session_history_preview(history),
                "preview": {
                    "memory": memory,
                    "checkpoints": checkpoints,
                },
            }
        )
    return sessions


def _load_benchmarks(workspace_root: Path) -> list[dict]:
    results_root = workspace_root / "benchmarks" / "results"
    if not results_root.exists():
        return []
    artifacts: list[dict] = []
    for path in sorted(results_root.rglob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md"}:
            continue
        preview = ""
        kind = path.suffix.lower().lstrip(".")
        try:
            if path.suffix.lower() == ".json":
                preview = json.dumps(_read_json(path), ensure_ascii=False, indent=2)
            else:
                preview = path.read_text(encoding="utf-8")
        except OSError:
            preview = ""
        artifacts.append(
            {
                "name": path.name,
                "kind": kind,
                "path": _relative(path, workspace_root),
                "preview": _clip(preview, 3000),
            }
        )
    return artifacts[:30]


def collect_dashboard_state(workspace_root: Path) -> dict:
    workspace_root = workspace_root.resolve()
    runs = _load_runs(workspace_root)
    sessions = _load_sessions(workspace_root)
    benchmarks = _load_benchmarks(workspace_root)
    completed = sum(1 for run in runs if str(run.get("status")).lower() == "completed")
    summary = {
        "run_count": len(runs),
        "session_count": len(sessions),
        "benchmark_count": len(benchmarks),
        "success_rate": completed / len(runs) if runs else 0.0,
        "avg_tool_steps": sum(run["tool_steps"] for run in runs) / len(runs) if runs else 0.0,
        "avg_attempts": sum(run["attempts"] for run in runs) / len(runs) if runs else 0.0,
    }
    return {
        "workspace": {
            "root": str(workspace_root),
            "pico_root": str(workspace_root / ".pico"),
        },
        "summary": summary,
        "runs": runs,
        "sessions": sessions,
        "benchmarks": benchmarks,
        "test_steps": TEST_STEPS,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    workspace_root: Path
    runner: DashboardTaskRunner | None = None

    def log_message(self, format: str, *args: object) -> None:
        if sys.stderr is not None:
            sys.stderr.write("[pico-viewer] " + (format % args) + "\n")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_text(INDEX_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/state":
            payload = collect_dashboard_state(self.workspace_root)
            payload["runtime"] = self.runner.snapshot() if self.runner is not None else {"status": "read_only", "busy": False}
            self._send_json(payload)
            return
        if parsed.path.startswith("/assets/"):
            self._send_asset(parsed.path)
            return
        if parsed.path == "/api/run":
            query = parse_qs(parsed.query)
            run_id = query.get("id", [""])[0]
            run = next((item for item in _load_runs(self.workspace_root) if item["run_id"] == run_id), None)
            if run is None:
                self.send_error(HTTPStatus.NOT_FOUND, "run not found")
                return
            self._send_json(run)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/tasks":
            self.send_error(HTTPStatus.NOT_FOUND, "not found")
            return
        if self.runner is None:
            self._send_json({"error": "task runner is not configured"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
            return
        try:
            payload = self._read_json_body()
            result = self.runner.start(str(payload.get("prompt", "")))
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON body"}, status=HTTPStatus.BAD_REQUEST)
            return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        except RuntimeError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.CONFLICT)
            return
        self._send_json(result, status=HTTPStatus.ACCEPTED)

    def _send_text(self, text: str, content_type: str) -> None:
        payload = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0") or 0)
        if content_length <= 0:
            return {}
        if content_length > 65536:
            raise ValueError("request body is too large")
        raw = self.rfile.read(content_length).decode("utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_asset(self, raw_path: str) -> None:
        normalized = posixpath.normpath(unquote(raw_path).lstrip("/"))
        if normalized.startswith("../") or normalized == "..":
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid path")
            return
        path = (self.workspace_root / normalized).resolve()
        assets_root = (self.workspace_root / "assets").resolve()
        try:
            path.relative_to(assets_root)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN, "asset outside allowed root")
            return
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "asset not found")
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "max-age=60")
        self.end_headers()
        self.wfile.write(data)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local dashboard and browser task runner for Pico artifacts.")
    parser.add_argument("--cwd", default=".", help="Workspace root containing .pico.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    parser.add_argument("--open", action="store_true", help="Open the dashboard in the default browser.")
    parser.add_argument("--provider", choices=("ollama", "openai", "deepseek"), default=None, help="Model backend for browser-submitted tasks.")
    parser.add_argument("--model", default=None, help="Model name override for browser-submitted tasks.")
    parser.add_argument("--ollama-host", default="http://127.0.0.1:11434", help="Ollama server URL for browser-submitted tasks.")
    parser.add_argument("--base-url", default=None, help="Provider API base URL for deepseek or openai.")
    parser.add_argument("--ollama-timeout", type=int, default=300, help="Ollama request timeout in seconds.")
    parser.add_argument("--openai-timeout", type=int, default=300, help="OpenAI-compatible request timeout in seconds.")
    parser.add_argument("--approval", choices=("auto", "never"), default="never", help="Approval policy for risky tools from browser-submitted tasks.")
    parser.add_argument("--resume", default=None, help="Session id to resume or 'latest' for browser-submitted tasks.")
    parser.add_argument("--skill", default=None, help="Activate a built-in skill for browser-submitted tasks.")
    parser.add_argument("--secret-env-name", dest="secret_env_names", action="append", default=[], help="Extra environment variable names to redact.")
    parser.add_argument("--max-steps", type=int, default=15, help="Maximum tool/model iterations per browser-submitted task.")
    parser.add_argument("--max-new-tokens", type=int, default=2048, help="Maximum model output tokens per step.")
    parser.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature sent to the provider.")
    parser.add_argument("--top-p", type=float, default=0.9, help="Top-p sampling value sent to Ollama.")
    return parser


def build_dashboard_agent(args: argparse.Namespace, workspace_root: Path):
    try:
        from .cli import build_agent as build_cli_agent
    except ImportError:  # pragma: no cover - supports direct script execution.
        from cli import build_agent as build_cli_agent

    agent_args = argparse.Namespace(
        cwd=str(workspace_root),
        provider=args.provider,
        model=args.model,
        host=args.ollama_host,
        base_url=args.base_url,
        ollama_timeout=args.ollama_timeout,
        openai_timeout=args.openai_timeout,
        resume=args.resume,
        skill=args.skill,
        approval=args.approval,
        secret_env_names=args.secret_env_names,
        max_steps=args.max_steps,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    return build_cli_agent(agent_args)


def _console_print(message: str, *, stream=None) -> None:
    stream = stream or sys.stdout
    if stream is not None:
        print(message, file=stream)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    workspace_root = Path(args.cwd).resolve()
    if not workspace_root.exists():
        _console_print(f"workspace does not exist: {workspace_root}", stream=sys.stderr)
        return 2

    class Handler(DashboardHandler):
        pass

    Handler.workspace_root = workspace_root
    Handler.runner = DashboardTaskRunner(
        lambda: build_dashboard_agent(args, workspace_root),
        runtime_options={
            "approval": args.approval,
            "model": args.model or "",
            "provider": args.provider or "default",
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{server.server_port}/"
    _console_print(f"Pico local viewer: {url}")
    _console_print(f"Workspace: {workspace_root}")
    _console_print("Press Ctrl+C to stop.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _console_print("")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
