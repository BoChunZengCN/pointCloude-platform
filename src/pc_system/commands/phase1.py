import json
import sys
from pathlib import Path

from pc_system.asset import LasAssetInfo, build_asset_metadata, write_asset_metadata
from pc_system.config import ProjectConfig
from pc_system.las_reader import LasReaderDependencyError, read_las_info
from pc_system.module_status import build_module_status_report, write_module_status_report
from pc_system.open3d_rule_segmentation_adapter import (
    Open3DRunner,
    open3d_rule_segmentation_adapter,
    subprocess_runner as open3d_subprocess_runner,
)
from pc_system.pdal_slice_adapter import PdalRunner, pdal_slice_adapter, subprocess_runner as pdal_subprocess_runner
from pc_system.potree_publisher import PotreePublishRequest, PotreeRunner, publish_potree, subprocess_runner
from pc_system.preview import publish_preview
from pc_system.qa import build_quality_report, write_quality_report
from pc_system.rule_segmentation import (
    RuleSegmentationRequest,
    build_rule_segmentation_plan,
    execute_rule_segmentation_plan,
    write_rule_segmentation_plan,
)
from pc_system.segmentation_summary import build_segmentation_summary, write_segmentation_summary
from pc_system.slice_executor import SliceAdapter, execute_slice_plan, placeholder_slice_adapter
from pc_system.slice_plan import SliceRequest, build_slice_plan, write_slice_plan


def _demo_las_info() -> LasAssetInfo:
    """生成 demo 用的最小 LAS 元数据。"""

    return LasAssetInfo(
        point_count=1,
        bounds={"min": [0.0, 0.0, 0.0], "max": [0.0, 0.0, 0.0]},
        has_rgb=True,
        has_classification=False,
        has_crs=False,
        scale=[0.001, 0.001, 0.001],
        offset=[0.0, 0.0, 0.0],
        point_format="demo",
    )


def run_init(project_root: Path) -> int:
    """初始化项目目录。"""

    ProjectConfig(project_root=project_root).ensure_directories()
    return 0


def run_demo_phase1(project_root: Path, las_path: Path) -> int:
    """用模拟元数据执行阶段一完整流程。"""

    return run_phase1_workflow(project_root, las_path, _demo_las_info())


def run_phase1_workflow(project_root: Path, las_path: Path, las_info: LasAssetInfo) -> int:
    """执行阶段一公共流程。"""

    paths = ProjectConfig(project_root=project_root).ensure_directories()
    metadata = build_asset_metadata(las_path, las_info)
    # 所有派生文件按 asset_id 分目录存放，便于一个项目下管理多个点云资产。
    asset_dir = paths["assets"] / metadata["asset_id"]
    report_dir = paths["reports"] / metadata["asset_id"]
    preview_dir = paths["previews"] / metadata["asset_id"]

    # 阶段一的三个核心产物：资产元数据、质检报告、预览入口。
    write_asset_metadata(metadata, asset_dir / "asset.json")
    report = build_quality_report(metadata)
    write_quality_report(report, report_dir)
    publish_preview(metadata, preview_dir)
    return 0


def _asset_dir(project_root: Path, asset_id: str) -> Path:
    """统一通过 ProjectConfig 解析资产目录，避免各命令各自拼路径。"""

    return ProjectConfig(project_root=project_root).paths()["assets"] / asset_id


def _load_asset_metadata(metadata_path: Path) -> dict:
    """读取 asset.json；缺失时抛出 FileNotFoundError 由调用方转成退出码。"""

    return json.loads(metadata_path.read_text(encoding="utf-8"))


def run_ingest(project_root: Path, las_path: Path, las_info_reader=read_las_info) -> int:
    """读取真实 LAS/LAZ 元数据，并执行阶段一公共流程。"""

    try:
        las_info = las_info_reader(las_path)
    except LasReaderDependencyError as exc:
        print(exc, file=sys.stderr)
        return 2
    return run_phase1_workflow(project_root, las_path, las_info)


def run_plan_slice(
    project_root: Path,
    asset_id: str,
    name: str,
    min_bounds: list[float],
    max_bounds: list[float],
    voxel_size: float | None,
    output_format: str,
) -> int:
    """读取资产元数据并写出 M5 切片计划。"""

    asset_dir = _asset_dir(project_root, asset_id)
    metadata_path = asset_dir / "asset.json"
    try:
        metadata = _load_asset_metadata(metadata_path)
    except FileNotFoundError:
        print(f"Asset metadata not found: {metadata_path}", file=sys.stderr)
        return 2

    request = SliceRequest(
        name=name,
        bounds={"min": min_bounds, "max": max_bounds},
        voxel_size=voxel_size,
        output_format=output_format,
    )
    plan = build_slice_plan(metadata, request)
    write_slice_plan(plan, asset_dir / "slices" / name)
    return 0


def run_execute_slice(
    project_root: Path,
    asset_id: str,
    slice_name: str,
    slice_adapter: SliceAdapter = placeholder_slice_adapter,
    engine: str = "placeholder",
    pdal_path: Path = Path("pdal"),
    pdal_runner: PdalRunner = pdal_subprocess_runner,
) -> int:
    """执行已存在的 M5 切片计划。"""

    plan_path = _asset_dir(project_root, asset_id) / "slices" / slice_name / "slice_plan.json"
    if not plan_path.exists():
        print(f"Slice plan not found: {plan_path}", file=sys.stderr)
        return 2
    if engine == "pdal":
        # 将 PDAL 参数包装成 SliceAdapter 协议，保持 execute_slice_plan 的入口不变。
        def adapter(plan: dict, destination: Path):
            return pdal_slice_adapter(plan, destination, pdal_path=pdal_path, runner=pdal_runner)

        execute_slice_plan(plan_path, adapter)
        return 0
    execute_slice_plan(plan_path, slice_adapter)
    return 0


def run_publish_potree(
    project_root: Path,
    asset_id: str,
    converter_path: Path,
    potree_runner: PotreeRunner = subprocess_runner,
) -> int:
    """读取资产元数据，并调用 PotreeConverter 生成 Potree 预览目录。"""

    asset_dir = _asset_dir(project_root, asset_id)
    try:
        metadata = _load_asset_metadata(asset_dir / "asset.json")
    except FileNotFoundError:
        print(f"Asset metadata not found: {asset_dir / 'asset.json'}", file=sys.stderr)
        return 2
    output_dir = ProjectConfig(project_root=project_root).paths()["previews"] / asset_id / "potree"
    publish_potree(
        PotreePublishRequest(
            asset_id=asset_id,
            source_file=Path(metadata["file"]["path"]),
            output_dir=output_dir,
            converter_path=converter_path,
        ),
        runner=potree_runner,
    )
    return 0


def _slice_dir(project_root: Path, asset_id: str, slice_name: str) -> Path:
    """统一解析切片目录。"""

    return _asset_dir(project_root, asset_id) / "slices" / slice_name


def run_plan_rule_segment(
    project_root: Path,
    asset_id: str,
    slice_name: str,
    name: str,
    methods: list[str],
) -> int:
    """读取切片计划并写出 M6 规则分割计划。"""

    slice_plan_path = _slice_dir(project_root, asset_id, slice_name) / "slice_plan.json"
    if not slice_plan_path.exists():
        print(f"Slice plan not found: {slice_plan_path}", file=sys.stderr)
        return 2
    slice_plan = json.loads(slice_plan_path.read_text(encoding="utf-8"))
    request = RuleSegmentationRequest(name=name, methods=methods)
    plan = build_rule_segmentation_plan(slice_plan, request)
    write_rule_segmentation_plan(plan, _slice_dir(project_root, asset_id, slice_name) / "segments" / name)
    return 0


def run_execute_rule_segment(
    project_root: Path,
    asset_id: str,
    slice_name: str,
    name: str,
    engine: str = "placeholder",
    python_path: Path = Path("python"),
    script_path: Path = Path("open3d_rule_segment.py"),
    open3d_runner: Open3DRunner = open3d_subprocess_runner,
) -> int:
    """执行已有 M6 规则分割计划。"""

    plan_path = _slice_dir(project_root, asset_id, slice_name) / "segments" / name / "rule_segmentation_plan.json"
    if not plan_path.exists():
        print(f"Rule segmentation plan not found: {plan_path}", file=sys.stderr)
        return 2
    if engine == "open3d":
        # 将 Open3D 脚本参数包装成 RuleSegmentationAdapter 协议。
        def adapter(plan: dict, destination: Path):
            return open3d_rule_segmentation_adapter(
                plan,
                destination,
                python_path=python_path,
                script_path=script_path,
                runner=open3d_runner,
            )

        execute_rule_segmentation_plan(plan_path, adapter)
        return 0
    execute_rule_segmentation_plan(plan_path)
    return 0


def run_report_rule_segment(
    project_root: Path,
    asset_id: str,
    slice_name: str,
    name: str,
) -> int:
    """读取规则分割 labels JSON，并生成摘要报告。"""

    segment_dir = _slice_dir(project_root, asset_id, slice_name) / "segments" / name
    plan_path = segment_dir / "rule_segmentation_plan.json"
    if not plan_path.exists():
        print(f"Rule segmentation plan not found: {plan_path}", file=sys.stderr)
        return 2
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    labels_path = segment_dir / plan["output"]["file_name"]
    if not labels_path.exists():
        print(f"Rule segmentation labels not found: {labels_path}", file=sys.stderr)
        return 2
    labels_payload = json.loads(labels_path.read_text(encoding="utf-8"))
    summary = build_segmentation_summary(labels_payload)
    report_dir = ProjectConfig(project_root=project_root).paths()["reports"] / asset_id / "segments" / slice_name / name
    write_segmentation_summary(summary, report_dir)
    return 0


def run_module_status(project_root: Path) -> int:
    """写出 Phase 1 模块完成度报告。"""

    report = build_module_status_report()
    output_dir = ProjectConfig(project_root=project_root).paths()["reports"]
    write_module_status_report(report, output_dir)
    return 0
