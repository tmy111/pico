# Pico benchmark 复现步骤

这份文档说明如何在本地复现 `benchmarks` 目录里的核心实验结果。命令默认在 Windows PowerShell 中执行，工作目录是仓库根目录：

```powershell
cd D:\code\pico-main
```

## 0. 先理解要复现什么

主要复现对象有两层：

1. 核心固定任务：读取 `benchmarks/coding_tasks.json` 里的 12 个 benchmark task，复制 fixture workspace，用确定性的 `FakeModelClient` 跑 agent，再用每个任务自己的 verifier 判断是否通过。
2. 完整实验包：在核心固定任务之外，再生成 context ablation、memory ablation、recovery ablation 和汇总报告。

复现输出建议写到：

```text
benchmarks/results/local-repro/
```

临时 workspace 建议写到：

```text
artifacts/local-repro-workspaces/
```

## 1. 检查 Python 版本

项目要求 Python 3.10 或更高。

```powershell
python --version
```

期望看到类似：

```text
Python 3.10.x
```

或更高版本。

## 2. 可选：先跑单元测试

这一步不是 benchmark 必需步骤，但可以确认当前代码基本可运行。

```powershell
python -m pytest
```

如果本机没有安装 `pytest`，可以先跳过 benchmark 复现；核心 benchmark 本身不依赖真实模型 API。

## 3. 复现核心 harness regression

在 PowerShell 中执行：

```powershell
@'
from pathlib import Path
from pico.evaluation.evaluator import run_harness_regression_v2

out = Path("benchmarks/results/local-repro")
out.mkdir(parents=True, exist_ok=True)

artifact = run_harness_regression_v2(
    benchmark_path=Path("benchmarks/coding_tasks.json"),
    artifact_path=out / "harness-regression-v2.json",
    workspace_root=Path("artifacts/local-repro-workspaces"),
)

print("wrote", out / "harness-regression-v2.json")
print(artifact["summary"])
'@ | python -
```

这一步会做这些事：

1. 读取 `benchmarks/coding_tasks.json`。
2. 逐个复制 `tests/fixtures/bench_repo_readme` 或 `tests/fixtures/bench_repo_patch`。
3. 用固定 scripted model output 跑 `Pico` agent。
4. 每个任务结束后执行自己的 `verifier`。
5. 生成 `benchmarks/results/local-repro/harness-regression-v2.json`。

## 4. 查看核心结果

执行：

```powershell
(Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json).summary
```

期望核心字段类似：

```text
total_tasks        : 12
passed             : 12
failed             : 0
pass_rate          : 1
within_budget      : 12
verifier_passes    : 12
within_budget_rate : 1
verifier_pass_rate : 1
```

如果 `passed` 不是 12，继续看失败任务：

```powershell
$data = Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json
$data.rows | Where-Object { -not $_.passed } | Select-Object id, status, failure_category, verifier_stderr, stop_reason
```

## 5. 查看每个任务的细节

列出每个任务是否通过：

```powershell
$data = Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json
$data.rows | Select-Object id, category, passed, within_budget, verifier_passed, tool_steps, attempts
```

查看某个任务的运行目录：

```powershell
$data = Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json
$row = $data.rows | Where-Object { $_.id -eq "sample_beta_locked" }
$row.run_dir_relpath
```

运行目录在：

```text
artifacts/local-repro-workspaces/.pico-benchmark-workspaces/<task-id>/<fixture-name>/.pico/runs/<run-id>/
```

里面通常有：

```text
task_state.json
trace.jsonl
report.json
```

## 6. 复现完整实验包

如果核心 harness regression 已经通过，可以继续跑完整实验。

```powershell
@'
from pathlib import Path
from pico.evaluation.evaluator import run_harness_regression_v2
from pico.evaluation.metrics import (
    run_context_ablation_v2,
    run_memory_ablation_v2,
    run_recovery_ablation_v2,
    write_benchmark_core_report,
)

out = Path("benchmarks/results/local-repro")
out.mkdir(parents=True, exist_ok=True)

run_harness_regression_v2(
    benchmark_path=Path("benchmarks/coding_tasks.json"),
    artifact_path=out / "harness-regression-v2.json",
    workspace_root=Path("artifacts/local-repro-workspaces"),
)

run_context_ablation_v2(out / "context-ablation-v2.json", repetitions=5)
run_memory_ablation_v2(out / "memory-ablation-v2.json", repetitions=5)
run_recovery_ablation_v2(out / "recovery-ablation-v2.json", repetitions=3)

write_benchmark_core_report(
    report_path=out / "pico-benchmark-core-report.md",
    harness_artifact_path=out / "harness-regression-v2.json",
    context_artifact_path=out / "context-ablation-v2.json",
    memory_artifact_path=out / "memory-ablation-v2.json",
    recovery_artifact_path=out / "recovery-ablation-v2.json",
)

print("wrote benchmark artifacts to", out)
'@ | python -
```

完成后应生成：

```text
benchmarks/results/local-repro/harness-regression-v2.json
benchmarks/results/local-repro/context-ablation-v2.json
benchmarks/results/local-repro/memory-ablation-v2.json
benchmarks/results/local-repro/recovery-ablation-v2.json
benchmarks/results/local-repro/pico-benchmark-core-report.md
```

## 7. 查看完整实验摘要

Harness regression：

```powershell
(Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json).summary
```

Context ablation：

```powershell
(Get-Content benchmarks/results/local-repro/context-ablation-v2.json -Raw | ConvertFrom-Json).summary
```

Memory ablation：

```powershell
(Get-Content benchmarks/results/local-repro/memory-ablation-v2.json -Raw | ConvertFrom-Json).variants
```

Recovery ablation：

```powershell
(Get-Content benchmarks/results/local-repro/recovery-ablation-v2.json -Raw | ConvertFrom-Json).variants.resume_enabled.summary
```

打开最终报告：

```powershell
Get-Content benchmarks/results/local-repro/pico-benchmark-core-report.md
```

## 8. 和归档结果对比

归档结果在：

```text
benchmarks/results/main-resume-repro-2026-06-07/
```

你可以对比两个核心 summary：

```powershell
$old = Get-Content benchmarks/results/main-resume-repro-2026-06-07/harness-regression-v2.json -Raw | ConvertFrom-Json
$new = Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json

$old.summary
$new.summary
```

注意：上下文字符数、prompt hash、run id、时间戳可能不同，这是正常的。更应该关注：

```text
passed
failed
pass_rate
within_budget_rate
verifier_pass_rate
resume_false_accept_rate
workspace_drift_detection_rate
```

## 9. 常见问题

### `ModuleNotFoundError: No module named 'pico'`

确认你在仓库根目录执行：

```powershell
cd D:\code\pico-main
```

然后再跑命令。

### `python3` 在 Windows 上找不到

不用直接运行 JSON 里的 verifier。`evaluator.py` 会把 verifier 里的 `python3` 自动替换成当前 `sys.executable`。你只需要用：

```powershell
python -
```

来运行本文里的复现脚本。

### `scripts/*.py` 导入失败

当前推荐直接使用：

```python
from pico.evaluation.evaluator import run_harness_regression_v2
from pico.evaluation.metrics import ...
```

不要优先跑 `scripts/run_large_scale_experiments.py`。这些脚本里有旧式 `from pico.metrics import ...` 导入，可能和当前包结构不一致。

### 结果文件里中文显示乱码

这是 PowerShell 终端编码显示问题，不一定表示文件坏了。优先用编辑器打开 Markdown/JSON，或只用 JSON 字段做判断。

## 10. 最小成功标准

如果只是想证明 benchmark 能复现，最低标准是：

```powershell
(Get-Content benchmarks/results/local-repro/harness-regression-v2.json -Raw | ConvertFrom-Json).summary
```

看到：

```text
total_tasks = 12
passed = 12
failed = 0
pass_rate = 1
within_budget_rate = 1
verifier_pass_rate = 1
```

这就说明核心固定任务复现成功。
