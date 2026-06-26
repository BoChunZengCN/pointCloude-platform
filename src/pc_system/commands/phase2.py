import sys
from pathlib import Path

from pc_system.config import ProjectConfig
from pc_system.fls_ingest import (
    FlsIngestRequest,
    FlsRunner,
    build_fls_ingest_plan,
    execute_fls_ingest_plan,
    subprocess_runner as fls_subprocess_runner,
    write_fls_ingest_plan,
)
from pc_system.gaussian_splatting import (
    GaussianRunner,
    GaussianSplatRequest,
    build_gaussian_splat_plan,
    execute_gaussian_splat_plan,
    subprocess_runner as gaussian_subprocess_runner,
    write_gaussian_splat_plan,
)
from pc_system.phase2_status import build_phase2_status_report, write_phase2_status_report
from pc_system.phase2_viewer import build_phase2_viewer_manifest, publish_phase2_viewer


def _fls_ingest_dir(project_root: Path, asset_id: str) -> Path:
    """统一解析 Phase 2 FLS 接入目录。"""

    return ProjectConfig(project_root=project_root).ensure_directories()["data_raw"] / "fls" / asset_id


def run_plan_fls_ingest(
    project_root: Path,
    asset_id: str,
    raw_files: list[Path],
    output_las: Path,
    registration: str,
) -> int:
    """写出 Phase 2 FLS 接入计划。"""

    plan = build_fls_ingest_plan(
        FlsIngestRequest(
            asset_id=asset_id,
            raw_files=raw_files,
            output_las=output_las,
            registration=registration,
        )
    )
    write_fls_ingest_plan(plan, _fls_ingest_dir(project_root, asset_id))
    return 0


def run_execute_fls_ingest(
    project_root: Path,
    asset_id: str,
    converter_path: Path,
    fls_runner: FlsRunner = fls_subprocess_runner,
) -> int:
    """执行 Phase 2 FLS 接入计划。"""

    plan_path = _fls_ingest_dir(project_root, asset_id) / "fls_ingest_plan.json"
    if not plan_path.exists():
        print(f"FLS ingest plan not found: {plan_path}", file=sys.stderr)
        return 2
    execute_fls_ingest_plan(plan_path, converter_path=converter_path, runner=fls_runner)
    return 0


def _splat_dir(project_root: Path, asset_id: str, name: str) -> Path:
    """统一解析 Phase 2 Gaussian Splatting 输出目录。"""

    return ProjectConfig(project_root=project_root).paths()["previews"] / asset_id / "splats" / name


def run_plan_gaussian_splat(
    project_root: Path,
    asset_id: str,
    name: str,
    source_las: Path,
    iterations: int,
) -> int:
    """写出 Phase 2 Gaussian Splatting 计划。"""

    output_dir = _splat_dir(project_root, asset_id, name)
    plan = build_gaussian_splat_plan(
        GaussianSplatRequest(
            name=name,
            source_las=source_las,
            output_dir=output_dir,
            iterations=iterations,
        )
    )
    write_gaussian_splat_plan(plan, output_dir)
    return 0


def run_execute_gaussian_splat(
    project_root: Path,
    asset_id: str,
    name: str,
    trainer_path: Path,
    python_path: Path,
    gaussian_runner: GaussianRunner = gaussian_subprocess_runner,
) -> int:
    """执行 Phase 2 Gaussian Splatting 计划。"""

    plan_path = _splat_dir(project_root, asset_id, name) / "gaussian_splat_plan.json"
    if not plan_path.exists():
        print(f"Gaussian Splatting plan not found: {plan_path}", file=sys.stderr)
        return 2
    execute_gaussian_splat_plan(
        plan_path,
        trainer_path=trainer_path,
        python_path=python_path,
        runner=gaussian_runner,
    )
    return 0


def run_publish_phase2_viewer(
    project_root: Path,
    asset_id: str,
    potree_path: Path | None,
    splat_path: Path | None,
    reports: list[Path],
) -> int:
    """发布 Phase 2 统一预览入口。"""

    manifest = build_phase2_viewer_manifest(asset_id, potree_path, splat_path, reports)
    output_dir = ProjectConfig(project_root=project_root).paths()["previews"] / asset_id
    publish_phase2_viewer(manifest, output_dir)
    return 0


def run_phase2_status(project_root: Path) -> int:
    """写出 Phase 2 模块完成度报告。"""

    report = build_phase2_status_report()
    output_dir = ProjectConfig(project_root=project_root).paths()["reports"]
    write_phase2_status_report(report, output_dir)
    return 0


