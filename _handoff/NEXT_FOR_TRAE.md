# NEXT_FOR_TRAE

**状态：** BASELINED — 助手+智能填报当前产品态已打基线；智能入库 V0.2 门禁仍 PARTIAL  
**更新日期：** 2026-07-28  
**校核：** `_handoff/ESG智能入库一页式/Cursor校核_V0.2_20260726.md`  
**分支：** `trae/carbon-page`（SmartEntry 已接默认填报；碳页组件未跟踪且**未接线**）  
**当前基线 Tag：** `baseline/assistant-smartentry-20260728`（说明：`_handoff/BASELINE_assistant_smartentry_20260728.md`）

**当前任务单（主指针）：**

| 工作流 | 任务书 | 校核结论 |
|--------|--------|----------|
| C · ESG智能数据填报一页式 | `_handoff/ESG智能入库一页式/ESG智能数据填报_一页式工作台设计与联调任务书_V0.2_20260726.md` | **PARTIAL** |
| 碳核算独立页（并行 · 暂停） | `_handoff/碳核算与月报独立页/Trae实施任务单_碳核算独立页_V1.0_20260726.md` | **PAUSED / 不接线** — 用户只要智能入库 |
| ESG智能助手 · 回答展示业务化 V1.1 | `_handoff/ESG智能助手_回答展示业务化优化_V1.1实施说明_20260727.md` | **IMPLEMENTED（前端）** — 业务卡片结构；上级检查 PackageCard+11类统计保留 |
| ESG智能助手 · 问答设计更新（主） | `_handoff/ESG智能助手_问答设计更新_V1.0_20260727.md` | **ACTIVE / for review** — 标准答法 + 意图全表 + 样例回答（仅助手 Q&A，非全平台） |
| ESG智能助手 · 库驱动问答 | `_handoff/ESG智能助手_库驱动问答与合规资料包设计_V0.2_20260727.md` | **IMPLEMENTED** — 每问独立 API 答 + 上级检查合规资料包（无 DEMO/演示字样）；碳页仍不接线 |
| ESG智能助手 · 上级环保检查资料包校核 | `_handoff/ESG智能助手_上级环保检查资料包_设计问答与校核报告_20260727.md` | **姊妹校核** — 设计问答深答 + 现状校核；与问答设计更新交叉引用 |

**当前开工/回退基线：** `baseline/assistant-smartentry-20260728`  
**Workspace UI 旧基线：** `baseline/workspace-ui-20260726`（保留）  
**首页保护基线：** `baseline/l1-l2-gis-20260726`（勿删）

---

## V0.2 一页式 — 已确认到位

- `WorkspaceSmartUpload.vue`：idle / uploading / parsing / ready 双栏 / done / failed  
- `WorkspacePage.vue`：默认 `smart-upload`；仅该 Tab 隐藏 `WorkspaceNav`  
- `dashboard.mock.ts`：顶栏「ESG智能数据填报」  
- 交付包 `交付_ESG智能入库一页式/`  
- `npm run check` EXIT:0；红线文件（Dashboard GIS / carbon route / monthly）本 diff 未破坏  

## V0.2 — 仍须补齐（未过 §12 门禁）

1. DEMO 资料包 A–D + 业务底数 + 幂等 init/cleanup（§7–9）  
2. 真原文预览与来源定位（或书面降级例外经用户接受）  
3. 多文件按资料包解析（现仅解析最后一文件）  
4. 疑似重复决策流（非仅 toast）  
5. 确认入库 DB 回查证据 + demo 隔离；交付说明已自承**未改后端**  
6. 设计图 PNG 补入同目录  

**在以上补齐并附 §11 证据前，不得标 V0.2 PASS。**

---

## 碳核算页 — Resume checklist（暂停 · 当前不接线）

**用户指示（2026-07-26）：不要碳核算，只要智能入库。** 组件可留在未跟踪树中，但勿注册路由/顶栏。

已有未跟踪文件：`CarbonPage.vue` + `components/carbon/{CarbonNav,CarbonOverview,CarbonBoundary,CarbonDetail}.vue`

待做（恢复时再做）：

1. `navItems` 加「碳核算」（允许同步「月报」占位）— **注意与 V0.2「仅三入口」顶栏冲突，恢复前需产品确认**  
2. `router` 注册 `/#/carbon`  
3. 各页 `handleNav*` 互通  
4. 点验三 Tab / `?t=` / 无硬编码 6175  
5. `npm run check` + `build`；交付 `交付_碳核算独立页/`  
6. **不**实现月报页主体（姊妹单）  

月报独立页：尚未开工。

---

## ESG智能助手（2026-07-27 · 已实现 · 问答设计 ACTIVE）

- **问答设计更新（ACTIVE / for review）：** `_handoff/ESG智能助手_问答设计更新_V1.0_20260727.md` — 标准答法、意图全表、样例完整回答、验收要点（**仅助手 Q&A**）
- **姊妹校核：** `_handoff/ESG智能助手_上级环保检查资料包_设计问答与校核报告_20260727.md`
- 设计稿：`_handoff/ESG智能助手_库驱动问答与合规资料包设计_V0.2_20260727.md`（口径：应对上级检查 = 库驱动合规口径 + 同答「下载资料包」）
- API：`POST /api/assistant/ask` · `GET /api/assistant/qa`（`server/assistant_qa.py`）
- 前端：`AssistantPage` 调 `askAssistant`；`packageCard` +「下载资料包」
- 样例包：`public/samples/assistant-compliance-packs/上级检查_{环保|安全|综合}合规资料包_202607(.zip)`（**无 DEMO_ / 演示**；环保包 00–11 可演示校核，内容仍为占位待批复落地）
- **不做：** 全平台能力盘点；碳核算页接线；Formal 打包 API；语音真能力（P3）
- 红线：禁止固定 FAQ 业务数；用户可见文案禁止 DEMO/演示

---

## 红线（仍有效）

不得改坏：工作台首页 GIS/KPI、正式库口径。助手已实现库驱动问答，后续改动勿回退为单模板 mock。V0.2 主路径与碳页恢复勿互相吞并 scope。

**回退（本轮助手+填报）：** `git switch --detach baseline/assistant-smartentry-20260728`  
**回退（首页 GIS/L1L2）：** `git switch --detach baseline/l1-l2-gis-20260726`
