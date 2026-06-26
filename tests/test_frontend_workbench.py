import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_frontend_workbench_static_files_are_present():
    """FE-M1 应提供可直接打开的静态工作台入口。"""
    index = FRONTEND / "index.html"
    styles = FRONTEND / "app.css"
    script = FRONTEND / "app.js"

    assert index.exists()
    assert styles.exists()
    assert script.exists()

    html = index.read_text(encoding="utf-8")
    assert "点云项目工作台" in html
    assert "app.css" in html
    assert "app.js" in html
    assert "project-preview" in html


def test_frontend_workbench_has_auditable_sample_project_data():
    """工作台先读取静态样例数据，后续可替换为后端生成的 manifest。"""
    sample_path = FRONTEND / "data" / "sample-project.json"
    assert sample_path.exists()

    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    assert payload["project_name"] == "脚架式点云示例项目"
    assert payload["asset"]["format"] == "LAS/LAZ"
    assert {step["phase"] for step in payload["workflow"]} == {"Phase 1", "Phase 2", "Phase 3"}
    assert all("status" in step and "command" in step for step in payload["workflow"])
    assert len(payload["reports"]) >= 3


def test_frontend_workbench_script_renders_core_sections():
    """前端脚本需要渲染工作台核心区域，而不是只有静态占位文字。"""
    script = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert "fetchProjectData" in script
    assert "renderWorkflow" in script
    assert "renderReports" in script
    assert "drawPointCloudPreview" in script
    assert "sample-project.json" in script


def test_frontend_workbench_styles_support_responsive_workspace():
    """工作台布局需要支持桌面和窄屏，避免只适配单一窗口。"""
    css = (FRONTEND / "app.css").read_text(encoding="utf-8")

    assert "grid-template-columns" in css
    assert "@media" in css
    assert "project-shell" in css
    assert "workflow-step" in css
