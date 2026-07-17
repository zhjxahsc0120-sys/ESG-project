# GIS 关联业务跳转 E02/S02 弹窗实施任务书_B

## 一、背景

A 阶段已完成 KPI 弹窗接收协议：

- `DashboardPage.vue` 已新增 `openKpiFromBusinessLink`
- `KpiDetailModal.vue` 已支持 `focusContext`
- E02/S02 可按 `sourceId → id → gisFeatureId` 定位并高亮明细行

后端和数据库锚点已完成：

- GIS `business-links.items[].sourceId` 可匹配 E02/S02 `detailData[].sourceId`
- E02 关联业务 `sourceTable` 已统一为 `env_issue_record`
- S02 关联业务 `sourceTable` 为 `safety_risk_point`

本阶段目标是打通“GIS 关联业务侧浮层 → E02/S02 KPI 弹窗”的真实查看跳转。

## 二、本阶段目标

在首页真实 GIS 灰度态中：

1. 点击 GIS 要素；
2. 点击“查看关联业务”；
3. 在侧浮层中点击“查看环保问题来源”或“查看安全风险来源”；
4. 自动打开 E02 或 S02 弹窗；
5. 自动定位并高亮对应明细行。

注意：本阶段仍然只是“查看来源”，不是办理、不是督办、不是处置。

## 三、允许修改文件

优先修改：

- `src/modules/traffic-gis-overview/components/BusinessLinksPanel.vue`
- `src/modules/traffic-gis-overview/components/TrafficGisOverview.vue`
- `src/components/gis/GisOverviewCesiumPanel.vue`
- `src/views/DashboardPage.vue`
- `src/modules/traffic-gis-overview/types/index.ts`

如确实需要，可轻微修改：

- `src/types/dashboard.ts`

## 四、禁止修改

- `server/`
- `src/components/gis/GisOverviewPanel.vue`
- `src/components/gis/RouteMapSvg.vue`
- 不新增路由
- 不修改 KPI 数据口径
- 不修改 E02/S02 弹窗结构
- 不默认开启 `useRealGisOnDashboard`
- 不引入复杂全局状态库

## 五、协议设计

### 1. BusinessLinkItem 使用字段

从 `BusinessLinkItem` 读取：

```ts
{
  targetKpiCode?: string // E02 / S02
  sourceId?: string      // E02-003 / S02-002
  sourceTable?: string   // env_issue_record / safety_risk_point
  title?: string
  code?: string
}
```

### 2. 可跳转条件

允许真实跳转的条件：

```ts
item.targetKpiCode === 'E02' || item.targetKpiCode === 'S02'
```

并且：

```ts
!!item.sourceId
```

权限口径：

- 如果 `permissions.canView === false`，不允许跳转，只显示提示；
- 如果 `permissions.canView === true`，允许查看来源；
- 不要用 `actionEnabled` 判断本次查看跳转。

说明：

`actionEnabled` 在第八阶段用于“预留按钮”状态，不能等同于领导层查看权限。本阶段真实查看跳转以 `permissions.canView` 和 `targetKpiCode/sourceId` 为准。

### 3. 事件载荷建议

新增事件类型：

```ts
export interface GisBusinessLinkOpenPayload {
  targetType: 'E02' | 'S02'
  sourceId: string
  sourceTable?: string
  gisFeatureId?: string
  title?: string
}
```

如果不想新增公共类型，也可在组件内定义同结构类型。

## 六、组件事件链

事件从内向外传递：

```text
BusinessLinksPanel
  emit('open-kpi-source', payload)
    ↓
TrafficGisOverview
  emit('openKpiSource', payload)
    ↓
GisOverviewCesiumPanel
  emit('openKpiSource', payload)
    ↓
DashboardPage
  openKpiFromBusinessLink(payload)
    ↓
KpiDetailModal focusContext 定位高亮
```

## 七、具体修改要求

### 1. BusinessLinksPanel.vue

当前点击按钮只是显示：

> 关联业务跳转为原型预留，尚未接入页面联动。

本阶段改为：

- 如果该 item 可跳转 E02/S02 且 `canView=true`：
  - emit `open-kpi-source`
  - 不再显示“尚未接入”的预留提示
- 如果不可跳转：
  - 保持轻量提示

建议函数：

```ts
function canOpenKpiSource(item: BusinessLinkItem) {
  return permissions.value?.canView !== false
    && (item.targetKpiCode === 'E02' || item.targetKpiCode === 'S02')
    && !!item.sourceId
}

function handleOpenSource(item: BusinessLinkItem) {
  if (!canOpenKpiSource(item)) {
    showPlaceholderTip(item)
    return
  }

  emit('open-kpi-source', {
    targetType: item.targetKpiCode,
    sourceId: item.sourceId,
    sourceTable: item.sourceTable,
    title: item.title || item.code,
  })
}
```

按钮文案：

- E02：`查看环保问题来源`
- S02：`查看安全风险来源`
- 不要再显示“（预留）”

不可跳转或非 E02/S02 项仍可显示：

- `查看来源（预留）`

### 2. TrafficGisOverview.vue

新增 emit：

```ts
openKpiSource: [payload: GisBusinessLinkOpenPayload]
```

接收 `BusinessLinksPanel` 事件后向外透传：

```vue
<BusinessLinksPanel
  ...
  @open-kpi-source="$emit('openKpiSource', $event)"
/>
```

如果需要补 `gisFeatureId`：

```ts
{
  ...payload,
  gisFeatureId: selected.value?.id
}
```

建议补上 `gisFeatureId`，便于兜底定位。

### 3. GisOverviewCesiumPanel.vue

新增 emit 并向外透传：

```ts
const emit = defineEmits<{
  openKpiSource: [payload: GisBusinessLinkOpenPayload]
}>()
```

模板：

```vue
<TrafficGisOverview
  ...
  @open-kpi-source="emit('openKpiSource', $event)"
/>
```

注意 Vue 事件命名：

- 子组件 emit 可用 `openKpiSource`
- 模板监听建议用 `@open-kpi-source`

### 4. DashboardPage.vue

首页真实 GIS 组件增加监听：

```vue
<GisOverviewCesiumPanel
  v-if="gisConfig.useRealGisOnDashboard"
  @open-kpi-source="openKpiFromBusinessLink"
/>
```

`openKpiFromBusinessLink` 已存在，尽量复用，不要另写一套。

## 八、交互边界

### 1. 侧浮层关闭

点击来源后打开 KPI 弹窗时，可以不强制关闭 GIS 侧浮层，因为 KPI 弹窗 Teleport 到 body 并压暗背景。

但推荐：

- 打开 KPI 弹窗后，GIS 内部侧浮层可以保持当前状态；
- 用户关闭 KPI 弹窗后首页仍正常。

不要为了关闭侧浮层引入全局状态。

### 2. 只查看，不办理

跳转后的 E02/S02 弹窗：

- 不新增办理按钮；
- 不新增督办按钮；
- 不新增处置按钮；
- 不改变现有领导层权限口径。

### 3. `/gis-preview`

`/gis-preview` 没有 DashboardPage 接收方。

处理方式：

- 可以在 `GisPreviewPage.vue` 中监听 `open-kpi-source` 并显示轻量提示：

> 预览页已触发 KPI 来源定位：E02-003。请在领导首页灰度态验证弹窗联动。

- 或者不监听，但控制台不得报错。

## 九、验收步骤

### 1. 后端接口确认

访问：

`http://127.0.0.1:8765/api/esg/gis/features/section-2-1/business-links?projectId=LUOYI-ESG`

确认：

- `S02-002 targetKpiCode=S02 sourceId=S02-002`
- `E02-003 targetKpiCode=E02 sourceId=E02-003`
- E02 的 `sourceTable=env_issue_record`
- S02 的 `sourceTable=safety_risk_point`

### 2. 首页真实 GIS 灰度态

临时设置：

```ts
useRealGisOnDashboard: true
```

访问：

`http://localhost:5174/#/`

操作：

1. 点击 2 标段；
2. 点击“查看关联业务”；
3. 点击“查看环保问题来源”。

预期：

- 打开 E02 弹窗；
- 明细行 `E02-003` 高亮；
- 出现来源提示：`已从 GIS 地图定位到：弃渣场截排水整改` 或同义文案；
- 不出现办理/督办/处置动作。

再操作：

1. 重新点击 2 标段；
2. 点击“查看关联业务”；
3. 点击“查看安全风险来源”。

预期：

- 打开 S02 弹窗；
- 明细行 `S02-002` 高亮；
- 出现来源提示；
- 不出现办理/督办/处置动作。

### 3. SVG 回退

恢复：

```ts
useRealGisOnDashboard: false
```

检查：

- 首页恢复原 SVG 地图；
- KPI、专题、时间轴不受影响。

### 4. `/gis-preview`

访问：

`http://localhost:5174/#/gis-preview`

检查：

- 页面不报错；
- 如增加了提示，可正常提示；
- 配置后台仍可打开。

## 十、完成后执行

```bash
npm.cmd run check
npm.cmd run build
```

## 十一、完成后回报

请回报：

1. 修改文件清单；
2. `BusinessLinksPanel` 是否已 emit KPI 来源定位事件；
3. `TrafficGisOverview` 是否已向外透传；
4. `GisOverviewCesiumPanel` 是否已向 DashboardPage 透传；
5. 点击环保问题是否能打开 E02 并高亮 `E02-003`；
6. 点击安全风险是否能打开 S02 并高亮 `S02-002`；
7. 是否没有新增办理/督办/处置；
8. `/gis-preview` 是否正常；
9. SVG 回退是否正常；
10. `npm.cmd run check` 结果；
11. `npm.cmd run build` 结果。

