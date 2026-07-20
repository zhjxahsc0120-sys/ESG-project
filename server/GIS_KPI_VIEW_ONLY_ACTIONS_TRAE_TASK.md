# GIS 来源打开 E02/S02 弹窗查看权限收口任务书

## 一、背景

当前链路已打通：

- 首页真实 GIS 点击 2 标段能打开 FeatureCard；
- 点击“查看关联业务”能打开 BusinessLinksPanel；
- 点击“查看环保问题来源”能打开 E02 弹窗并定位记录；
- 点击“查看安全风险来源”能打开 S02 弹窗并定位记录。

浏览器复验发现：

- 从 GIS 来源打开 E02/S02 弹窗时，弹窗底部仍显示“发起督办”按钮；
- 该按钮是原 KPI 弹窗既有能力，不是本轮 GIS 跳转新增；
- 但从 GIS 关联业务进入时，前面已明确权限口径为“领导层仅查看关联业务线索，不在地图侧办理事项”，因此建议做小范围收口。

## 二、本阶段目标

当 `focusContext.from === 'gis'` 且当前弹窗为 E02 或 S02 时：

- 不显示“发起督办”按钮；
- 不显示任何办理、处置、督办类操作；
- 保留“关闭”；
- 可保留“查看事项详情 / 查看风险点详情”类查看按钮，但如未接业务页，继续保持预留或禁用；
- 普通从首页 KPI 卡片点击打开 E02/S02 时，原有按钮策略不变。

## 三、允许修改文件

优先修改：

- `src/components/modal/KpiDetailModal.vue`

如需要，可轻微修改：

- `src/types/dashboard.ts`

## 四、禁止修改

- 不修改 `server/`
- 不修改 GIS 模块
- 不修改 `DashboardPage.vue` 的事件链路
- 不修改 E02/S02 数据口径
- 不默认开启 `useRealGisOnDashboard`

## 五、实现建议

在 `KpiDetailModal.vue` 中增加计算属性：

```ts
const isFromGis = computed(() => props.focusContext?.from === 'gis')
const isGisViewOnlyKpi = computed(() =>
  isFromGis.value && (props.detail.key === 'E02' || props.detail.key === 'S02')
)
```

底部按钮区域：

```vue
<button
  v-if="!isGisViewOnlyKpi"
  ...
>
  发起督办
</button>
```

如果当前按钮文案不是固定“发起督办”，而是通用 action button，请按“督办/办理/处置”类按钮统一隐藏。

可在 GIS 来源提示 banner 或底部增加一行弱提示：

> GIS 来源定位仅用于查看，不在地图侧办理或督办。

但不要让页面变拥挤。

## 六、验收步骤

### 1. GIS 来源打开 E02

临时设置：

```ts
useRealGisOnDashboard: true
```

操作：

首页 → 点击 2 标段 → 查看关联业务 → 查看环保问题来源

检查：

- E02 弹窗打开；
- 显示 GIS 来源定位提示；
- E02-003 对应行高亮；
- 不显示“发起督办”；
- 不显示办理/处置类按钮；
- “关闭”可用。

### 2. GIS 来源打开 S02

操作：

首页 → 点击 2 标段 → 查看关联业务 → 查看安全风险来源

检查：

- S02 弹窗打开；
- 显示 GIS 来源定位提示；
- S02-002 对应行高亮；
- 不显示“发起督办”；
- 不显示办理/处置类按钮；
- “关闭”可用。

### 3. 普通 KPI 打开回归

恢复或保持同页均可：

- 直接点击首页 E02 KPI 卡片；
- 直接点击首页 S02 KPI 卡片。

检查：

- 普通 KPI 打开没有 GIS 来源提示；
- 原有按钮策略不变。

### 4. SVG 回退

最后恢复：

```ts
useRealGisOnDashboard: false
```

## 七、完成后执行

```bash
npm.cmd run check
npm.cmd run build
```

## 八、完成后回报

请回报：

1. 修改文件清单；
2. GIS 来源打开 E02 是否隐藏“发起督办”；
3. GIS 来源打开 S02 是否隐藏“发起督办”；
4. 普通 KPI 打开 E02/S02 是否保持原有按钮策略；
5. `useRealGisOnDashboard` 最终是否恢复为 `false`；
6. `npm.cmd run check` 结果；
7. `npm.cmd run build` 结果。
