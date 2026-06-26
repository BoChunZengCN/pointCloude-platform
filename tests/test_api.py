import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from pc_system.api import create_app


def case_dir(name: str) -> Path:
    path = Path(__file__).resolve().parent / "_output" / f"{name}-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_registry(project: Path) -> None:
    assets_dir = project / "data" / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "asset_index.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "asset_count": 1,
                "assets": [
                    {
                        "asset_id": "scan-a",
                        "file_name": "scan-a.las",
                        "point_count": 10,
                        "report_paths": {"quality_report": "reports/scan-a/quality_report.html"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_api_health_reports_project_root():
    project = case_dir("api-health") / "workspace"
    client = TestClient(create_app(project))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["project_root"].endswith("workspace")


def test_api_lists_assets_from_registry():
    project = case_dir("api-assets") / "workspace"
    write_registry(project)
    client = TestClient(create_app(project))

    response = client.get("/assets")

    assert response.status_code == 200
    payload = response.json()
    assert payload["asset_count"] == 1
    assert payload["assets"][0]["asset_id"] == "scan-a"


def test_api_returns_single_asset_or_404():
    project = case_dir("api-asset-detail") / "workspace"
    write_registry(project)
    client = TestClient(create_app(project))

    found = client.get("/assets/scan-a")
    missing = client.get("/assets/missing")

    assert found.status_code == 200
    assert found.json()["asset_id"] == "scan-a"
    assert missing.status_code == 404
