# GIS 关联业务与 E02/S02 指标弹窗跳转协议设计 V1.0

更新时间：2026-07-16  
适用范围：领导层首页真实 GIS、GIS 关联业务侧浮层、E02 未闭环环保问题弹窗、S02 在管较大及以上安全风险点弹窗。

## 1. 设计结论

本阶段不直接写跳转功能代码，先固化跳转协议和边界。

推荐结论：

- GIS 侧只负责“空间定位 + 业务线索查看 + 发起打开请求”；
- DashboardPage 负责打开 E02/S02 KPI 弹窗；
- KpiDetailModal 负责根据传入上下文定位、筛选、高亮对应明细行；
- 领导层仍然只查看，不在 GIS 侧办理、处置或发起督办；
- 首次实施只支持 E02/S02；
- 不使用名称模糊匹配，必须使用稳定 `sourceId` 精确定位；
- 在 KPI 明细数据补齐稳定 ID 前，不应强行做真实跳转。

## 2. 为什么不能现在直接硬跳

当前 GIS 关联业务接口已经返回：

```json
{
  "targetKpiCode": "E02",
  "sourceTable": "environment_problem_item",
  "sourceId": "E02-003"
}
```

但当前 KPI 明细接口存在两个问题：

1. `GET /api/dashboard/kpi/E02` 的 `detailData` 目前没有稳定 `id/sourceId` 字段；
2. `GET /api/dashboard/kpi/S02` 的 `detailData` 也没有稳定 `id/sourceId` 字段。

因此如果前端现在直接跳，只能按 `name/location/status` 模糊匹配，后续真实数据一变就会错选。

正式协议必须先补：

- E02 明细行稳定 ID；
- S02 明细行稳定 ID；
- GIS business-links 的 `sourceId` 与 KPI `detailData[].sourceId` 一致。

## 3. 目标交互

### 3.1 GIS 到 KPI

用户在首页真实 GIS 灰度态：

1. 点击 2 标段；
2. 点击“查看关联业务”；
3. 在侧浮层中看到：
   - 安全风险 `S02-002`；
   - 环保问题 `E02-003`；
4. 点击“查看安全风险来源”；
5. 首页打开 S02 KPI 弹窗；
6. S02 弹窗自动定位并高亮 `S02-002` 对应明细；
7. 弹窗顶部或表格上方显示：
   - 来源：GIS 2标段；
   - 已定位关联事项：S02-002；
8. 用户只能查看，不进入办理。

E02 同理。

### 3.2 KPI 到 GIS（本协议只预留）

KPI 弹窗中可预留“定位到地图”能力，但本阶段不实施。

原因：

- 首页默认仍是 SVG 地图；
- 真实 GIS 是灰度开关；
- 如果默认 SVG 状态下从 KPI 定位 GIS，会产生模式切换与地图加载时机问题。

后续如实施，应另设协议。

## 4. 数据协议

### 4.1 GIS 关联业务项

接口：

```text
GET /api/esg/gis/features/{featureId}/business-links?projectId=LUOYI-ESG
```

业务项结构：

```ts
interface BusinessLinkItem {
  id: string
  type: 'environment_problem' | 'safety_risk' | string
  typeLabel?: string
  code?: string
  title: string
  status?: string
  riskLevel?: number
  summary?: string
  sourceTable?: string
  sourceId?: string
  targetKpiCode?: 'E02' | 'S02' | string
  targetModule?: string
  targetModuleGroup?: string
  actionLabel?: string
  actionEnabled?: boolean
  actionTip?: string
  updatedAt?: string
}
```

跳转需要字段：

| 字段 | 是否必需 | 说明 |
|---|---:|---|
| `targetKpiCode` | 是 | 目前仅支持 `E02`、`S02` |
| `sourceTable` | 是 | 来源业务表 |
| `sourceId` | 是 | 来源业务主键/编码 |
| `code` | 建议 | 展示编码，可与 `sourceId` 一致 |
| `title` | 是 | 展示标题 |
| `featureId` | 是 | GIS 要素 ID，由父级 data 提供 |
| `featureName` | 是 | GIS 要素名称，由父级 data 提供 |

### 4.2 KPI 明细行

E02/S02 KPI 接口需要补齐稳定字段。

#### E02

接口：

```text
GET /api/dashboard/kpi/E02
```

`detailData[]` 建议结构：

```ts
interface E02DetailRow {
  id: string              // 例如 E02-003
  sourceId: string        // 例如 E02-003
  sourceTable: 'env_issue_record' | 'environment_problem_item'
  name: string
  time: string
  level: string
  department: string
  deadline: string
  status: string
  mainStatus: string
  overdue: boolean
  gisFeatureId?: string   // 例如 section-2-1
}
```

#### S02

接口：

```text
GET /api/dashboard/kpi/S02
```

`detailData[]` 建议结构：

```ts
interface S02DetailRow {
  id: string              // 例如 S02-002
  sourceId: string        // 例如 S02-002
  sourceTable: 'safety_risk_point'
  name: string
  level: string
  location: string
  type: string
  time: string
  status: string
  gisFeatureId?: string   // 例如 section-2-1 或 slope-2-1
}
```

### 4.3 映射要求

| GIS relation type | targetKpiCode | KPI sourceTable | KPI sourceId 示例 |
|---|---|---|---|
| `environment_problem` | `E02` | `env_issue_record` 或 `environment_problem_item` | `E02-003` |
| `safety_risk` | `S02` | `safety_risk_point` | `S02-002` |

强制要求：

- `business-links.items[].sourceId` 必须能在目标 KPI `detailData[].sourceId` 中找到；
- 如果找不到，不得误选第一行；
- 如果找不到，只打开目标 KPI 弹窗，并提示“未定位到对应明细”。

## 5. 前端事件协议

### 5.1 GIS 模块向 DashboardPage 发出的事件

建议事件名：

```ts
openKpiLink
```

事件结构：

```ts
interface GisKpiLinkRequest {
  source: 'GIS_BUSINESS_LINK'
  projectId: string
  featureId: string
  featureName: string
  targetKpiCode: 'E02' | 'S02'
  sourceTable: string
  sourceId: string
  relationType: string
  relationCode?: string
  relationTitle: string
  relationStatus?: string
  readonly: true
  openMode: 'modal'
  focusMode: 'highlight-row'
}
```

示例：

```json
{
  "source": "GIS_BUSINESS_LINK",
  "projectId": "LUOYI-ESG",
  "featureId": "section-2-1",
  "featureName": "2标段",
  "targetKpiCode": "S02",
  "sourceTable": "safety_risk_point",
  "sourceId": "S02-002",
  "relationType": "safety_risk",
  "relationCode": "S02-002",
  "relationTitle": "高边坡施工较大风险点",
  "relationStatus": "持续管控",
  "readonly": true,
  "openMode": "modal",
  "focusMode": "highlight-row"
}
```

### 5.2 组件传递链路

推荐链路：

```text
BusinessLinksPanel
  emit openKpiLink(request)
TrafficGisOverview
  emit openKpiLink(request)
GisOverviewCesiumPanel
  emit openKpiLink(request)
DashboardPage
  handleGisKpiLink(request)
  -> load target KPI detail
  -> open KpiDetailModal
  -> pass focusContext
KpiDetailModal
  -> locate row by sourceId
  -> apply filter if needed
  -> highlight row
```

## 6. KPI 弹窗上下文协议

DashboardPage 打开 KpiDetailModal 时传：

```ts
interface KpiModalFocusContext {
  source: 'GIS_BUSINESS_LINK'
  sourceId: string
  sourceTable: string
  gisFeatureId: string
  gisFeatureName: string
  relationTitle: string
  relationStatus?: string
  readonly: boolean
}
```

KpiDetailModal 接收：

```ts
defineProps<{
  detail: KpiDetailConfig
  focusContext?: KpiModalFocusContext
}>()
```

弹窗行为：

1. 根据 `focusContext.sourceId` 查找 `detail.detailData`；
2. 找到后高亮行；
3. 如当前有筛选条件导致目标行不可见，应自动清空筛选或切换到包含目标行的筛选；
4. 表格滚动到目标行；
5. 显示来源提示条；
6. 不自动点击“发起督办”；
7. 不进入办理态。

来源提示条建议文案：

```text
来自 GIS：2标段｜已定位关联事项 S02-002 高边坡施工较大风险点
```

未定位到明细：

```text
来自 GIS：2标段｜未在当前指标明细中定位到 S02-002，请检查数据同步状态。
```

## 7. 权限边界

### 7.1 允许

允许：

- 打开 E02/S02 弹窗；
- 定位并高亮明细行；
- 展示 GIS 来源提示；
- 查看业务来源；
- 保留“查看详情（预留）”；
- 保留只读说明。

### 7.2 不允许

不允许：

- GIS 侧办理事项；
- GIS 侧处置事项；
- GIS 侧发起督办；
- 跳转到工作台办理页面；
- 修改 E02/S02 业务状态；
- 关闭或改写首页 KPI 值；
- 根据名称模糊匹配并自动选中；
- 找不到明细时误选第一行。

### 7.3 按钮策略

如果 E02/S02 弹窗中已有“发起督办”按钮：

- 从 GIS 来源打开时，不应自动触发；
- 如按钮保留，应继续使用原型预留提示；
- 不应显示为“可办理”或“可处置”。

建议从 GIS 来源打开时显示：

```text
领导层仅查看关联业务线索，不在地图侧办理事项。
```

## 8. 异常与降级策略

| 场景 | 处理 |
|---|---|
| `targetKpiCode` 为空 | 不打开弹窗，toast：该关联业务暂未配置指标入口 |
| `targetKpiCode` 非 E02/S02 | 不打开弹窗，toast：该指标入口暂未接入 |
| `sourceId` 为空 | 不打开弹窗，toast：缺少业务来源编码，无法定位 |
| KPI 接口请求失败 | toast：指标数据加载失败，请稍后重试 |
| KPI 明细未找到 `sourceId` | 打开弹窗但不选中行，显示未定位提示 |
| 首页当前为 SVG 地图 | 不影响；该联动只从真实 GIS 灰度态触发 |
| 用户关闭 KPI 弹窗 | 返回首页，GIS 侧状态不变 |

## 9. 第一阶段实施范围建议

第一阶段只做：

1. 后端补 E02/S02 `detailData[].id/sourceId/sourceTable/gisFeatureId`；
2. 前端定义 `GisKpiLinkRequest` 和 `KpiModalFocusContext` 类型；
3. BusinessLinksPanel 中将“查看来源”从 toast 改为 emit 请求；
4. DashboardPage 接收请求并打开目标 KPI；
5. KpiDetailModal 根据 `sourceId` 高亮行；
6. 找不到行时显示未定位提示。

不做：

- KPI 到 GIS 反向定位；
- 自动切换 `useRealGisOnDashboard`；
- 办理/督办；
- 工作台跳转；
- 路由参数化；
- URL 深链。

## 10. 第二阶段预留

后续可扩展：

- KPI 弹窗中点击“定位到地图”；
- E02/S02 弹窗行和 GIS 要素双向联动；
- URL 深链，如 `/#/?kpi=S02&sourceId=S02-002`；
- 真实业务系统详情页；
- 按权限控制是否允许督办。

## 11. 实施前检查清单

实施前必须确认：

- [ ] `GET /api/dashboard/kpi/E02` detailData 已有 `sourceId`；
- [ ] `GET /api/dashboard/kpi/S02` detailData 已有 `sourceId`；
- [ ] GIS `business-links.items[].sourceId` 与 KPI `detailData[].sourceId` 一致；
- [ ] `targetKpiCode` 仅允许 `E02/S02`；
- [ ] 首页默认 `useRealGisOnDashboard: false`；
- [ ] 灰度验收时再临时开启真实 GIS；
- [ ] 找不到明细时不会误选；
- [ ] 从 GIS 打开的 KPI 弹窗不提供办理入口。

## 12. 推荐给 Trae 的实施顺序

不要一次性做完全部交互。建议分两步：

### Trae 任务 A：数据 ID 与弹窗高亮基础能力

- 后端/接口已补 ID 后；
- KpiDetailModal 支持 `focusContext`；
- E02/S02 表格支持按 `sourceId` 高亮；
- DashboardPage 支持打开 KPI 并传入 `focusContext`；
- 暂不改 BusinessLinksPanel 按钮。

### Trae 任务 B：GIS 侧按钮接入真实打开

- BusinessLinksPanel 点击“查看来源”；
- 生成 `GisKpiLinkRequest`；
- 逐级 emit 到 DashboardPage；
- 打开 E02/S02；
- 验证高亮行。

这样拆分能避免“按钮已跳转但弹窗定位不准”的尴尬。

