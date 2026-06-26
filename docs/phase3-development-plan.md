# Phase 3 Development Plan

## Goal

Move the Phase 1 and Phase 2 adapter-based system toward production readiness by validating external tools, preparing end-to-end production runs, and recording deployment readiness.

## Module Order

1. P3-M1 Production tool check
2. P3-M2 Production pipeline plan
3. P3-M3 Production run report
4. P3-M4 Deployment package checklist

## Implemented Boundaries

### P3-M1 Production Tool Check

P3-M1 validates whether configured external tools exist before a production run starts:

- `pc_system.phase3_tool_check.ToolSpec`
- `build_tool_check_report`
- `write_tool_check_report`
- CLI command: `phase3-tool-check`

The command writes:

```text
reports/phase3_tool_check.json
reports/phase3_tool_check.md
```

Supported tool path checks:

- `--fls-converter`
- `--pdal-path`
- `--potree-converter`
- `--gaussian-trainer`
- `--open3d-script`

Current boundary:

- The check validates configured file paths only
- Missing configured required tools mark the report as blocked
- Unconfigured optional tools are reported as `not_configured`
- Version probing and sample execution checks are deferred to later Phase 3 modules

### P3-M2 Production Pipeline Plan

P3-M2 writes an auditable plan that sequences the existing Phase 1, Phase 2, and Phase 3 commands without running heavy external tools automatically:

```text
pc-system plan-production-run --project-root <workspace> --asset-id <asset_id>
```

The command writes `reports/production_runs/<asset_id>/production_run_plan.json` and `.md`.

### P3-M3 Production Run Report

P3-M3 reads a production run plan and writes a run report summarizing step status:

```text
pc-system report-production-run --project-root <workspace> --asset-id <asset_id>
```

The command writes `reports/production_runs/<asset_id>/production_run_report.json` and `.md`.

### Asset Registry

The asset registry scans `data/assets/*/asset.json` and writes:

```text
data/assets/asset_index.json
data/assets/asset_index.md
```

CLI command:

```text
pc-system index-assets --project-root <workspace>
```

### P3-M4 Deployment Package Checklist

P3-M4 checks whether a deployable delivery package has the key artifacts needed for handoff:

```text
pc-system check-deployment-package --project-root <workspace> --asset-id <asset_id>
```

The command writes:

```text
reports/deployment/<asset_id>/deployment_checklist.json
reports/deployment/<asset_id>/deployment_checklist.md
```

Current required checks:

- `data/assets/asset_index.json`
- `reports/production_runs/<asset_id>/production_run_plan.json`
- `reports/production_runs/<asset_id>/production_run_report.json`
- `reports/phase3_tool_check.json`
- `previews/<asset_id>/phase2_viewer_manifest.json`

Optional checks currently include quality and segmentation HTML reports.

## Phase 3 Completion State

P3-M1 through P3-M4 are implemented and covered by tests. Remaining production-hardening work should focus on real job execution state updates, packaged artifact export, and deployment automation.


