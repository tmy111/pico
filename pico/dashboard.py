"""Local read-only dashboard for Pico artifacts."""

from __future__ import annotations

import argparse
import json
import mimetypes
import posixpath
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pico 本地观测台</title>
  <style>
    :root {
      --bg: #f6f7f3;
      --panel: #ffffff;
      --soft: #eef4ef;
      --ink: #17201b;
      --muted: #67716a;
      --line: #dae2dc;
      --green: #247a52;
      --green-soft: #e1f1e6;
      --amber: #9a6618;
      --amber-soft: #f8ead2;
      --red: #ae3a36;
      --red-soft: #f6dfdc;
      --blue: #286b8f;
      --blue-soft: #dcecf2;
      --shadow: 0 16px 42px rgba(23, 32, 27, 0.08);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: linear-gradient(180deg, rgba(225, 241, 230, 0.72), rgba(246, 247, 243, 0) 330px), var(--bg);
      color: var(--ink);
    }
    button, input, select { font: inherit; }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      min-height: 38px;
      padding: 0 12px;
      cursor: pointer;
    }
    button:hover { border-color: #aab8ae; background: #f7faf7; }
    .shell { width: min(1480px, calc(100% - 40px)); margin: 0 auto; padding: 20px 0 36px; }
    .topbar { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding-bottom: 18px; }
    .brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
    .mark {
      width: 42px; height: 42px; display: grid; place-items: center; flex: 0 0 auto;
      border: 1px solid #c5d6ca; background: #fff; box-shadow: 0 10px 28px rgba(36, 122, 82, 0.12);
      font-weight: 800;
    }
    h1 { margin: 0; font-size: 22px; line-height: 1.1; letter-spacing: 0; }
    .subtitle { margin: 4px 0 0; color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .actions { display: flex; align-items: center; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }
    .layout { display: grid; grid-template-columns: 312px minmax(0, 1fr); gap: 18px; align-items: start; }
    .sidebar { position: sticky; top: 18px; display: grid; gap: 14px; min-width: 0; }
    .main { display: grid; gap: 18px; min-width: 0; }
    .panel { background: var(--panel); border: 1px solid var(--line); box-shadow: var(--shadow); }
    .panel-inner { padding: 16px; }
    .title-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
    h2 { margin: 0; font-size: 14px; letter-spacing: 0; }
    .hint { color: var(--muted); font-size: 12px; line-height: 1.55; }
    .nav { display: grid; gap: 6px; }
    .nav button {
      width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 12px;
      border-color: transparent; background: transparent; text-align: left;
    }
    .nav button.active { border-color: #b8d2c1; background: var(--green-soft); color: #154a31; font-weight: 700; }
    .count {
      min-width: 30px; height: 22px; display: inline-grid; place-items: center;
      border: 1px solid var(--line); background: #fff; color: var(--muted); font-size: 12px;
    }
    .summary-grid { display: grid; grid-template-columns: repeat(5, minmax(128px, 1fr)); gap: 12px; }
    .metric { border: 1px solid var(--line); background: #fff; min-height: 94px; padding: 14px; }
    .metric span { display: block; color: var(--muted); font-size: 12px; margin-bottom: 10px; }
    .metric strong { display: block; font-size: 28px; line-height: 1; }
    .metric small { display: block; color: var(--muted); margin-top: 9px; overflow-wrap: anywhere; }
    .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
    .search { width: min(380px, 100%); min-height: 38px; border: 1px solid var(--line); background: #fff; padding: 0 11px; }
    .table-wrap { overflow: auto; border: 1px solid var(--line); }
    table { width: 100%; min-width: 820px; border-collapse: collapse; background: #fff; }
    th, td { text-align: left; padding: 11px 12px; border-bottom: 1px solid var(--line); vertical-align: top; font-size: 13px; }
    th { position: sticky; top: 0; z-index: 1; background: #f2f6f1; color: #3e4b42; font-weight: 750; }
    tr[data-run-id] { cursor: pointer; }
    tr[data-run-id]:hover td { background: #f7faf7; }
    tr.selected td { background: #edf8f1; }
    .badge {
      display: inline-flex; align-items: center; min-height: 24px; padding: 0 8px;
      border: 1px solid var(--line); background: #fff; font-size: 12px; white-space: nowrap;
    }
    .ok { border-color: #afd5b8; background: var(--green-soft); color: #185536; }
    .warn { border-color: #e5c28c; background: var(--amber-soft); color: #75490e; }
    .bad { border-color: #e2aaa6; background: var(--red-soft); color: #84241f; }
    .info { border-color: #b2d2df; background: var(--blue-soft); color: #20546e; }
    .detail-grid { display: grid; grid-template-columns: minmax(0, 0.92fr) minmax(420px, 1.08fr); gap: 14px; align-items: start; }
    .kv { display: grid; gap: 9px; }
    .kv-row { display: grid; grid-template-columns: 126px minmax(0, 1fr); gap: 12px; padding-bottom: 9px; border-bottom: 1px solid var(--line); }
    .kv-row dt { margin: 0; color: var(--muted); font-size: 12px; }
    .kv-row dd { margin: 0; font-size: 13px; overflow-wrap: anywhere; }
    .box, .answer, .flow, .timeline { border: 1px solid var(--line); background: #fbfcfa; }
    .answer { padding: 12px; min-height: 94px; white-space: pre-wrap; line-height: 1.55; font-size: 13px; overflow-wrap: anywhere; }
    .box { padding: 12px; max-height: 420px; overflow: auto; }
    pre { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.5 "SFMono-Regular", Consolas, "Liberation Mono", monospace; }
    .flow { padding: 14px; display: grid; gap: 10px; }
    .flow-node {
      display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 10px; align-items: start;
      position: relative;
    }
    .flow-node:not(:last-child)::after {
      content: ""; position: absolute; left: 16px; top: 34px; bottom: -10px; width: 2px; background: var(--line);
    }
    .dot {
      width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid var(--line);
      background: #fff; font-size: 13px; font-weight: 750; z-index: 1;
    }
    .flow-card { border: 1px solid var(--line); background: #fff; padding: 10px; min-width: 0; }
    .flow-card strong { display: block; font-size: 13px; margin-bottom: 4px; }
    .flow-card p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.45; overflow-wrap: anywhere; }
    .timeline { max-height: 620px; overflow: auto; }
    .event { display: grid; grid-template-columns: 140px minmax(0, 1fr); gap: 12px; padding: 13px; border-bottom: 1px solid var(--line); }
    .event:last-child { border-bottom: 0; }
    .event-name { font-weight: 750; font-size: 13px; overflow-wrap: anywhere; }
    .event-meta { margin-top: 4px; color: var(--muted); font-size: 12px; }
    .session-list { display: grid; gap: 10px; }
    .session-item { border: 1px solid var(--line); background: #fff; padding: 12px; display: grid; gap: 8px; }
    .session-top { display: flex; justify-content: space-between; gap: 10px; align-items: start; }
    .session-id { font-weight: 750; overflow-wrap: anywhere; }
    .session-meta { color: var(--muted); font-size: 12px; }
    .empty { border: 1px dashed #b8c7bd; background: rgba(255, 255, 255, 0.72); padding: 22px; color: var(--muted); line-height: 1.65; }
    .asset-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 12px; }
    .asset-strip img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border: 1px solid var(--line); background: #eef1ec; }
    .hidden { display: none !important; }
    @media (max-width: 1100px) {
      .layout, .detail-grid { grid-template-columns: 1fr; }
      .sidebar { position: static; }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 680px) {
      .shell { width: min(100% - 24px, 1480px); }
      .topbar { align-items: stretch; flex-direction: column; }
      .actions, .actions button { width: 100%; justify-content: center; }
      .summary-grid { grid-template-columns: 1fr; }
      .kv-row, .event { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="mark">p</div>
        <div>
          <h1>Pico 本地观测台</h1>
          <p class="subtitle" id="workspaceText">正在读取工作区...</p>
        </div>
      </div>
      <div class="actions">
        <button id="refreshButton" type="button">刷新</button>
        <button id="openStaticButton" type="button">静态版</button>
      </div>
    </header>

    <div class="layout">
      <aside class="sidebar">
        <section class="panel">
          <div class="panel-inner">
            <div class="title-row"><h2>查看范围</h2></div>
            <p class="hint" id="sourceHint">服务端只读当前工作区的 `.pico`、`benchmarks/results` 和 `assets/screenshots`。</p>
            <nav class="nav">
              <button class="active" type="button" data-view="runs">Runs <span class="count" id="runCount">0</span></button>
              <button type="button" data-view="sessions">Sessions <span class="count" id="sessionCount">0</span></button>
              <button type="button" data-view="benchmarks">Benchmarks <span class="count" id="benchmarkCount">0</span></button>
            </nav>
          </div>
        </section>
        <section class="panel">
          <div class="panel-inner">
            <div class="title-row"><h2>CLI 截图</h2></div>
            <p class="hint">用于对照命令行界面，图片从本仓库 assets 读取。</p>
            <div class="asset-strip">
              <img src="/assets/screenshots/pico-help.png" alt="pico help">
              <img src="/assets/screenshots/pico-start.png" alt="pico start">
              <img src="/assets/screenshots/pico-repl.png" alt="pico repl">
            </div>
          </div>
        </section>
      </aside>

      <main class="main">
        <section class="summary-grid">
          <div class="metric"><span>Run 数</span><strong id="metricRuns">0</strong><small id="metricLatest">尚未加载</small></div>
          <div class="metric"><span>成功率</span><strong id="metricSuccess">0%</strong><small>status = completed</small></div>
          <div class="metric"><span>平均工具步</span><strong id="metricTools">0</strong><small>agent action count</small></div>
          <div class="metric"><span>平均 attempts</span><strong id="metricAttempts">0</strong><small>model request rounds</small></div>
          <div class="metric"><span>Sessions</span><strong id="metricSessions">0</strong><small>.pico/sessions</small></div>
        </section>

        <section id="runsView" class="panel">
          <div class="panel-inner">
            <div class="toolbar">
              <div><div class="title-row"><h2>Run 列表</h2></div><p class="hint">点击一行查看流程图、trace 时间线和 report。</p></div>
              <input class="search" id="runSearch" type="search" placeholder="筛选 run、请求、状态或工具">
            </div>
            <div id="runsEmpty" class="empty">当前工作区还没有 `.pico/runs` 数据。跑一次 `pico "your task"` 后再刷新。</div>
            <div id="runsTableWrap" class="table-wrap hidden">
              <table>
                <thead><tr><th>Run</th><th>状态</th><th>用户请求</th><th>工具步</th><th>Attempts</th><th>停止原因</th><th>最后工具</th></tr></thead>
                <tbody id="runsTable"></tbody>
              </table>
            </div>
          </div>
        </section>

        <section id="runDetail" class="panel hidden">
          <div class="panel-inner">
            <div class="title-row"><h2>Run 详情</h2><span class="badge info" id="detailRunId">-</span></div>
            <div class="detail-grid">
              <div>
                <dl class="kv" id="runKv"></dl>
                <h2 style="margin:18px 0 10px;">可视化流程</h2>
                <div class="flow" id="runFlow"></div>
                <h2 style="margin:18px 0 10px;">最终回答</h2>
                <div class="answer" id="finalAnswer"></div>
                <h2 style="margin:18px 0 10px;">Report JSON</h2>
                <div class="box"><pre id="reportJson">{}</pre></div>
              </div>
              <div>
                <h2 style="margin:0 0 10px;">Trace 时间线</h2>
                <div class="timeline" id="traceTimeline"></div>
              </div>
            </div>
          </div>
        </section>

        <section id="sessionsView" class="panel hidden">
          <div class="panel-inner">
            <div class="toolbar">
              <div><div class="title-row"><h2>Session / Memory</h2></div><p class="hint">展示会话历史、memory 和 checkpoint 摘要。</p></div>
              <input class="search" id="sessionSearch" type="search" placeholder="筛选 session、消息或 memory">
            </div>
            <div id="sessionsEmpty" class="empty">当前工作区还没有 `.pico/sessions` 数据。</div>
            <div id="sessionList" class="session-list hidden"></div>
          </div>
        </section>

        <section id="benchmarksView" class="panel hidden">
          <div class="panel-inner">
            <div class="title-row"><h2>Benchmark 产物</h2></div>
            <p class="hint">自动读取 `benchmarks/results` 下的 JSON/Markdown 摘要，方便快速对照评测结论。</p>
            <div id="benchmarksEmpty" class="empty">没有找到 benchmark 产物。</div>
            <div id="benchmarkList" class="session-list hidden"></div>
          </div>
        </section>
      </main>
    </div>
  </div>

  <script>
    const state = { data: null, activeRunId: "", view: "runs" };
    const $ = (id) => document.getElementById(id);
    const els = {
      workspaceText: $("workspaceText"), sourceHint: $("sourceHint"), refreshButton: $("refreshButton"),
      openStaticButton: $("openStaticButton"), runCount: $("runCount"), sessionCount: $("sessionCount"),
      benchmarkCount: $("benchmarkCount"), metricRuns: $("metricRuns"), metricLatest: $("metricLatest"),
      metricSuccess: $("metricSuccess"), metricTools: $("metricTools"), metricAttempts: $("metricAttempts"),
      metricSessions: $("metricSessions"), runSearch: $("runSearch"), sessionSearch: $("sessionSearch"),
      runsEmpty: $("runsEmpty"), runsTableWrap: $("runsTableWrap"), runsTable: $("runsTable"),
      runDetail: $("runDetail"), detailRunId: $("detailRunId"), runKv: $("runKv"), runFlow: $("runFlow"),
      finalAnswer: $("finalAnswer"), reportJson: $("reportJson"), traceTimeline: $("traceTimeline"),
      sessionsEmpty: $("sessionsEmpty"), sessionList: $("sessionList"), benchmarksEmpty: $("benchmarksEmpty"),
      benchmarkList: $("benchmarkList"),
      views: { runs: $("runsView"), sessions: $("sessionsView"), benchmarks: $("benchmarksView") },
    };

    function escapeHtml(value) {
      return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
    }
    function clip(value, length = 150) {
      const text = String(value || "");
      return text.length <= length ? text : text.slice(0, length - 1) + "...";
    }
    function fmtNumber(value, digits = 1) {
      const number = Number(value || 0);
      if (!Number.isFinite(number)) return "0";
      return Math.abs(number - Math.round(number)) < 0.05 ? String(Math.round(number)) : number.toFixed(digits);
    }
    function badgeClass(status, stopReason) {
      const value = String(status || stopReason || "").toLowerCase();
      if (value.includes("completed") || value.includes("final_answer")) return "ok";
      if (value.includes("failed") || value.includes("error") || value.includes("denied") || value.includes("interrupted") || value.includes("missing_report")) return "bad";
      if (value.includes("running") || value.includes("stopped") || value.includes("limit")) return "warn";
      return "info";
    }
    function eventTone(event) {
      const name = String(event.kind || event.event || "").toLowerCase();
      if (name.includes("finish") || name.includes("answer")) return "ok";
      if (name.includes("error") || name.includes("failed") || name.includes("denied")) return "bad";
      if (name.includes("tool") || name.includes("checkpoint")) return "warn";
      return "info";
    }

    async function loadData() {
      els.workspaceText.textContent = "正在读取工作区...";
      const response = await fetch("/api/state", { cache: "no-store" });
      if (!response.ok) throw new Error(await response.text());
      state.data = await response.json();
      state.activeRunId = state.data.runs[0]?.run_id || "";
      renderAll();
    }

    function renderAll() {
      const data = state.data || { workspace: {}, summary: {}, runs: [], sessions: [], benchmarks: [] };
      els.workspaceText.textContent = data.workspace.root || "未知工作区";
      els.sourceHint.textContent = `只读数据源：${data.workspace.pico_root || ".pico"}`;
      els.runCount.textContent = data.summary.run_count || 0;
      els.sessionCount.textContent = data.summary.session_count || 0;
      els.benchmarkCount.textContent = data.summary.benchmark_count || 0;
      els.metricRuns.textContent = data.summary.run_count || 0;
      els.metricSuccess.textContent = `${Math.round((data.summary.success_rate || 0) * 100)}%`;
      els.metricTools.textContent = fmtNumber(data.summary.avg_tool_steps);
      els.metricAttempts.textContent = fmtNumber(data.summary.avg_attempts);
      els.metricSessions.textContent = data.summary.session_count || 0;
      els.metricLatest.textContent = data.runs[0] ? clip(data.runs[0].run_id, 28) : "尚未加载";
      renderRuns();
      renderRunDetail();
      renderSessions();
      renderBenchmarks();
    }

    function filteredRuns() {
      const data = state.data || { runs: [] };
      const q = els.runSearch.value.trim().toLowerCase();
      if (!q) return data.runs;
      return data.runs.filter((run) => [run.run_id, run.status, run.user_request, run.stop_reason, run.last_tool, run.final_answer].join(" ").toLowerCase().includes(q));
    }

    function renderRuns() {
      const data = state.data || { runs: [] };
      const rows = filteredRuns();
      els.runsEmpty.classList.toggle("hidden", data.runs.length > 0);
      els.runsTableWrap.classList.toggle("hidden", data.runs.length === 0);
      els.runsTable.innerHTML = rows.map((run) => `
        <tr data-run-id="${escapeHtml(run.run_id)}" class="${run.run_id === state.activeRunId ? "selected" : ""}">
          <td><strong>${escapeHtml(run.run_id)}</strong></td>
          <td><span class="badge ${badgeClass(run.status, run.stop_reason)}">${escapeHtml(run.status || "unknown")}</span></td>
          <td>${escapeHtml(clip(run.user_request, 190))}</td>
          <td>${escapeHtml(run.tool_steps)}</td>
          <td>${escapeHtml(run.attempts)}</td>
          <td>${escapeHtml(run.stop_reason || "-")}</td>
          <td>${escapeHtml(run.last_tool || "-")}</td>
        </tr>`).join("");
    }

    function renderRunDetail() {
      const data = state.data || { runs: [] };
      const run = data.runs.find((item) => item.run_id === state.activeRunId);
      els.runDetail.classList.toggle("hidden", !run || state.view !== "runs");
      if (!run) return;
      els.detailRunId.textContent = run.run_id;
      const rows = [
        ["状态", run.status || "unknown"], ["用户请求", run.user_request || "-"], ["停止原因", run.stop_reason || "-"],
        ["工具步", run.tool_steps], ["Attempts", run.attempts], ["最后工具", run.last_tool || "-"],
        ["恢复状态", run.resume_status || "-"], ["Checkpoint", run.checkpoint_id || "-"], ["目录", run.path || "-"],
      ];
      els.runKv.innerHTML = rows.map(([key, value]) => `<div class="kv-row"><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("");
      els.runFlow.innerHTML = (run.flow || []).length ? run.flow.map((node, index) => `
        <div class="flow-node">
          <div class="dot ${eventTone(node)}">${index + 1}</div>
          <div class="flow-card">
            <strong>${escapeHtml(node.title)}</strong>
            <p>${escapeHtml(node.detail || "")}</p>
          </div>
        </div>`).join("") : `<div class="empty">没有足够 trace 数据生成流程。</div>`;
      els.finalAnswer.textContent = run.final_answer || "这个 run 还没有记录 final_answer。";
      els.reportJson.textContent = JSON.stringify(run.report || {}, null, 2);
      els.traceTimeline.innerHTML = (run.trace || []).length ? run.trace.map((event, index) => renderEvent(event, index)).join("") : `<div class="event"><div><div class="event-name">no_trace</div></div><pre>没有找到 trace.jsonl</pre></div>`;
    }

    function renderEvent(event, index) {
      const name = event.event || event.name || `event_${index + 1}`;
      const duration = event.duration_ms ?? event.run_duration_ms;
      const meta = [duration !== undefined ? `${duration} ms` : "", event.tool_status ? `tool: ${event.tool_status}` : "", event.name && event.name !== name ? `name: ${event.name}` : ""].filter(Boolean).join(" · ");
      return `<div class="event"><div><div class="event-name">${escapeHtml(name)}</div><div class="event-meta">${escapeHtml(meta || `#${index + 1}`)}</div></div><pre>${escapeHtml(JSON.stringify(event, null, 2))}</pre></div>`;
    }

    function filteredSessions() {
      const data = state.data || { sessions: [] };
      const q = els.sessionSearch.value.trim().toLowerCase();
      if (!q) return data.sessions;
      return data.sessions.filter((session) => JSON.stringify(session).toLowerCase().includes(q));
    }

    function renderSessions() {
      const data = state.data || { sessions: [] };
      const sessions = filteredSessions();
      els.sessionsEmpty.classList.toggle("hidden", data.sessions.length > 0);
      els.sessionList.classList.toggle("hidden", data.sessions.length === 0);
      els.sessionList.innerHTML = sessions.map((session) => `
        <article class="session-item">
          <div class="session-top">
            <div><div class="session-id">${escapeHtml(session.id)}</div><div class="session-meta">${escapeHtml(session.path)} · ${session.message_count} messages · ${session.note_count} notes · ${session.checkpoint_count} checkpoints</div></div>
            <span class="badge info">${escapeHtml(session.cwd || "session")}</span>
          </div>
          <div class="answer">${escapeHtml(session.last_message || "没有历史消息")}</div>
          <div class="box"><pre>${escapeHtml(JSON.stringify(session.preview, null, 2))}</pre></div>
        </article>`).join("");
    }

    function renderBenchmarks() {
      const data = state.data || { benchmarks: [] };
      els.benchmarksEmpty.classList.toggle("hidden", data.benchmarks.length > 0);
      els.benchmarkList.classList.toggle("hidden", data.benchmarks.length === 0);
      els.benchmarkList.innerHTML = data.benchmarks.map((item) => `
        <article class="session-item">
          <div class="session-top">
            <div><div class="session-id">${escapeHtml(item.name)}</div><div class="session-meta">${escapeHtml(item.path)}</div></div>
            <span class="badge info">${escapeHtml(item.kind)}</span>
          </div>
          <div class="box"><pre>${escapeHtml(item.preview)}</pre></div>
        </article>`).join("");
    }

    function switchView(view) {
      state.view = view;
      document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
      Object.entries(els.views).forEach(([key, node]) => node.classList.toggle("hidden", key !== view));
      els.runDetail.classList.toggle("hidden", view !== "runs" || !state.activeRunId);
    }

    els.refreshButton.addEventListener("click", loadData);
    els.openStaticButton.addEventListener("click", () => { window.location.href = "/static-viewer"; });
    els.runSearch.addEventListener("input", renderRuns);
    els.sessionSearch.addEventListener("input", renderSessions);
    els.runsTable.addEventListener("click", (event) => {
      const row = event.target.closest("tr[data-run-id]");
      if (!row) return;
      state.activeRunId = row.dataset.runId;
      renderRuns();
      renderRunDetail();
    });
    document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
    loadData().catch((error) => {
      els.workspaceText.textContent = "读取失败";
      els.sourceHint.textContent = error.message;
    });
  </script>
</body>
</html>
"""


try:
    from .dashboard_frontend import INDEX_HTML as WORKBENCH_HTML
except ImportError:  # pragma: no cover - supports direct script execution.
    from dashboard_frontend import INDEX_HTML as WORKBENCH_HTML

INDEX_HTML = WORKBENCH_HTML


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
    }


class DashboardHandler(BaseHTTPRequestHandler):
    workspace_root: Path

    def log_message(self, format: str, *args: object) -> None:
        if sys.stderr is not None:
            sys.stderr.write("[pico-viewer] " + (format % args) + "\n")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_text(INDEX_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/state":
            self._send_json(collect_dashboard_state(self.workspace_root))
            return
        if parsed.path == "/static-viewer":
            static_path = self.workspace_root / "pico-local-viewer.html"
            if static_path.exists():
                self._send_text(static_path.read_text(encoding="utf-8"), "text/html; charset=utf-8")
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "static viewer not found")
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

    def _send_text(self, text: str, content_type: str) -> None:
        payload = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, payload: object) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
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
    parser = argparse.ArgumentParser(description="Run a read-only local dashboard for Pico artifacts.")
    parser.add_argument("--cwd", default=".", help="Workspace root containing .pico.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    parser.add_argument("--open", action="store_true", help="Open the dashboard in the default browser.")
    return parser


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
