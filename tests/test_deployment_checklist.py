import json
from pathlib import Path
from uuid import uuid4

from pc_system.cli import main
from pc_system.deployment_checklist import (
    DeploymentItem,
    build_deployment_checklist,
    write_deployment_checklist,
)


def case_dir(name: str) -> Path:
    path = Path(__file__).resolve().parent / "_output" / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("ok", encoding="utf-8")


def test_build_deployment_checklist_marks_ready_and_missing_items():
    project = Path("C:/workspace")
    existing = {
        project / "data" / "assets" / "asset_index.json",
        project / "reports" / "production_runs" / "scan" / "production_run_plan.json",
        project / "reports" / "production_runs" / "scan" / "production_run_report.json",
    }

    checklist = build_deployment_checklist(
        project,
        "scan",
        exists=lambda path: path in existing,
    )

    assert checklist["phase"] == "Phase 3"
    assert checklist["module"] == "P3-M4 Deployment Package Checklist"
    assert checklist["asset_id"] == "scan"
    assert checklist["status"] == "blocked"
    assert checklist["ready"] is False
    assert checklist["summary"]["ready"] == 3
    assert checklist["summary"]["missing"] > 0
    assert checklist["items"][0]["name"] == "asset_registry"
    assert checklist["items"][0]["status"] == "ready"


def test_write_deployment_checklist_outputs_json_and_markdown():
    checklist = {
        "phase": "Phase 3",
        "module": "P3-M4 Deployment Package Checklist",
        "asset_id": "scan",
        "status": "ready",
        "ready": True,
        "summary": {"total": 1, "ready": 1, "missing": 0},
        "items": [
            DeploymentItem(
                name="asset_registry",
                required=True,
                path="data/assets/asset_index.json",
                status="ready",
            ).to_dict()
        ],
    }
    output_dir = case_dir("deployment-checklist")

    outputs = write_deployment_checklist(checklist, output_dir)

    payload = json.loads(outputs["json"].read_text(encoding="utf-8"))
    markdown = outputs["markdown"].read_text(encoding="utf-8")
    assert payload["ready"] is True
    assert outputs["json"].name == "deployment_checklist.json"
    assert outputs["markdown"].name == "deployment_checklist.md"
    assert "# Deployment Package Checklist" in markdown
    assert "| asset_registry | required | ready | data/assets/asset_index.json |" in markdown


def test_cli_check_deployment_package_writes_report():
    workspace = case_dir("cli-deployment-checklist")
    project = workspace / "workspace"
    touch(project / "data" / "assets" / "asset_index.json")
    touch(project / "reports" / "production_runs" / "scan" / "production_run_plan.json")
    touch(project / "reports" / "production_runs" / "scan" / "production_run_report.json")
    touch(project / "reports" / "phase3_tool_check.json")
    touch(project / "previews" / "scan" / "phase2_viewer_manifest.json")

    exit_code = main([
        "check-deployment-package",
        "--project-root",
        str(project),
        "--asset-id",
        "scan",
    ])

    report_path = project / "reports" / "deployment" / "scan" / "deployment_checklist.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["asset_id"] == "scan"
    assert payload["summary"]["total"] >= 6
    assert (report_path.parent / "deployment_checklist.md").exists()
