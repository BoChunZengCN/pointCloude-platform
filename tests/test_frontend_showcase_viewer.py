from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_showcase_viewer_entry_files_exist_and_link_assets():
    """FE-M3 应提供独立展示型查看器入口。"""
    viewer = FRONTEND / "viewer.html"
    styles = FRONTEND / "viewer.css"
    script = FRONTEND / "viewer.js"

    assert viewer.exists()
    assert styles.exists()
    assert script.exists()

    html = viewer.read_text(encoding="utf-8")
    assert "展示型查看器入口" in html
    assert "viewer.css" in html
    assert "viewer.js" in html
    assert "showcase-links" in html


def test_showcase_viewer_script_prioritizes_potree_splat_and_reports():
    """展示入口要突出 Potree、Gaussian Splatting 和报告交付物。"""
    script = (FRONTEND / "viewer.js").read_text(encoding="utf-8")

    assert "Potree" in script
    assert "Gaussian Splatting" in script
    assert "质量报告" in script
    assert "生产运行报告" in script
    assert "asset_index.json" in script
