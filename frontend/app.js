const WORKSPACE_REGISTRY_URL = "../workspace/data/assets/asset_index.json";
const DATA_URL = "data/sample-project.json";

const DEFAULT_PROJECT_DATA = {
  project_name: "脚架式点云示例项目",
  summary: "已处理 LAS/LAZ 资产进入生产工作流，Phase 1 与 Phase 2 已具备可审计输出，Phase 3 正在补齐生产化计划。",
  asset: {
    id: "site-a-las",
    name: "三维扫描大厅样例",
    format: "LAS/LAZ",
    source: "processed_las",
    point_count: 12840000,
    colorized: true,
    coordinate_system: "统一工程坐标",
    bounds: "X 0-38m, Y 0-22m, Z 0-7m",
  },
  workflow: [
    {
      phase: "Phase 1",
      name: "LAS 资产处理",
      status: "completed",
      command: "pc-system ingest / demo-phase1",
      output: "asset.json, quality_report.html, preview_manifest.json",
    },
    {
      phase: "Phase 1",
      name: "切片与规则分割",
      status: "completed",
      command: "pc-system plan-slice / execute-rule-segment",
      output: "slice_plan.json, segmentation_summary.html",
    },
    {
      phase: "Phase 2",
      name: "Potree 与 Splat 入口",
      status: "completed",
      command: "pc-system publish-phase2-viewer",
      output: "phase2_viewer_manifest.json",
    },
    {
      phase: "Phase 3",
      name: "生产工具检查",
      status: "completed",
      command: "pc-system phase3-tool-check",
      output: "phase3_tool_check.md",
    },
    {
      phase: "Phase 3",
      name: "生产运行计划",
      status: "planned",
      command: "pc-system plan-production-run",
      output: "production_run_plan.json",
    },
  ],
  reports: [
    { name: "质量报告", kind: "QA", href: "../workspace/reports/site-a-las/quality_report.html", status: "ready" },
    { name: "分割汇总", kind: "Segmentation", href: "../workspace/reports/site-a-las/segments/room-a/baseline/segmentation_summary.html", status: "ready" },
    { name: "Phase 2 状态", kind: "Status", href: "../workspace/reports/phase2_status.md", status: "ready" },
    { name: "Phase 3 工具检查", kind: "Production", href: "../workspace/reports/phase3_tool_check.md", status: "ready" },
  ],
};

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

function statusText(status) {
  const names = {
    completed: "已完成",
    planned: "计划中",
    blocked: "阻塞",
    ready: "可用",
  };
  return names[status] || status;
}

function setText(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = value;
  }
}

function createFact(term, value) {
  const fragment = document.createDocumentFragment();
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = term;
  dd.textContent = value;
  fragment.append(dt, dd);
  return fragment;
}

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${url}`);
  }
  return await response.json();
}

function normalizeRegistryProject(registry) {
  const firstAsset = registry.assets?.[0];
  if (!firstAsset) {
    return {
      ...DEFAULT_PROJECT_DATA,
      project_name: "未发现真实资产索引",
      summary: "请先运行 pc-system index-assets 生成 workspace/data/assets/asset_index.json，然后刷新工作台。",
      asset_count: 0,
    };
  }

  return {
    project_name: "真实点云项目工作台",
    summary: `已从 workspace 读取 ${registry.asset_count} 个资产，当前展示 ${firstAsset.asset_id}。`,
    asset_count: registry.asset_count,
    asset: {
      id: firstAsset.asset_id,
      name: firstAsset.file_name || firstAsset.asset_id,
      format: "LAS/LAZ",
      source: firstAsset.source_path || "workspace_registry",
      point_count: firstAsset.point_count || 0,
      colorized: Boolean(firstAsset.has_rgb),
      coordinate_system: "来自 asset_index.json",
      bounds: JSON.stringify(firstAsset.bounds || {}),
    },
    workflow: DEFAULT_PROJECT_DATA.workflow,
    reports: [
      { name: "质量报告", kind: "QA", href: `../workspace/${firstAsset.report_paths.quality_report}`, status: "ready" },
      { name: "生产运行计划", kind: "Production", href: `../workspace/${firstAsset.report_paths.production_plan}`, status: "ready" },
      { name: "生产运行报告", kind: "Production", href: `../workspace/${firstAsset.report_paths.production_report}`, status: "ready" },
      { name: "Phase 2 Viewer", kind: "Viewer", href: `../workspace/${firstAsset.preview_paths.phase2_viewer}`, status: "ready" },
    ],
  };
}

async function fetchProjectData() {
  try {
    return normalizeRegistryProject(await loadJson(WORKSPACE_REGISTRY_URL));
  } catch (workspaceError) {
    try {
      return await loadJson(DATA_URL);
    } catch (sampleError) {
      // 直接双击 file:// 打开时，部分浏览器会拦截本地 JSON fetch；此时使用内置样例数据。
      return DEFAULT_PROJECT_DATA;
    }
  }
}

function renderAsset(project) {
  const { asset } = project;
  setText("project-title", project.project_name);
  setText("project-summary", project.summary);
  setText("metric-assets", String(project.asset_count ?? 1));
  setText("metric-points", formatNumber(asset.point_count));
  setText("metric-phases", new Set(project.workflow.map((step) => step.phase)).size.toString());
  setText("asset-format", asset.format);

  const detail = document.getElementById("asset-detail");
  detail.replaceChildren(
    assetPill("资产", asset.name),
    assetPill("坐标", asset.coordinate_system),
    assetPill("范围", asset.bounds),
  );

  const facts = document.getElementById("asset-facts");
  facts.replaceChildren(
    createFact("资产 ID", asset.id),
    createFact("格式", asset.format),
    createFact("颜色", asset.colorized ? "RGB 已保留" : "未记录"),
    createFact("来源", asset.source),
    createFact("点数", formatNumber(asset.point_count)),
  );
}

function assetPill(label, value) {
  const node = document.createElement("div");
  node.className = "asset-pill";
  const labelNode = document.createElement("span");
  const valueNode = document.createElement("strong");
  labelNode.textContent = label;
  valueNode.textContent = value;
  node.append(labelNode, valueNode);
  return node;
}

function renderWorkflow(project) {
  const list = document.getElementById("workflow-list");
  const items = project.workflow.map((step) => {
    const node = document.createElement("article");
    node.className = "workflow-step";
    node.dataset.status = step.status;
    node.innerHTML = `
      <span class="workflow-phase"></span>
      <h3 class="workflow-name"></h3>
      <div class="workflow-command"></div>
      <p class="workflow-output"></p>
      <span class="status-chip"></span>
    `;
    node.querySelector(".workflow-phase").textContent = step.phase;
    node.querySelector(".workflow-name").textContent = step.name;
    node.querySelector(".workflow-command").textContent = step.command;
    node.querySelector(".workflow-output").textContent = step.output;
    node.querySelector(".status-chip").textContent = statusText(step.status);
    return node;
  });

  list.replaceChildren(...items);
  const hasBlocked = project.workflow.some((step) => step.status === "blocked");
  const hasPlanned = project.workflow.some((step) => step.status === "planned");
  setText("workflow-ready", hasBlocked ? "需处理" : hasPlanned ? "可推进" : "已就绪");
}

function renderReports(project) {
  const list = document.getElementById("report-list");
  const links = project.reports.map((report) => {
    const link = document.createElement("a");
    link.className = "report-link";
    link.href = report.href;
    link.innerHTML = `
      <span>
        <span class="report-name"></span>
        <span class="report-kind"></span>
      </span>
      <span class="report-status"></span>
    `;
    link.querySelector(".report-name").textContent = report.name;
    link.querySelector(".report-kind").textContent = report.kind;
    link.querySelector(".report-status").textContent = statusText(report.status);
    return link;
  });
  list.replaceChildren(...links);
}

function drawPointCloudPreview(project) {
  const canvas = document.getElementById("project-preview");
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;

  context.clearRect(0, 0, width, height);
  context.fillStyle = "#101713";
  context.fillRect(0, 0, width, height);

  // 使用确定性点阵模拟脚架式扫描点云的密度变化，便于无后端时也能观察工作台状态。
  for (let i = 0; i < 1800; i += 1) {
    const ring = (i % 120) / 120;
    const sweep = i * 0.037;
    const radius = 70 + ring * 310 + Math.sin(i * 0.013) * 18;
    const x = width / 2 + Math.cos(sweep) * radius * 1.2;
    const y = height / 2 + Math.sin(sweep) * radius * 0.52 + Math.cos(i * 0.011) * 28;
    const depth = Math.max(0, Math.min(1, y / height));
    context.fillStyle = `rgba(${80 + depth * 80}, ${180 - depth * 40}, ${150 + depth * 70}, ${0.28 + ring * 0.55})`;
    context.fillRect(x, y, 1.6 + ring * 1.8, 1.6 + ring * 1.8);
  }

  context.strokeStyle = "rgba(255, 255, 255, 0.18)";
  context.lineWidth = 1;
  for (let row = 1; row < 4; row += 1) {
    const y = (height / 4) * row;
    context.beginPath();
    context.moveTo(32, y);
    context.lineTo(width - 32, y);
    context.stroke();
  }

  context.fillStyle = "rgba(255, 255, 255, 0.82)";
  context.font = "20px Segoe UI, Microsoft YaHei, sans-serif";
  context.fillText(project.asset.name, 32, 44);
  context.font = "14px Segoe UI, Microsoft YaHei, sans-serif";
  context.fillText(`${project.asset.format} · ${formatNumber(project.asset.point_count)} points`, 32, 70);
}

async function initWorkbench() {
  const project = await fetchProjectData();
  renderAsset(project);
  renderWorkflow(project);
  renderReports(project);
  drawPointCloudPreview(project);
}

initWorkbench();


