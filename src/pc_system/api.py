import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pc_system.config import ProjectConfig


def _registry_path(project_root: Path) -> Path:
    """返回项目资产索引路径。"""

    return ProjectConfig(project_root=project_root).paths()["assets"] / "asset_index.json"


def _load_registry(project_root: Path) -> dict:
    """读取资产索引；缺失时返回空 registry，便于前端先启动。"""

    path = _registry_path(project_root)
    if not path.exists():
        return {"schema_version": "1.0", "asset_count": 0, "assets": []}
    return json.loads(path.read_text(encoding="utf-8"))


def create_app(project_root: Path) -> FastAPI:
    """创建最小 API 应用。"""

    app = FastAPI(title="Point Cloud Platform API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        """健康检查，返回当前绑定的项目目录。"""

        return {"status": "ok", "project_root": str(project_root)}

    @app.get("/assets")
    def list_assets() -> dict:
        """返回项目资产索引。"""

        return _load_registry(project_root)

    @app.get("/assets/{asset_id}")
    def get_asset(asset_id: str) -> dict:
        """返回单个资产索引条目。"""

        registry = _load_registry(project_root)
        for asset in registry["assets"]:
            if asset["asset_id"] == asset_id:
                return asset
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

    return app


app = create_app(Path(os.environ.get("PC_SYSTEM_PROJECT_ROOT", "workspace")))
