# NEXT FOR TRAE — read before Dashboard/GIS work

## Protected baseline (do not overwrite casually)

As of **2026-07-26**, the product-complete Dashboard L1/L2 + GIS state is pinned:

| Item | Value |
|------|--------|
| Annotated tag | `baseline/l1-l2-gis-20260726` |
| Note | `_handoff/BASELINE_L1L2_GIS_20260726.md` |
| Branch when pinned | `trae/workspace-nav-s02s03` |

**Trae must not** change Dashboard GIS L1/L2, home master layout, Cesium GIS overview module, or related L1/L2 panels **without an Issue that explicitly authorizes that scope**.

If a task only covers Workspace / Assistant / a single modal polish, keep diffs off:

- `src/views/DashboardPage.vue` (except trivial wiring already required by scoped Issue)
- `src/components/master/*`
- `src/modules/traffic-gis-overview/**`
- `src/components/gis/*` home embedding paths
- Core L1/L2 KPI/panel composition unless the Issue says otherwise

Prefer restoring from the tag if accidental overwrites happen.

## Prior task context (GIS lazy-load — historical)

Earlier handoff below described Cesium chunk lazy-load for `/gis-preview`. That work is **out of band** relative to the protected baseline unless re-scoped in a new Issue. Do not treat the old “允许修改 GisPreviewPage / GisOverviewCesiumPanel” note as permission to rewrite L1/L2 home.

---

## Legacy brief (reference only): Cesium lazy-load chunking

第二阶段已完成首页 `useRealGisOnDashboard` 开关与 `GisOverviewCesiumPanel` 异步组件。若再做彻底懒加载分包，须单独 Issue，且验收后不得破坏 `baseline/l1-l2-gis-20260726` 的视觉与交互完整态。

允许修改（仅当 Issue 明确要求）：

- `src/views/GisPreviewPage.vue`
- `src/components/gis/GisOverviewCesiumPanel.vue`
- 必要时轻微调整 `vite.config.ts`

默认禁止修改（受 baseline 保护）：

- `src/views/DashboardPage.vue`
- `src/components/panels/GisOverviewPanel.vue` / master GIS section
- `src/modules/traffic-gis-overview/`（除非 Issue 点名且含回归清单）

## Related recovery docs

- `_handoff/BASELINE_L1L2_GIS_20260726.md`
- `_handoff/Cursor_L1L2_GIS完整态恢复说明_20260726.md`
- `_handoff/Cursor_完整态校核_20260726.md`
- `_handoff/Cursor_首页回归回退说明_20260726.md`
