"""Browser UI for the local Pico dashboard."""

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pico 工作台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f6f2;
      --surface: #ffffff;
      --surface-soft: #f0f3ee;
      --ink: #151a18;
      --muted: #68716c;
      --line: #d9ded8;
      --line-strong: #b8c2ba;
      --green: #226b46;
      --green-soft: #e0f0e6;
      --blue: #245f86;
      --blue-soft: #dbeaf2;
      --amber: #8b5d13;
      --amber-soft: #f6e8cf;
      --red: #a83a36;
      --red-soft: #f4dddb;
      --shadow: 0 18px 44px rgba(21, 26, 24, 0.08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
    }
    button, input, textarea { font: inherit; }
    button {
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
    }
    button:hover { border-color: var(--line-strong); background: #f9fbf8; }
    .shell {
      height: 100vh;
      min-height: 720px;
      display: grid;
      grid-template-rows: 58px minmax(0, 1fr);
    }
    .topbar {
      display: grid;
      grid-template-columns: minmax(280px, 1fr) auto;
      align-items: center;
      gap: 18px;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.86);
      backdrop-filter: blur(14px);
    }
    .brand {
      min-width: 0;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .mark {
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      border: 1px solid #c8d6cc;
      border-radius: 8px;
      background: #fff;
      color: var(--green);
      font-weight: 800;
    }
    h1 {
      margin: 0;
      font-size: 17px;
      line-height: 1.1;
      letter-spacing: 0;
    }
    .workspace-line {
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .top-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 0 9px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface);
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }
    .workbench {
      min-height: 0;
      display: grid;
      grid-template-columns: 292px minmax(440px, 1fr) 380px;
    }
    .rail, .inspector {
      min-width: 0;
      min-height: 0;
      overflow: auto;
      background: #fbfcfa;
    }
    .rail {
      border-right: 1px solid var(--line);
      padding: 14px;
    }
    .inspector {
      border-left: 1px solid var(--line);
      padding: 14px;
    }
    .chat {
      min-width: 0;
      min-height: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      background: var(--surface);
    }
    .section {
      display: grid;
      gap: 8px;
      margin-bottom: 18px;
    }
    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      min-height: 28px;
      color: #2b342f;
      font-size: 12px;
      font-weight: 750;
      text-transform: uppercase;
    }
    .search {
      width: 100%;
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      padding: 0 10px;
      color: var(--ink);
    }
    .list {
      display: grid;
      gap: 7px;
    }
    .item {
      width: 100%;
      display: grid;
      gap: 5px;
      min-height: 46px;
      padding: 9px;
      border: 1px solid transparent;
      border-radius: 8px;
      background: transparent;
      text-align: left;
    }
    .item:hover { background: #fff; }
    .item.active {
      border-color: #b9d1c0;
      background: var(--green-soft);
    }
    .item-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .item-title {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 13px;
      font-weight: 700;
    }
    .item-meta, .item-text {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      max-width: 120px;
      padding: 0 7px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--muted);
      font-size: 11px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .ok { border-color: #aecfb7; background: var(--green-soft); color: #185135; }
    .info { border-color: #b4cede; background: var(--blue-soft); color: #1e526f; }
    .warn { border-color: #dfc08b; background: var(--amber-soft); color: #70480e; }
    .bad { border-color: #dda6a2; background: var(--red-soft); color: #7d2825; }
    .chat-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      min-height: 64px;
      padding: 12px 18px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }
    .chat-title {
      min-width: 0;
      display: grid;
      gap: 4px;
    }
    .chat-title strong {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 15px;
    }
    .chat-title span {
      color: var(--muted);
      font-size: 12px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(72px, 1fr));
      gap: 8px;
      min-width: 340px;
    }
    .metric {
      min-height: 42px;
      padding: 7px 9px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfa;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 11px;
    }
    .metric strong {
      display: block;
      margin-top: 2px;
      font-size: 15px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .messages {
      min-height: 0;
      overflow: auto;
      padding: 18px;
      display: grid;
      align-content: start;
      gap: 14px;
      background:
        linear-gradient(180deg, rgba(245, 246, 242, 0.9), rgba(255, 255, 255, 0) 160px),
        #fff;
    }
    .message {
      display: grid;
      grid-template-columns: 34px minmax(0, 760px);
      gap: 10px;
      align-items: start;
    }
    .message.assistant { justify-content: start; }
    .message.user {
      grid-template-columns: minmax(0, 760px) 34px;
      justify-content: end;
    }
    .avatar {
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface-soft);
      color: #34413a;
      font-size: 12px;
      font-weight: 800;
    }
    .bubble {
      min-width: 0;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 10px 28px rgba(21, 26, 24, 0.05);
    }
    .user .bubble {
      background: #18211d;
      color: #fff;
      border-color: #18211d;
    }
    .tool .bubble {
      background: #fbfcfa;
      border-color: #cfd8d1;
    }
    .message-role {
      margin-bottom: 7px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 750;
      text-transform: uppercase;
    }
    .user .message-role { color: rgba(255, 255, 255, 0.68); }
    .message-text {
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: 13px/1.55 inherit;
    }
    details.tool-call {
      margin-top: 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
    }
    details.tool-call summary {
      cursor: pointer;
      padding: 8px 10px;
      color: #33413a;
      font-size: 12px;
      font-weight: 700;
    }
    pre {
      margin: 0;
      padding: 10px;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: 12px/1.45 "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    }
    .composer {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      padding: 12px 18px;
      border-top: 1px solid var(--line);
      background: #fff;
    }
    .composer textarea {
      width: 100%;
      min-height: 46px;
      max-height: 120px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
      color: var(--muted);
      background: #fbfcfa;
    }
    .composer button {
      width: 88px;
      height: 46px;
      color: var(--muted);
      background: #f3f5f1;
    }
    .panel {
      display: grid;
      gap: 9px;
      margin-bottom: 14px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      box-shadow: var(--shadow);
    }
    .panel-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }
    .kv {
      display: grid;
      gap: 7px;
    }
    .kv-row {
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 10px;
      font-size: 12px;
    }
    .kv-row span:first-child { color: var(--muted); }
    .kv-row span:last-child {
      min-width: 0;
      overflow-wrap: anywhere;
    }
    .progress-line {
      height: 8px;
      overflow: hidden;
      border-radius: 999px;
      background: var(--surface-soft);
    }
    .progress-line > span {
      display: block;
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--green), var(--blue));
    }
    .timeline {
      display: grid;
      gap: 9px;
    }
    .event {
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr);
      gap: 9px;
      position: relative;
    }
    .event:not(:last-child)::after {
      content: "";
      position: absolute;
      left: 13px;
      top: 28px;
      bottom: -9px;
      width: 2px;
      background: var(--line);
    }
    .dot {
      width: 28px;
      height: 28px;
      display: grid;
      place-items: center;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      font-size: 11px;
      font-weight: 800;
      z-index: 1;
    }
    .event-card {
      min-width: 0;
      padding: 8px 9px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfa;
    }
    .event-card strong {
      display: block;
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .event-card span {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }
    .empty {
      padding: 16px;
      border: 1px dashed var(--line-strong);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.72);
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .hidden { display: none !important; }

    @media (max-width: 1180px) {
      .shell { height: auto; min-height: 100vh; }
      .workbench { grid-template-columns: 280px minmax(0, 1fr); }
      .inspector { grid-column: 1 / -1; border-left: 0; border-top: 1px solid var(--line); }
      .chat { min-height: 680px; }
    }
    @media (max-width: 780px) {
      .topbar { grid-template-columns: 1fr; height: auto; padding: 10px 12px; }
      .top-actions { justify-content: stretch; }
      .top-actions button, .top-actions .status-pill { flex: 1; justify-content: center; }
      .workbench { grid-template-columns: 1fr; }
      .rail { border-right: 0; border-bottom: 1px solid var(--line); }
      .chat-head { align-items: stretch; flex-direction: column; }
      .metrics { min-width: 0; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .message, .message.user { grid-template-columns: 1fr; }
      .avatar { display: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="mark">p</div>
        <div>
          <h1>Pico 工作台</h1>
          <div class="workspace-line" id="workspaceText">正在读取工作区...</div>
        </div>
      </div>
      <div class="top-actions">
        <span class="status-pill" id="activeStatus">空闲</span>
        <button id="refreshButton" type="button">刷新</button>
      </div>
    </header>

    <div class="workbench">
      <aside class="rail">
        <section class="section">
          <div class="section-title"><span>会话历史</span><span class="badge" id="sessionCount">0</span></div>
          <input class="search" id="sessionSearch" type="search" placeholder="搜索会话">
          <div class="list" id="sessionList"></div>
        </section>

        <section class="section">
          <div class="section-title"><span>运行步骤</span><span class="badge" id="stepCount">0/0</span></div>
          <div class="list" id="stepList"></div>
        </section>

        <section class="section">
          <div class="section-title"><span>任务运行</span><span class="badge" id="runCount">0</span></div>
          <input class="search" id="runSearch" type="search" placeholder="搜索任务">
          <div class="list" id="runList"></div>
        </section>
      </aside>

      <main class="chat">
        <header class="chat-head">
          <div class="chat-title">
            <strong id="conversationTitle">尚未加载对话</strong>
            <span id="conversationMeta">等待本地运行记录。</span>
          </div>
          <div class="metrics">
            <div class="metric"><span>运行数</span><strong id="metricRuns">0</strong></div>
            <div class="metric"><span>成功率</span><strong id="metricSuccess">0%</strong></div>
            <div class="metric"><span>工具步数</span><strong id="metricTools">0</strong></div>
            <div class="metric"><span>模型轮次</span><strong id="metricAttempts">0</strong></div>
          </div>
        </header>

        <section class="messages" id="messages"></section>

        <footer class="composer">
          <textarea id="composerText" placeholder="输入测试任务"></textarea>
          <button id="sendButton" type="button">发送</button>
        </footer>
      </main>

      <aside class="inspector">
        <section class="panel">
          <div class="panel-title"><span>当前工作区</span><span class="badge info" id="picoRoot">.pico</span></div>
          <div class="kv" id="workspaceKv"></div>
        </section>

        <section class="panel">
          <div class="panel-title"><span>任务进度</span><span class="badge" id="taskBadge">空闲</span></div>
          <div class="progress-line"><span id="progressFill"></span></div>
          <div class="kv" id="taskKv"></div>
        </section>

        <section class="panel">
          <div class="panel-title"><span>流程</span><span class="badge" id="flowCount">0</span></div>
          <div class="timeline" id="flowTimeline"></div>
        </section>

        <section class="panel">
          <div class="panel-title"><span>轨迹</span><span class="badge" id="traceCount">0</span></div>
          <div class="timeline" id="traceTimeline"></div>
        </section>

        <section class="panel">
          <div class="panel-title"><span>报告</span></div>
          <pre id="reportJson">{}</pre>
        </section>
      </aside>
    </div>
  </div>

  <script>
    const state = {
      data: null,
      selection: { kind: "run", id: "" },
      pollTimer: null,
    };
    const $ = (id) => document.getElementById(id);
    const els = {
      workspaceText: $("workspaceText"),
      activeStatus: $("activeStatus"),
      refreshButton: $("refreshButton"),
      sessionCount: $("sessionCount"),
      stepCount: $("stepCount"),
      runCount: $("runCount"),
      sessionSearch: $("sessionSearch"),
      runSearch: $("runSearch"),
      sessionList: $("sessionList"),
      stepList: $("stepList"),
      runList: $("runList"),
      conversationTitle: $("conversationTitle"),
      conversationMeta: $("conversationMeta"),
      metricRuns: $("metricRuns"),
      metricSuccess: $("metricSuccess"),
      metricTools: $("metricTools"),
      metricAttempts: $("metricAttempts"),
      messages: $("messages"),
      picoRoot: $("picoRoot"),
      workspaceKv: $("workspaceKv"),
      taskBadge: $("taskBadge"),
      progressFill: $("progressFill"),
      taskKv: $("taskKv"),
      flowCount: $("flowCount"),
      flowTimeline: $("flowTimeline"),
      traceCount: $("traceCount"),
      traceTimeline: $("traceTimeline"),
      reportJson: $("reportJson"),
      composerText: $("composerText"),
      sendButton: $("sendButton"),
    };

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function clip(value, limit = 120) {
      const text = String(value ?? "");
      return text.length <= limit ? text : text.slice(0, limit - 1) + "...";
    }

    function fmtNumber(value, digits = 1) {
      const number = Number(value || 0);
      if (!Number.isFinite(number)) return "0";
      return Math.abs(number - Math.round(number)) < 0.05 ? String(Math.round(number)) : number.toFixed(digits);
    }

    function tone(value) {
      const text = String(value || "").toLowerCase();
      if (text.includes("completed") || text.includes("final_answer") || text.includes("success")) return "ok";
      if (text.includes("failed") || text.includes("error") || text.includes("denied") || text.includes("missing_report")) return "bad";
      if (text.includes("running") || text.includes("stopped") || text.includes("limit") || text.includes("tool")) return "warn";
      return "info";
    }

    function displayStatus(value) {
      const text = String(value || "");
      const labels = {
        idle: "空闲",
        running: "运行中",
        completed: "已完成",
        stopped: "已停止",
        failed: "失败",
        interrupted: "已中断",
        unknown: "未知",
      };
      return labels[text.toLowerCase()] || text || "-";
    }

    function displayRole(value) {
      const text = String(value || "").toLowerCase();
      if (text === "user") return "用户";
      if (text === "assistant") return "助手";
      if (text === "tool") return "工具";
      return value || "消息";
    }

    function selectedRun() {
      const data = state.data || { runs: [] };
      return data.runs.find((run) => run.run_id === state.selection.id) || data.runs[0] || null;
    }

    function selectedSession() {
      const data = state.data || { sessions: [] };
      return data.sessions.find((session) => session.id === state.selection.id) || data.sessions[0] || null;
    }

    function currentArtifact() {
      return state.selection.kind === "session" ? selectedSession() : selectedRun();
    }

    async function loadData() {
      els.workspaceText.textContent = "正在读取工作区...";
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) throw new Error(await response.text());
      state.data = await response.json();
      const runtimeRunId = state.data.runtime?.run_id || "";
      if (runtimeRunId) {
        state.selection = { kind: "run", id: runtimeRunId };
      } else if (!state.selection.id) {
        const running = state.data.runs.find((run) => run.status === "running");
        const firstRun = running || state.data.runs[0];
        if (firstRun) state.selection = { kind: "run", id: firstRun.run_id };
        else if (state.data.sessions[0]) state.selection = { kind: "session", id: state.data.sessions[0].id };
      }
      render();
    }

    function render() {
      const data = state.data || { workspace: {}, summary: {}, runs: [], sessions: [], test_steps: [], runtime: {} };
      const summary = data.summary || {};
      const runtime = data.runtime || {};
      const activeRun = selectedRun();
      els.workspaceText.textContent = data.workspace.root || "未知工作区";
      const visibleStatus = runtime.status === "running" ? "running" : (activeRun ? activeRun.status || "unknown" : runtime.status || "idle");
      els.activeStatus.textContent = displayStatus(visibleStatus);
      els.activeStatus.className = `status-pill ${tone(visibleStatus)}`;
      els.sessionCount.textContent = summary.session_count || 0;
      updateStepCount();
      els.runCount.textContent = summary.run_count || 0;
      els.metricRuns.textContent = summary.run_count || 0;
      els.metricSuccess.textContent = `${Math.round((summary.success_rate || 0) * 100)}%`;
      els.metricTools.textContent = fmtNumber(summary.avg_tool_steps);
      els.metricAttempts.textContent = fmtNumber(summary.avg_attempts);
      els.picoRoot.textContent = data.workspace.pico_root ? ".pico" : "none";
      renderWorkspace(data.workspace || {});
      renderLists();
      renderTestSteps();
      renderConversation();
      renderInspector();
      renderComposer(runtime);
      schedulePolling(runtime.status === "running");
    }

    function renderWorkspace(workspace) {
      const runtime = state.data?.runtime || {};
      els.workspaceKv.innerHTML = kvRows([
        ["根目录", workspace.root || "-"],
        ["Pico 数据", workspace.pico_root || "-"],
        ["Provider", runtime.provider || "-"],
        ["Model", runtime.model || "-"],
        ["Approval", runtime.approval || "-"],
      ]);
    }

    function renderComposer(runtime) {
      const running = runtime.status === "running";
      els.composerText.disabled = running;
      els.sendButton.disabled = running || !els.composerText.value.trim();
      els.sendButton.textContent = running ? "运行中" : "发送";
    }

    function filteredSessions() {
      const data = state.data || { sessions: [] };
      const q = els.sessionSearch.value.trim().toLowerCase();
      if (!q) return data.sessions;
      return data.sessions.filter((session) => String(session.id || "").toLowerCase().includes(q));
    }

    function filteredRuns() {
      const data = state.data || { runs: [] };
      const q = els.runSearch.value.trim().toLowerCase();
      if (!q) return data.runs;
      return data.runs.filter((run) => [run.run_id, run.status, run.user_request, run.final_answer, run.last_tool, run.stop_reason].join(" ").toLowerCase().includes(q));
    }

    function renderLists() {
      const sessions = filteredSessions();
      const runs = filteredRuns();
      els.sessionList.innerHTML = sessions.length ? sessions.map((session) => `
        <button class="item ${state.selection.kind === "session" && state.selection.id === session.id ? "active" : ""}" type="button" data-kind="session" data-id="${escapeHtml(session.id)}">
          <span class="item-top"><span class="item-title">${escapeHtml(session.id)}</span></span>
        </button>`).join("") : `<div class="empty">没有找到会话记录。</div>`;

      els.runList.innerHTML = runs.length ? runs.map((run) => `
        <button class="item ${state.selection.kind === "run" && state.selection.id === run.run_id ? "active" : ""}" type="button" data-kind="run" data-id="${escapeHtml(run.run_id)}">
          <span class="item-top"><span class="item-title">${escapeHtml(run.run_id)}</span><span class="badge ${tone(run.status)}">${escapeHtml(displayStatus(run.status || "-"))}</span></span>
          <span class="item-text">${escapeHtml(clip(run.user_request || run.final_answer || "run", 98))}</span>
          <span class="item-meta">${run.tool_steps || 0} 个工具步骤 / ${run.attempts || 0} 轮模型请求</span>
        </button>`).join("") : `<div class="empty">没有找到任务运行记录。</div>`;
    }

    function stepProgress() {
      const steps = state.data?.test_steps || [];
      const run = selectedRun();
      const seenEvents = new Set((run?.trace || []).map((event) => event.event));
      const completed = steps.filter((step) => seenEvents.has(step.event)).length;
      return { steps, seenEvents, completed };
    }

    function updateStepCount() {
      const { steps, completed } = stepProgress();
      els.stepCount.textContent = `${completed}/${steps.length}`;
    }

    function renderTestSteps() {
      const { steps, seenEvents } = stepProgress();
      els.stepList.innerHTML = steps.length ? steps.map((step, index) => {
        const done = seenEvents.has(step.event);
        return `
          <div class="item ${done ? "active" : ""}">
            <span class="item-top"><span class="item-title">${index + 1}. ${escapeHtml(step.title)}</span><span class="badge ${done ? "ok" : "info"}">${done ? "已完成" : "未到达"}</span></span>
          </div>`;
      }).join("") : `<div class="empty">没有运行步骤。</div>`;
    }

    function renderConversation() {
      if (state.selection.kind === "session") {
        const session = selectedSession();
        if (!session) {
          renderEmptyConversation();
          return;
        }
        els.conversationTitle.textContent = session.id;
        els.conversationMeta.textContent = `${session.message_count} 条消息 / ${session.note_count} 条记忆 / ${session.checkpoint_count} 个检查点`;
        const messages = session.history || [];
        els.messages.innerHTML = messages.length ? messages.map(renderMessage).join("") : `<div class="empty">这个会话还没有消息历史。</div>`;
        return;
      }

      const run = selectedRun();
      if (!run) {
        renderEmptyConversation();
        return;
      }
      els.conversationTitle.textContent = run.user_request ? clip(run.user_request, 90) : run.run_id;
      els.conversationMeta.textContent = `${run.run_id} / ${displayStatus(run.status || "unknown")} / ${run.path || ""}`;
      const messages = runMessages(run);
      els.messages.innerHTML = messages.map(renderMessage).join("");
    }

    function renderEmptyConversation() {
      els.conversationTitle.textContent = "尚未加载对话";
      els.conversationMeta.textContent = "等待本地运行记录。";
      els.messages.innerHTML = `<div class="empty">先运行一次 pico，然后刷新这个页面。</div>`;
    }

    function runMessages(run) {
      const messages = [];
      if (run.user_request) messages.push({ role: "user", content: run.user_request });
      for (const event of run.trace || []) {
        if (event.event === "tool_executed") {
          messages.push({
            role: "tool",
            name: event.name || "tool",
            args: event.args || {},
            content: event.result || "",
          });
        } else if (event.event === "model_error") {
          messages.push({
            role: "assistant",
            content: event.error || "Model request failed.",
          });
        } else if (event.event === "model_parsed" && event.kind === "retry") {
          messages.push({
            role: "assistant",
            content: "Runtime asked the model to retry because the response was not a valid tool call or final answer.",
          });
        }
      }
      if (run.final_answer) messages.push({ role: "assistant", content: run.final_answer });
      if (!messages.length) messages.push({ role: "assistant", content: "这个任务运行没有记录到可展示的对话内容。" });
      return messages;
    }

    function renderMessage(message) {
      const role = String(message.role || "assistant").toLowerCase();
      const safeRole = role === "user" ? "user" : role === "tool" ? "tool" : "assistant";
      const avatar = safeRole === "user" ? "U" : safeRole === "tool" ? "T" : "P";
      const body = safeRole === "tool" ? renderToolBody(message) : `<pre class="message-text">${escapeHtml(message.content || "")}</pre>`;
      if (safeRole === "user") {
        return `<article class="message user"><div class="bubble"><div class="message-role">用户</div>${body}</div><div class="avatar">${avatar}</div></article>`;
      }
      return `<article class="message ${safeRole}"><div class="avatar">${avatar}</div><div class="bubble"><div class="message-role">${escapeHtml(safeRole === "tool" ? `工具：${message.name || "tool"}` : displayRole(safeRole))}</div>${body}</div></article>`;
    }

    function renderToolBody(message) {
      return `
        <pre class="message-text">${escapeHtml(clip(message.content || "", 1200))}</pre>
        <details class="tool-call">
          <summary>参数</summary>
          <pre>${escapeHtml(JSON.stringify(message.args || {}, null, 2))}</pre>
        </details>`;
    }

    function renderInspector() {
      const run = state.selection.kind === "run" ? selectedRun() : selectedRun();
      if (!run) {
        els.taskBadge.textContent = "空闲";
        els.taskBadge.className = "badge info";
        els.progressFill.style.width = "0%";
        els.taskKv.innerHTML = kvRows([["状态", "-"], ["运行", "-"]]);
        els.flowCount.textContent = "0";
        els.traceCount.textContent = "0";
        els.flowTimeline.innerHTML = `<div class="empty">尚未选择任务运行。</div>`;
        els.traceTimeline.innerHTML = "";
        els.reportJson.textContent = "{}";
        return;
      }
      const progress = progressPercent(run);
      els.taskBadge.textContent = displayStatus(run.status || "unknown");
      els.taskBadge.className = `badge ${tone(run.status)}`;
      els.progressFill.style.width = `${progress}%`;
      els.taskKv.innerHTML = kvRows([
        ["运行", run.run_id || "-"],
        ["状态", displayStatus(run.status || "-")],
        ["停止原因", run.stop_reason || "-"],
        ["工具步骤", run.tool_steps ?? 0],
        ["模型轮次", run.attempts ?? 0],
        ["最后工具", run.last_tool || "-"],
        ["检查点", run.checkpoint_id || "-"],
        ["恢复状态", run.resume_status || "-"],
      ]);
      const flow = run.flow || [];
      const trace = run.trace || [];
      els.flowCount.textContent = flow.length;
      els.traceCount.textContent = trace.length;
      els.flowTimeline.innerHTML = flow.length ? flow.map((event, index) => renderFlowEvent(event, index)).join("") : `<div class="empty">没有流程事件。</div>`;
      els.traceTimeline.innerHTML = trace.length ? trace.slice(-10).map((event, index) => renderTraceEvent(event, index)).join("") : `<div class="empty">没有轨迹事件。</div>`;
      els.reportJson.textContent = JSON.stringify(run.report || run.task_state || {}, null, 2);
    }

    function progressPercent(run) {
      if (run.status === "completed") return 100;
      if (run.status === "failed" || run.status === "interrupted") return 100;
      const steps = Number(run.tool_steps || 0);
      const attempts = Number(run.attempts || 0);
      return Math.max(8, Math.min(92, 12 + steps * 12 + attempts * 8));
    }

    function renderFlowEvent(event, index) {
      return `
        <div class="event">
          <div class="dot ${tone(event.kind)}">${index + 1}</div>
          <div class="event-card">
            <strong>${escapeHtml(event.title || event.kind || "event")}</strong>
            <span>${escapeHtml(event.detail || "")}</span>
          </div>
        </div>`;
    }

    function renderTraceEvent(event, index) {
      const name = event.event || event.name || `event_${index + 1}`;
      const detail = event.duration_ms !== undefined ? `${event.duration_ms} ms` : JSON.stringify(event);
      return `
        <div class="event">
          <div class="dot ${tone(name)}">${index + 1}</div>
          <div class="event-card">
            <strong>${escapeHtml(name)}</strong>
            <span>${escapeHtml(clip(detail, 140))}</span>
          </div>
        </div>`;
    }

    function kvRows(rows) {
      return rows.map(([key, value]) => `<div class="kv-row"><span>${escapeHtml(key)}</span><span>${escapeHtml(value)}</span></div>`).join("");
    }

    function selectArtifact(kind, id) {
      state.selection = { kind, id };
      render();
    }

    function schedulePolling(shouldPoll) {
      if (state.pollTimer) {
        clearTimeout(state.pollTimer);
        state.pollTimer = null;
      }
      if (!shouldPoll) return;
      state.pollTimer = setTimeout(() => {
        loadData().catch((error) => {
          els.messages.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
        });
      }, 1200);
    }

    async function submitTask() {
      const prompt = els.composerText.value.trim();
      if (!prompt || els.sendButton.disabled) return;
      els.sendButton.disabled = true;
      els.sendButton.textContent = "提交中";
      try {
        const response = await fetch("/api/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.error || response.statusText);
        els.composerText.value = "";
        await loadData();
      } catch (error) {
        els.messages.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
      } finally {
        renderComposer(state.data?.runtime || {});
      }
    }

    els.refreshButton.addEventListener("click", loadData);
    els.sessionSearch.addEventListener("input", renderLists);
    els.runSearch.addEventListener("input", renderLists);
    els.composerText.addEventListener("input", () => renderComposer(state.data?.runtime || {}));
    els.composerText.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        submitTask();
      }
    });
    els.sendButton.addEventListener("click", submitTask);
    els.sessionList.addEventListener("click", (event) => {
      const item = event.target.closest("[data-kind][data-id]");
      if (item) selectArtifact(item.dataset.kind, item.dataset.id);
    });
    els.runList.addEventListener("click", (event) => {
      const item = event.target.closest("[data-kind][data-id]");
      if (item) selectArtifact(item.dataset.kind, item.dataset.id);
    });

    loadData().catch((error) => {
      els.workspaceText.textContent = "读取失败";
      els.messages.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    });
  </script>
</body>
</html>
"""
