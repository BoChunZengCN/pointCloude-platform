import json
from pathlib import Path
from uuid import uuid4

from pc_system.cli import main
from pc_system.production_pipeline import build_production_run_plan, write_production_run_plan
from pc_system.production_run_report import build_production_run_report, write_production_run_report


def case_dir(name: str) -> Path:
    path = Path(__file__).resolve().parent / "_output" / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def sample_plan() -> dict:
    metadata = {
        "asset_id": "scan",
        "file": {"path": "C:/data/scan.las", "name": "scan.las"},
        "las": {"bounds": {"min": [0, 0, 0], "max": [10, 10, 3]}},
    }
    return build_production_run_plan(metadata)


def test_build_production_run_report_summarizes_planned_steps():
    report = build_production_run_report(sample_plan())

    assert report["phase"] == "Phase 3"
    assert report["module"] == "P3-M3 Production Run Report"
    assert report["asset_id"] == "scan"
    assert report["status"] == "not_started"
    assert report["summary"] == {"total": 11, "planned": 11, "completed": 0, "failed": 0, "blocked": 0}
    assert report["steps"][0]["step_id"] == "ingest"
    assert report["steps"][0]["status"] == "planned"


def test_write_production_run_report_outputs_json_and_markdown():
    workspace = case_dir("production-report")
    report = build_production_run_report(sample_plan())

    outputs = write_production_run_report(report, workspace)

    payload = json.loads(outputs["json"].read_text(encoding="utf-8"))
    markdown = outputs["markdown"].read_text(encoding="utf-8")
    assert payload["status"] == "not_started"
    assert outputs["json"].name == "production_run_report.json"
    assert outputs["markdown"].name == "production_run_report.md"
    assert "# Production Run Report" in markdown
    assert "| ingest | Phase 1 | planned |" in markdown


def test_cli_report_production_run_reads_plan_and_writes_report():
    workspace = case_dir("cli-production-report")
    project = workspace / "workspace"
    plan_dir = project / "reports" / "production_runs" / "scan"
    plan = sample_plan()
    write_production_run_plan(plan, plan_dir)

    exit_code = main([
        "report-production-run",
        "--project-root",
        str(project),
        "--asset-id",
        "scan",
    ])

    report_path = plan_dir / "production_run_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["asset_id"] == "scan"
    assert (plan_dir / "production_run_report.md").exists()
