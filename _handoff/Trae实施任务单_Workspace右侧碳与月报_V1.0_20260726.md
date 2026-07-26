# Trae 实施任务单 · Workspace 右侧碳与月报 V1.0

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-26 |
| **版本** | V1.0 · **开工令** |
| **状态** | **READY_for_trae** |
| **实施方** | Trae |
| **本单性质** | 仅 Workspace「填报概览」右侧栏：碳摘要 + 月报摘要 |
| **设计依据** | `_handoff/Workspace右侧_碳与月报模块设计_V0.1_20260726.md` |
| **开工基线 Tag** | **`baseline/workspace-ui-20260726`**（Workspace UI 打磨快照） |
| **首页保护 Tag** | `baseline/l1-l2-gis-20260726`（**勿改首页**；两 tag 共存） |
| **基线说明** | `_handoff/BASELINE_Workspace_UI_20260726.md` |

> **重要：** 本文件是本 sprint **唯一实现依据**。口径或布局变更 → **停工 → 改设计**，不得自行扩 scope。

---

## 0. 背景

1. 用户要求在 **数据填报（Workspace）右侧**增加与首页同源的**碳相关模块**与**月报模块**，服务填报场景一眼看碳 / 月报进度。
2. 上一 sprint「数据填报页续作」可能并行收尾；**本单为当前主任务**。若续作未合入，实施时**勿回退**已落地的五 Tab / 真解析能力。
3. 设计结论：**仅填报概览**右栏；保留紧凑助手；碳 + 月报各一张 `.ws-panel`；今日重点降级 ≤2 条；点击由 `WorkspacePage` 宿主挂载既有 E04 / 月报模态。

---

## 0.1 基线与回退（MUST）

| 动作 | 命令 / 要求 |
|------|-------------|
| 开工前对齐 | 从含 tag `baseline/workspace-ui-20260726` 的分支创建实施分支（或 `git switch --detach` 检视后切回分支开工） |
| 破损回退 | `git switch --detach baseline/workspace-ui-20260726`（详见 `_handoff/BASELINE_Workspace_UI_20260726.md`） |
| 首页回退 | 仍用 `baseline/l1-l2-gis-20260726`；**禁止删除或覆盖该 tag** |
| 格式 | 必须与当前 Workspace UI 统一（`.ws-panel` / `.ws-btn-*` / `--ws-*`）；**禁止新视觉语言** |

---

## 1. 硬禁令（红线 · MUST）

### 1.1 FORBIDDEN — 首页 / GIS / L1–L2 / 其它模块

| # | 禁止 |
|---|------|
| R1 | **禁止改动** `src/views/DashboardPage.vue` |
| R2 | **禁止改动** GIS / `src/modules/traffic-gis-overview/**` |
| R3 | **禁止改动** e01 / e02 / e03 / s02 业务与文案（及对应 L1/L2 工作台核心） |
| R4 | **禁止改动** `HeaderNav.vue` 结构与样式；勿改 `navItems`「统一视觉」 |
| R5 | **禁止改动** 首页右栏面板**源码重写**：`CarbonBenefitPanel.vue`、`MonthlyReportPanel.vue`、Master 碳/月报组件（可 **read/reuse API** 与只读 import 模态，不得改面板内部） |
| R6 | **禁止改动** S01–G04 等 KPI 模态内部业务（含 S01–S04、G01–G04）；本单仅允许 Workspace 宿主 **open/close** 既有 E04 / Monthly 模态 |
| R7 | **禁止回归破坏** `baseline/l1-l2-gis-20260726` 保护的首页完整度 |

### 1.2 FORBIDDEN — ESG 智能助手

| # | 禁止 |
|---|------|
| R8 | **禁止改动** `src/views/AssistantPage.vue`、`src/components/assistant/**` |
| R9 | **禁止**推进助手 DB 驱动问答 |

### 1.3 FORBIDDEN — 全局样式 / 新视觉 / 种子

| # | 禁止 |
|---|------|
| R10 | **禁止改动** `layout.scss`、`tokens.scss` 全局壳层 / 全局 tokens |
| R11 | **禁止**新视觉语言（新色板、新卡片体系、非 Workspace token 的 glow/紫系皮肤等） |
| R12 | UI **禁止**「演示 / 测试 / 未确认」chrome |
| R13 | **不要**改五 Tab 结构或把五项挂进平台顶栏 |
| R14 | **不要**在 tasks / smart-upload / review / documents 挂本右轨 |
| R15 | **不要**为对齐 Workspace 去改 `dashboard.mock.ts` / KPI SQL / E04 seed 主值 |
| R16 | 不向 `main` 直推；分支遵循 `AGENTS.md` |
| R17 | **禁止**改其它非 Workspace 模块「顺手打磨」 |

### 1.4 ALLOWED — 白名单（仅这些）

| 路径 | 允许动作 |
|------|----------|
| `src/views/WorkspacePage.vue` | 宿主挂载 E04 / Monthly 模态；接收 emit |
| `src/components/workspace/**` | Home 右栏编排；新建 `WorkspaceCarbonSummary.vue` / `WorkspaceMonthlySummary.vue` 等 |
| `src/styles/workspace.scss` | **仅**右栏摘要卡局部样式；复用 `.ws-panel` / `.ws-btn-*` / `--ws-*` |
| `src/services/api.ts` | **薄**客户端：复用/微调已有 `getDashboardPanels`、`getMonthlyReportReadiness`、topic、E04 client；**禁止新 schema**；禁止顺手改 GIS/E01–E03 API |
| `src/types/workspace.ts` | 仅 emit/props 类型需要时 |
| `src/data/workspace.mock.ts` | 仅今日重点条数/文案降级需要时 |

**只读复用（可 import，不改文件）：**  
`E04CarbonEmissionModal`、`MonthlyReportModal`、dashboard/monthly mock（仅回落）、`monthly-readiness` 校验工具。

**后端：** 本单默认不改 `server/**`。确需修补须先停工确认；**禁止新 schema / 碳主值迁移**。

---

## 2. 与旧单关系

| 文档 | 本 sprint |
|------|-----------|
| `_handoff/Trae实施任务单_数据填报页续作_仅Workspace_V1.0_20260726.md` | 并行收尾可继续，但 **NEXT 指针指向本单**；冲突以本单红线为准 |
| `_handoff/Trae实施任务单_Workspace入口与S02S03小改_V1.0_20260726.md` | SUPERSEDED |
| Header 视觉统一 / 助手 DB 问答 | HOLD / OUT |

---

## 3. 范围内实施项（In Scope）

### 3.1 Module A · 碳摘要（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| C-1 | 紧凑 `.ws-panel` 碳卡；展示 panels.`carbon.metrics` 中与 `CarbonBenefitPanel` 相同的最多 3 项（滤「较基准下降」） | 有值且非硬编码常量 |
| C-2 | 来源 Top3（name + %）来自 `carbon.sources` | 与 panels 同源 |
| C-3 | 可选一行无数值边界提示（油+电+材料；运输暂不纳入） | 无演示角标 |
| C-4 | 「查看核算」→ WorkspacePage 打开既有 E04 模态 | 不改 DashboardPage / 不改面板源码 |

### 3.2 Module B · 月报摘要（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| M-1 | 紧凑 `.ws-panel`：期次、归集率%、已归集 n/m、三态计数、截止区间 | 同源 readiness（默认期次与 store 一致） |
| M-2 | 待处理最多 3 条：`taskName` + `monthlyStatus` | 来自 `exceptionTasks` |
| M-3 | 「查看月报准备」→ 既有 `MonthlyReportModal` + topic API | 不改首页面板 |

### 3.3 右栏编排（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| L-1 | 栈序：助手（紧凑）→ 碳 → 月报 → 今日重点（≤2） | 符合设计 |
| L-2 | **仅** Home / `activeNav===workspace` 显示 | 五 Tab 未破 |
| L-3 | 右栏可纵向滚动，不撑破左表 | 1366 / 1920 可扫一眼 |

### 3.4 Out of Scope

- 复刻首页 RingChart / 减排措施整板 / 月报双栏大表  
- 全 Tab 右轨、第六 Tab、Header 入口  
- 助手 DB 问答、Dashboard/GIS、碳主值迁移  
- 续作单中的审核文档 6 列卡等（非本单阻塞）

---

## 4. 验收清单

### 4.1 红线抽检

| # | 查 | 期望 |
|---|-----|------|
| H1 | `git diff` | **无** DashboardPage / GIS / assistant / HeaderNav / CarbonBenefitPanel·MonthlyReportPanel 源码改写 / layout&tokens 全局 / S01–G04 模态业务 |
| H2 | 样式 | 仅 `workspace.scss` + 现有 ws 组件类；无新视觉语言 |
| H3 | 基线 | 从 `baseline/workspace-ui-20260726` 开工；未破坏 `baseline/l1-l2-gis-20260726` |

### 4.2 功能

| # | 查 | 期望 |
|---|-----|------|
| W1 | `/#/workspace` 右栏 | 助手 + 碳 + 月报 + 今日重点(≤2) |
| W2 | 碳数据 | 与 `GET /api/dashboard/panels` carbon 一致；无手工 6175 |
| W3 | 月报数据 | 与 readiness 接口一致 |
| W4 | 下钻 | 两按钮打开既有模态并可关闭 |
| W5 | 其它 Tab | 无本右轨；五 Tab 仍在 |
| W6 | 文案 | 无演示/测试/未确认 chrome |

### 4.3 编译

见 §5。

---

## 5. 验证命令

```bash
npm ci
npm run check
npm run build
```

若例外改动了任何 Python（默认不应）：

```bash
python -m compileall -q server
```

**点击验收（最低）：**

1. `/#/workspace`：右栏四段栈序正确；碳/月报有数  
2. 「查看核算」→ E04 类模态；关闭后回填报概览  
3. 「查看月报准备」→ 月报模态  
4. 其它 Tab：**无**碳/月报右轨  
5. 大屏首页碳/月报面板：本分支**未改坏**（对照 `baseline/l1-l2-gis-20260726`）

---

## 6. 交付包约定

建议目录：`交付_Workspace右侧碳与月报/`

1. 变更文件列表（对照白名单）  
2. 交付说明：完成项；panels/readiness mock vs API；验证结果；声明未改 Dashboard/GIS/Assistant/HeaderNav/首页右栏源码  
3. 可选截图  
4. 已知未做项  

**分支建议：** `trae/<issue>-workspace-right-carbon-monthly`  
**PR：** 引用 Issue；按 `AGENTS.md`；不向 `main` 直推。

---

## 7. 完成定义（DoD）

- [ ] §1 红线未破；格式统一 Workspace  
- [ ] §3 全部完成  
- [ ] §4 验收通过；§5 命令通过（或例外已记录）  
- [ ] 交付包完整  
- [ ] 无产品代码外 scope 蔓延  

---

## 8. 给 Trae 的一句话

> **从 `baseline/workspace-ui-20260726` 开工**：只在 Workspace 填报概览右栏加碳/月报两张紧凑 `.ws-panel`（panels + readiness，宿主挂既有模态）；**Dashboard / GIS / e01–e03/s02 / HeaderNav / Assistant / layout·tokens / 首页 CarbonBenefitPanel 源码 / S01–G04 模态一律不许碰**；破损回退该 tag。
