from pathlib import Path

from pc_system.json_io import write_json


SUMMARY_STATUSES = ["planned", "completed", "failed", "blocked"]


def build_production_run_report(plan: dict, step_results: dict[str, dict] | None = None) -> dict:
    """根据生产运行计划生成 P3-M3 运行报告。

    当前版本先汇总计划状态；后续接入真实执行器时，step_results 可覆盖单步状态。
    """

    results = step_results or {}
    steps = []
    for step in plan["steps"]:
        result = results.get(step["step_id"], {})
        status = result.get("status", step["status"])
        steps.append(
            {
                "step_id": step["step_id"],
                "phase": step["phase"],
                "name": step["name"],
                "status": status,
                "command": step["command"],
                "outputs": step["outputs"],
                "message": result.get("message", ""),
            }
        )

    summary = {"total": len(steps)}
    for status in SUMMARY_STATUSES:
        summary[status] = sum(1 for step in steps if step["status"] == status)

    if summary["failed"] > 0:
        run_status = "failed"
    elif summary["blocked"] > 0:
        run_status = "blocked"
    elif summary["completed"] == summary["total"]:
        run_status = "completed"
    else:
        run_status = "not_started"

    return {
        "phase": "Phase 3",
        "module": "P3-M3 Production Run Report",
        "asset_id": plan["asset_id"],
        "status": run_status,
        "summary": summary,
        "steps": steps,
    }


def _render_markdown(report: dict) -> str:
    """把运行报告渲染为 Markdown。"""

    lines = [
        "# Production Run Report",
        "",
        f"Asset: {report['asset_id']}",
        f"Status: {report['status']}",
        "",
        "| Step | Phase | Status | Name |",
        "| --- | --- | --- | --- |",
    ]
    for step in report["steps"]:
        lines.append(f"| {step['step_id']} | {step['phase']} | {step['status']} | {step['name']} |")
    return "\n".join(lines) + "\n"


def write_production_run_report(report: dict, output_dir: Path) -> dict[str, Path]:
    """写出生产运行报告 JSON 和 Markdown。"""

    json_path = write_json(report, output_dir / "production_run_report.json")
    markdown_path = output_dir / "production_run_report.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
