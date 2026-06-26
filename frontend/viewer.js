const REGISTRY_URL = "../workspace/data/assets/asset_index.json";

const FALLBACK_ASSET = {
  asset_id: "site-a-las",
  file_name: "sample.las",
  preview_paths: {
    potree_manifest: "previews/site-a-las/potree_manifest.json",
    phase2_viewer: "previews/site-a-las/phase2_viewer_manifest.json",
  },
  report_paths: {
    quality_report: "reports/site-a-las/quality_report.html",
    production_report: "reports/production_runs/site-a-las/production_run_report.md",
  },
};

async function loadRegistry() {
  try {
    const response = await fetch(REGISTRY_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("asset_index.json unavailable");
    }
    return await response.json();
  } catch (error) {
    return { asset_count: 1, assets: [FALLBACK_ASSET] };
  }
}

function deliveryLinks(asset) {
  return [
    {
      kind: "potree",
      title: "Potree",
      label: "点云查看器",
      href: `../workspace/${asset.preview_paths.potree_manifest}`,
    },
    {
      kind: "splat",
      title: "Gaussian Splatting",
      label: "Splat 视觉成果",
      href: `../workspace/${asset.preview_paths.phase2_viewer}`,
    },
    {
      kind: "report",
      title: "质量报告",
      label: "QA / 质检结果",
      href: `../workspace/${asset.report_paths.quality_report}`,
    },
    {
      kind: "report",
      title: "生产运行报告",
      label: "Phase 3 交付记录",
      href: `../workspace/${asset.report_paths.production_report}`,
    },
  ];
}

function renderShowcase(registry) {
  const asset = registry.assets?.[0] || FALLBACK_ASSET;
  document.getElementById("showcase-summary").textContent = `${asset.asset_id} · ${asset.file_name} · ${registry.asset_count} 个资产可展示`;
  const links = deliveryLinks(asset).map((item) => {
    const link = document.createElement("a");
    link.className = "showcase-card";
    link.dataset.kind = item.kind;
    link.href = item.href;
    link.innerHTML = `<span></span><strong></strong>`;
    link.querySelector("span").textContent = item.label;
    link.querySelector("strong").textContent = item.title;
    return link;
  });
  document.getElementById("showcase-links").replaceChildren(...links);
}

loadRegistry().then(renderShowcase);
