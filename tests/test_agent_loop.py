from pico import FakeModelClient, Pico, SessionStore, WorkspaceContext
from pico.agent_loop import AgentLoop
<<<<<<< HEAD
from pico.task_state import STATUS_FAILED, STOP_REASON_MODEL_ERROR


class FailingModelClient:
    supports_prompt_cache = False

    def __init__(self, message="backend broke"):
        self.message = message
        self.prompts = []
        self.last_completion_metadata = {"provider": "fake"}

    def complete(self, prompt, max_new_tokens, **kwargs):
        del max_new_tokens, kwargs
        self.prompts.append(prompt)
        raise RuntimeError(self.message)
=======
>>>>>>> origin/main


def build_agent(tmp_path, outputs):
    (tmp_path / "README.md").write_text("demo\n", encoding="utf-8")
    workspace = WorkspaceContext.build(tmp_path)
    store = SessionStore(tmp_path / ".pico" / "sessions")
    return Pico(
        model_client=FakeModelClient(outputs),
        workspace=workspace,
        session_store=store,
        approval_policy="auto",
    )


def test_agent_loop_runs_same_control_flow_as_pico_ask(tmp_path):
    (tmp_path / "hello.txt").write_text("alpha\n", encoding="utf-8")
    agent = build_agent(
        tmp_path,
        [
            '<tool>{"name":"read_file","args":{"path":"hello.txt","start":1,"end":1}}</tool>',
            "<final>Done.</final>",
        ],
    )

    answer = AgentLoop(agent).run("Inspect hello.txt")

    assert answer == "Done."
    assert agent.current_task_state.status == "completed"
    assert agent.run_store.report_path(agent.current_task_state.run_id).exists()


def test_pico_ask_delegates_to_agent_loop(tmp_path):
    agent = build_agent(tmp_path, ["<final>Facade works.</final>"])

    assert agent.ask("Use facade") == "Facade works."
<<<<<<< HEAD


def test_agent_loop_marks_model_error_as_failed_and_writes_report(tmp_path):
    agent = build_agent(tmp_path, [])
    agent.model_client = FailingModelClient("provider returned no text")

    answer = AgentLoop(agent).run("Trigger provider error")

    task_state = agent.current_task_state
    report = agent.run_store.load_report(task_state.run_id)
    trace_text = agent.run_store.trace_path(task_state).read_text(encoding="utf-8")
    assert answer == "provider returned no text"
    assert task_state.status == STATUS_FAILED
    assert task_state.stop_reason == STOP_REASON_MODEL_ERROR
    assert report["status"] == STATUS_FAILED
    assert report["stop_reason"] == STOP_REASON_MODEL_ERROR
    assert report["final_answer"] == "provider returned no text"
    assert '"event": "model_error"' in trace_text
    assert '"event": "run_finished"' in trace_text


def test_agent_loop_uses_finalization_turn_after_tool_budget(tmp_path):
    (tmp_path / "hello.txt").write_text("alpha\n", encoding="utf-8")
    agent = build_agent(
        tmp_path,
        [
            '<tool>{"name":"read_file","args":{"path":"hello.txt","start":1,"end":1}}</tool>',
            "<final>Summarized with gathered evidence.</final>",
        ],
    )
    agent.max_steps = 1

    answer = AgentLoop(agent).run("Inspect hello.txt")

    task_state = agent.current_task_state
    report = agent.run_store.load_report(task_state.run_id)
    trace_text = agent.run_store.trace_path(task_state).read_text(encoding="utf-8")
    assert answer == "Summarized with gathered evidence."
    assert task_state.status == "completed"
    assert task_state.tool_steps == 1
    assert task_state.attempts == 2
    assert report["final_answer"] == "Summarized with gathered evidence."
    assert "Do not call more tools" in agent.model_client.prompts[-1]
    assert '"finalization_turn": true' in trace_text
=======
>>>>>>> origin/main
