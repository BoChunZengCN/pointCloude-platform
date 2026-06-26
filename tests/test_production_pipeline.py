import json
from pathlib import Path
from uuid import uuid4

from pc_system.cli import main
from pc_system.production_pipeline import build_production_run_plan, write_production_run_plan


def case_dir(name: str) -> Path:
    path = Path(__file__).resolve().parent / "_output" / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def sample_asset_metadata(asset_id: str = "scan") -> dict:
    return {
        "asset_id": asset_id,
        "file": {"path": "C:/data/scan.las", "name": "scan.las"},
        "las": {
            "point_count": 1000,
            "bounds": {"min": [0, 0, 0], "max": [10, 10, 3]},
        },
    }


def test_build_production_run_plan_sequences_existing_workflow_commands():
    plan = build_production_run_plan(
        sample_asset_metadata(),
        slice_name="room-a",
        segment_name="baseline",
        splat_name="baseline",
    )

    assert plan["phase"] == "Phase 3"
    assert plan["module"] == "P3-M2 Production Pipeline Plan"
    assert plan["asset_id"] == "scan"
    assert plan["status"] == "planned"
    assert [step["step_id"] for step in plan["steps"]] == [
        "ingest",
        "qa_preview",
        "potree_publish",
        "slice_plan",
        "slice_execute",
        "rule_segment_plan",
        "rule_segment_execute",
        "rule_segment_report",
        "gaussian_splat_plan",
        "phase2_viewer",
        "phase3_tool_check",
    ]
    assert all(step["status"] == "planned" for step in plan["steps"])
    assert plan["steps"][0]["command"][:2] == ["pc-system", "ingest"]
    assert plan["steps"][3]["command"][:2] == ["pc-system", "plan-slice"]


def test_write_production_run_plan_outputs_json_and_markdown():
    workspace = case_dir("production-plan")
    plan = build_production_run_plan(sample_asset_metadata("site-a"))

    outputs = write_production_run_plan(plan, workspace)

    payload = json.loads(outputs["json"].read_text(encoding="utf-8"))
    markdown = outputs["markdown"].read_text(encoding="utf-8")
    assert payload["asset_id"] == "site-a"
    assert outputs["json"].name == "production_run_plan.json"
    assert outputs["markdown"].name == "production_run_plan.md"
    assert "# Production Run Plan" in markdown
    assert "| ingest | Phase 1 | planned |" in markdown


def test_cli_plan_production_run_reads_asset_and_writes_plan():
    workspace = case_dir("cli-production-plan")
    project = workspace / "workspace"
    asset_dir = project / "data" / "assets" / "scan"
    asset_dir.mkdir(parents=True)
    (asset_dir / "asset.json").write_text(json.dumps(sample_asset_metadata()), encoding="utf-8")

    exit_code = main([
        "plan-production-run",
        "--project-root",
        str(project),
        "--asset-id",
        "scan",
        "--slice-name",
        "room-a",
        "--segment-name",
        "baseline",
    ])

    plan_path = project / "reports" / "production_runs" / "scan" / "production_run_plan.json"
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["asset_id"] == "scan"
    assert payload["parameters"]["slice_name"] == "room-a"
    assert (plan_path.parent / "production_run_plan.md").exists()
