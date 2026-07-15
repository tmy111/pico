import json

from pico.dashboard import collect_dashboard_state
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
