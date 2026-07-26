# NEXT_FOR_TRAE

**状态：** READY_for_trae  
**更新日期：** 2026-07-26  
**当前唯一任务单：** `_handoff/Trae实施任务单_Workspace右侧碳与月报_V1.0_20260726.md`  
**设计依据：** `_handoff/Workspace右侧_碳与月报模块设计_V0.1_20260726.md`  
**开工基线：** `baseline/workspace-ui-20260726`（说明：`_handoff/BASELINE_Workspace_UI_20260726.md`）  
**首页保护基线（勿删）：** `baseline/l1-l2-gis-20260726`

## 本 sprint 指令

在 **数据填报（Workspace）→ 填报概览** 右侧栏增加与首页同源的 **碳摘要** + **月报摘要**（两张 `.ws-panel`）。保留紧凑 ESG 助手入口；今日重点降级 ≤2 条；下钻由 `WorkspacePage` 宿主挂载既有 E04 / 月报模态。

**红线：** 禁止碰 Dashboard / GIS / e01–e03/s02 / HeaderNav / Assistant / `layout.scss`·全局 tokens / 首页 `CarbonBenefitPanel` 源码重写（可只读 API）/ S01–G04 模态内部。**仅允许** `WorkspacePage`、`components/workspace/**`、`workspace.scss`，及 `api.ts` 薄读调用（无新 schema）。版式必须统一现有 Workspace UI，禁止新视觉语言。

**数据：** `GET /api/dashboard/panels`（碳）+ `GET /api/monthly-report/readiness`（月报）；禁止硬编码 6175；UI 禁止演示/测试 chrome。

**回退：** `git switch --detach baseline/workspace-ui-20260726`

## 旧 sprint 已取消 / 已取代 / 并行

| 文档 | 处置 |
|------|------|
| `_handoff/Trae实施任务单_数据填报页续作_仅Workspace_V1.0_20260726.md` | **并行收尾可继续**；NEXT 主指针为本碳/月报单；冲突以本单红线为准 |
| `_handoff/Trae实施任务单_Workspace入口与S02S03小改_V1.0_20260726.md` | **SUPERSEDED** |
| `_handoff/Trae实施任务单_Workspace智能入库真解析演示_V1.0_20260726.md` | 旁路能力相关；非主指针 |
| Header 大屏视觉统一 | **HOLD** |
| 助手 DB 驱动问答 | **OUT** |

## 基线

- Workspace 开工/回退：`baseline/workspace-ui-20260726` → `_handoff/BASELINE_Workspace_UI_20260726.md`
- 首页 L1/L2 GIS：`baseline/l1-l2-gis-20260726` → 仍有效，**两 tag 共存**

## 完成后

按任务单 §验收与交付包约定收口；等待 Codex 验收。勿默认写满 `_handoff/TRAE_DONE_REPORT.md` 除非本单约定要求。
