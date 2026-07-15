import json
import time
from types import SimpleNamespace

import pytest

from pico.dashboard import DashboardTaskRunner, collect_dashboard_state
from pico.run_store import RunStore
from pico.task_state import TaskState


def test_dashboard_state_exposes_runs_and_session_history(tmp_path):
    store = RunStore(tmp_path / ".pico" / "runs")
    task_state = TaskState.create(
        run_id="run_ui_001",
        task_id="task_ui_001",
        user_request="Show the current workspace.",
    )
    store.start_run(task_state)
    store.append_trace(
        task_state,
        {
            "event": "tool_executed",
            "name": "read_file",
            "args": {"path": "README.md"},
            "result": "demo",
        },
    )
    task_state.finish_success("Workspace shown.")
    store.write_task_state(task_state)
    store.write_report(task_state, task_state.to_dict())

    sessions_root = tmp_path / ".pico" / "sessions"
    sessions_root.mkdir(parents=True)
    (sessions_root / "session-ui.json").write_text(
        json.dumps(
            {
                "id": "session-ui",
                "history": [
                    {"role": "user", "content": "hello"},
                    {
                        "role": "tool",
                        "name": "read_file",
                        "args": {"path": "README.md"},
                        "content": "demo",
                    },
                    {"role": "assistant", "content": "hi"},
                ],
                "memory": {"notes": ["remember me"]},
                "checkpoints": {"items": {"cp1": {}}},
            }
        ),
        encoding="utf-8",
    )

    state = collect_dashboard_state(tmp_path)

    assert state["summary"]["run_count"] == 1
    assert state["runs"][0]["run_id"] == "run_ui_001"
    assert state["runs"][0]["flow"]
    assert state["sessions"][0]["id"] == "session-ui"
    assert state["sessions"][0]["message_count"] == 3
    assert state["sessions"][0]["history"][1]["name"] == "read_file"
    assert state["sessions"][0]["history"][1]["args"] == {"path": "README.md"}
    assert [step["event"] for step in state["test_steps"]] == [
        "run_started",
        "prompt_built",
        "model_requested",
        "model_parsed",
        "tool_executed",
        "checkpoint_created",
        "run_finished",
    ]


def test_dashboard_task_runner_runs_agent_in_background():
    class FakeAgent:
        approval_policy = "never"
        model_client = SimpleNamespace(model="fake")

        def __init__(self):
            self.current_task_state = None
            self.prompts = []

        def ask(self, prompt):
            self.prompts.append(prompt)
            self.current_task_state = SimpleNamespace(run_id="run_web_001", status="completed")
            return "done"

    created = []
    runner = DashboardTaskRunner(lambda: created.append(FakeAgent()) or created[-1], runtime_options={"approval": "never", "model": "fake", "provider": "fake"})

    idle = runner.snapshot()

    assert idle["initialized"] is False
    assert idle["approval"] == "never"
    assert created == []

    accepted = runner.start("Inspect README")

    assert accepted["status"] in {"running", "completed"}
    for _ in range(20):
        snapshot = runner.snapshot()
        if snapshot["status"] == "completed":
            break
        time.sleep(0.01)
    assert snapshot["status"] == "completed"
    assert snapshot["run_id"] == "run_web_001"
    assert snapshot["answer"] == "done"
    assert snapshot["approval"] == "never"
    assert snapshot["model"] == "fake"
    assert snapshot["initialized"] is True
    assert len(created) == 1


def test_dashboard_task_runner_rejects_empty_prompt():
    created = []
    runner = DashboardTaskRunner(lambda: created.append(SimpleNamespace(ask=lambda prompt: "unused")) or created[-1])

    with pytest.raises(ValueError, match="prompt must not be empty"):
        runner.start("   ")
    assert created == []
