# E02/S02 弹窗与 GIS 关联业务真实跳转协议实施任务书_A

## 一、背景

当前 GIS 扩展功能先暂停，不继续增加地图能力。本阶段只做“地图关联业务线索 → 首页 KPI 弹窗”的真实跳转协议落地。

后端已完成前置数据锚点：

- `GET /api/dashboard/kpi/E02` 的 `detailData` 已补充 `id/sourceId/sourceTable/rawId/gisFeatureId`
- `GET /api/dashboard/kpi/S02` 的 `detailData` 已补充 `id/sourceId/sourceTable/rawId/gisFeatureId`
- GIS `business-links` 返回的 `sourceId` 可与 E02/S02 弹窗明细行精确匹配
- 后端验收脚本已通过：
  - `server/environment_safety_kpi_mysql_test.py`
  - `server/gis_business_summary_test.py`

示例映射：

| 来源 | sourceId | sourceTable | gisFeatureId | 说明 |
|---|---:|---|---|---|
| E02 | E02-003 | env_issue_record | section-2-1 | 弃渣场扬尘控制不到位 |
| E02 | E02-005 | env_issue_record | eco-1-1 | 生态敏感区施工管控 |
| S02 | S02-002 | safety_risk_point | section-2-1 | 高边坡坍塌风险 |
| S02 | S02-006 | safety_risk_point | slope-2-1 | 弃渣场边坡位移监测 |

## 二、本阶段目标

完成前端第一阶段：让 E02/S02 弹窗支持外部传入定位上下文，并能自动定位、高亮对应明细行。

本阶段不要求真正从 GIS 侧按钮触发跳转；先把 KPI 弹窗侧的“接收协议”做好。

完成后，后续 B 阶段再把 GIS `BusinessLinksPanel` 的“查看来源/查看业务”按钮接到这个协议。

## 三、允许修改文件

优先修改：

- `src/components/KpiDetailModal.vue`
- `src/views/DashboardPage.vue`
- `src/types/dashboard.ts`

如项目实际文件路径不同，以当前项目为准。

## 四、禁止修改

- `server/`
- `src/modules/traffic-gis-overview/`
- `src/components/gis/GisOverviewPanel.vue`
- `src/components/gis/RouteMapSvg.vue`
- 不要修改 GIS 后端接口
- 不要新增路由
- 不要改其他 E/G/S 指标的数据口径
- 不要修改 `useRealGisOnDashboard` 默认值

## 五、协议类型建议

在 `src/types/dashboard.ts` 增加：

```ts
export interface KpiModalFocusContext {
  sourceTable?: string
  sourceId?: string
  gisFeatureId?: string
  from?: 'gis' | 'dashboard' | 'workspace'
  title?: string
}
```

`sourceId` 是主匹配字段。

匹配优先级：

1. `row.sourceId === focusContext.sourceId`
2. `row.id === focusContext.sourceId`
3. 如确实没有 sourceId，可兜底使用 `row.gisFeatureId === focusContext.gisFeatureId`

## 六、KpiDetailModal 修改要求

### 1. 新增 prop

给 `KpiDetailModal.vue` 增加可选 prop：

```ts
focusContext?: KpiModalFocusContext | null
```

要求：

- 无 `focusContext` 时，所有弹窗保持当前行为；
- 有 `focusContext` 且当前 KPI 是 E02/S02 时，自动定位明细行；
- 如果当前 KPI 不是 E02/S02，暂不处理，不报错。

### 2. E02 定位与高亮

当 `detail.key === 'E02'` 且 `focusContext.sourceId` 存在：

- 在 `detail.detailData` 中查找匹配行；
- 如当前筛选条件导致目标行不可见，应自动清除或调整 E02 表格筛选，确保目标行显示；
- 目标行增加高亮样式，例如：
  - 左侧蓝色竖线；
  - 行背景轻微蓝色发光；
  - 2 秒以内淡入即可，不要强烈闪烁；
- 弹窗顶部或明细区上方显示轻量来源提示：

文案建议：

> 已从 GIS 地图定位到关联环保问题：E02-003

如果 `focusContext.title` 有值，可显示：

> 已从 GIS 地图定位到：弃渣场扬尘控制不到位

### 3. S02 定位与高亮

当 `detail.key === 'S02'` 且 `focusContext.sourceId` 存在：

- 同样按 `sourceId/id/gisFeatureId` 匹配；
- 确保目标风险点行可见；
- 高亮该风险点明细行；
- 显示轻量来源提示：

> 已从 GIS 地图定位到关联安全风险点：S02-002

### 4. 滚动处理

如明细表区域当前有内部滚动：

- 可以调用 `scrollIntoView({ block: 'center' })`；
- 但不得新增页面级滚动条；
- 不得导致弹窗整体布局抖动。

如果当前弹窗无滚动或目标行已经可见，仅高亮即可。

### 5. 找不到匹配行时

不得空白、不得报错。

显示轻量提示：

> 已打开对应指标弹窗，但未在当前明细中找到该 GIS 关联记录。

同时保持弹窗正常展示全部明细。

## 七、DashboardPage 修改要求

### 1. 增加状态

建议增加：

```ts
const kpiFocusContext = ref<KpiModalFocusContext | null>(null)
```

打开普通 KPI 弹窗时：

```ts
kpiFocusContext.value = null
```

### 2. 预留统一入口函数

增加函数：

```ts
function openKpiFromBusinessLink(payload: {
  targetType: 'E02' | 'S02'
  sourceId: string
  sourceTable?: string
  gisFeatureId?: string
  title?: string
}) {
  kpiFocusContext.value = {
    sourceId: payload.sourceId,
    sourceTable: payload.sourceTable,
    gisFeatureId: payload.gisFeatureId,
    from: 'gis',
    title: payload.title
  }
  openKpiDetail(payload.targetType)
}
```

本阶段可以先不被 GIS 组件调用，但函数和传参链路要完整。

### 3. 传给弹窗

`KpiDetailModal` 增加：

```vue
:focus-context="kpiFocusContext"
```

关闭弹窗时建议清空：

```ts
kpiFocusContext.value = null
```

## 八、权限边界

领导层从 GIS 跳到 E02/S02 弹窗后：

- 只能查看；
- 可以看到定位来源；
- 不提供办理、整改、处置；
- 不新增“发起督办”；
- 不改变现有“查看详情（预留）”策略。

如已有按钮保持禁用/预留提示即可。

## 九、验收步骤

### 1. 普通 KPI 打开回归

访问：

`http://localhost:5174/#/`

检查：

- 普通点击 E02 正常打开；
- 普通点击 S02 正常打开；
- 无高亮来源提示；
- 其他 KPI 弹窗不受影响。

### 2. 临时开发触发验证

可临时在 `DashboardPage.vue` 中加一个仅开发环境使用的触发按钮或控制台入口，测试后保留为注释或移除。

测试 payload：

```ts
openKpiFromBusinessLink({
  targetType: 'E02',
  sourceId: 'E02-003',
  sourceTable: 'env_issue_record',
  gisFeatureId: 'section-2-1',
  title: '弃渣场扬尘控制不到位'
})
```

预期：

- 打开 E02 弹窗；
- 明细中 `E02-003` 行高亮；
- 显示来源提示。

再测试：

```ts
openKpiFromBusinessLink({
  targetType: 'S02',
  sourceId: 'S02-002',
  sourceTable: 'safety_risk_point',
  gisFeatureId: 'section-2-1',
  title: '高边坡坍塌风险'
})
```

预期：

- 打开 S02 弹窗；
- 明细中 `S02-002` 行高亮；
- 显示来源提示。

### 3. 找不到记录测试

测试：

```ts
openKpiFromBusinessLink({
  targetType: 'E02',
  sourceId: 'E02-NOT-FOUND'
})
```

预期：

- E02 弹窗正常打开；
- 不报错；
- 显示“未在当前明细中找到”提示。

## 十、完成后执行

```bash
npm.cmd run check
npm.cmd run build
```

## 十一、完成后回报

请回报：

1. 修改文件清单；
2. 是否新增 `KpiModalFocusContext`；
3. E02 是否可按 `sourceId` 定位并高亮；
4. S02 是否可按 `sourceId` 定位并高亮；
5. 普通 KPI 打开是否不受影响；
6. 找不到记录时是否有轻量提示；
7. 是否未修改 GIS 模块和后端；
8. `npm.cmd run check` 结果；
9. `npm.cmd run build` 结果。
