from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_frontend_prefers_workspace_asset_registry_before_sample_data():
    """FE-M2 工作台应优先读取真实 workspace 资产索引，再回退样例数据。"""
    script = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert "WORKSPACE_REGISTRY_URL" in script
    assert "../workspace/data/assets/asset_index.json" in script
    assert "normalizeRegistryProject" in script
    assert script.index("WORKSPACE_REGISTRY_URL") < script.index("DATA_URL")


def test_frontend_exposes_registry_empty_state_copy():
    """真实 workspace 没有资产时，页面需要给出可理解的空状态。"""
    script = (FRONTEND / "app.js").read_text(encoding="utf-8")

    assert "未发现真实资产索引" in script
    assert "pc-system index-assets" in script
