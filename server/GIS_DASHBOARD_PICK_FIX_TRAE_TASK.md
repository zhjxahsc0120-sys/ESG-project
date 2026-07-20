# 领导首页真实 GIS 缩放态点击拾取修复任务书

## 一、背景

当前 GIS 业务链路已经完成：

- GIS `business-links` 能返回 E02/S02 关联业务；
- `BusinessLinksPanel → DashboardPage → KpiDetailModal` 跳转协议已接通；
- E02/S02 弹窗可按 `sourceId` 定位并高亮。

但浏览器灰度点测发现：

- 首页真实 GIS 能正常显示线路、标段、点位；
- 图层按钮、复位按钮等 DOM 操作正常；
- 点击 2 标段线路或标签时，FeatureCard 没有打开；
- 因此无法进入“查看关联业务 → 打开 E02/S02 弹窗”链路。

经浏览器检查，问题高度疑似为：领导首页 1920×1080 画布使用 CSS `transform: scale(...)` 等比缩放，导致 Cesium canvas 可见尺寸与内部尺寸不一致，PickManager 拾取坐标未做缩放补偿。

实测数据：

```json
{
  "canvasAttrWidth": "1225",
  "canvasAttrHeight": "606",
  "canvasClientWidth": 1225,
  "canvasClientHeight": 606,
  "canvasRect": { "w": 816.93, "h": 404 },
  "wrapperTransform": "matrix(0.666667, 0, 0, 0.666667, 0, 0)"
}
```

也就是说：

- Cesium canvas 内部尺寸约 `1225×606`
- 页面可见点击区域约 `817×404`
- 缩放比例约 `0.666667`

结果是：用户点击的是缩放后的可见坐标，但 Cesium `scene.pick()` 需要的是内部 canvas 坐标。

## 二、本阶段目标

修复首页真实 GIS 嵌入态的要素点击拾取：

1. 在 `useRealGisOnDashboard=true` 时，点击 2 标段能打开 FeatureCard；
2. 点击 FeatureCard 中“查看关联业务”能打开业务侧浮层；
3. 点击“查看环保问题来源”能打开 E02 弹窗并高亮 `E02-003`；
4. 点击“查看安全风险来源”能打开 S02 弹窗并高亮 `S02-002`；
5. `/gis-preview` 不受影响；
6. 默认 `useRealGisOnDashboard` 最后恢复为 `false`。

## 三、允许修改文件

优先修改：

- `src/modules/traffic-gis-overview/cesium/interaction/PickManager.ts`

如需要，可轻微修改：

- `src/modules/traffic-gis-overview/components/TrafficGisOverview.vue`
- `src/modules/traffic-gis-overview/cesium/core/ViewerManager.ts`

## 四、禁止修改

- 不修改 `server/`
- 不修改业务接口
- 不修改 E02/S02 弹窗逻辑
- 不修改 DashboardPage 布局
- 不默认开启 `useRealGisOnDashboard`
- 不删除 SVG 回退地图

## 五、建议修复方式

### 1. 在 PickManager 中增加坐标补偿

当前逻辑类似：

```ts
private pick(position: Cesium.Cartesian2): PickResult | undefined {
  const picked = this.viewer.scene.pick(position)
  ...
}
```

建议改为：

```ts
private normalizePickPosition(position: Cesium.Cartesian2): Cesium.Cartesian2 {
  const canvas = this.viewer.scene.canvas
  const rect = canvas.getBoundingClientRect()

  if (!rect.width || !rect.height) return position

  const scaleX = canvas.clientWidth / rect.width
  const scaleY = canvas.clientHeight / rect.height

  if (!Number.isFinite(scaleX) || !Number.isFinite(scaleY)) return position

  return new Cesium.Cartesian2(
    position.x * scaleX,
    position.y * scaleY,
  )
}

private pick(position: Cesium.Cartesian2): PickResult | undefined {
  const normalized = this.normalizePickPosition(position)
  const picked = this.viewer.scene.pick(normalized)
  ...
}
```

说明：

- 未缩放时 `canvas.clientWidth === rect.width`，比例约为 1，不影响 `/gis-preview`；
- 首页缩放时可自动补偿；
- 不要硬编码 `0.666667`；
- 不要依赖 `window.devicePixelRatio`，因为这里的关键问题是 CSS transform 缩放，不是普通 DPR。

### 2. 兼容边界

如果某些浏览器下 `clientWidth` 和 `rect.width` 的关系不同，可进一步兜底：

```ts
const width = canvas.width || canvas.clientWidth
const height = canvas.height || canvas.clientHeight
const scaleX = width / rect.width
const scaleY = height / rect.height
```

但需注意不要重复乘 DPR。如果修复后 `/gis-preview` 点选异常，应回退为 `clientWidth / rect.width` 方案。

### 3. 可选：增加调试日志但不要保留噪声

修复过程中可临时打印：

```ts
console.debug('[GIS pick scale]', { position, rect, clientWidth: canvas.clientWidth, scaleX, scaleY })
```

最终提交前请删除或注释，避免控制台噪声。

## 六、验收步骤

### 1. 首页真实 GIS 灰度验收

临时设置：

```ts
useRealGisOnDashboard: true
```

访问：

`http://localhost:5174/#/`

检查：

- 真实 GIS 正常显示；
- 点击 2 标段线路或“2标段”标签；
- FeatureCard 打开；
- FeatureCard 显示“施工标段概览”；
- FeatureCard 显示“查看关联业务”按钮；
- 点击“查看关联业务”，侧浮层打开；
- 侧浮层显示：
  - `安全风险 S02-002`
  - `环保问题 E02-003`
- 点击“查看环保问题来源”：
  - E02 弹窗打开；
  - `E02-003` 明细行高亮；
- 关闭弹窗后，再点击“查看安全风险来源”：
  - S02 弹窗打开；
  - `S02-002` 明细行高亮。

### 2. `/gis-preview` 回归

访问：

`http://localhost:5174/#/gis-preview`

检查：

- 点击 2 标段仍可打开 FeatureCard；
- “查看关联业务”仍可打开；
- 预览页触发 KPI 来源定位时显示提示条；
- 控制台无错误。

### 3. SVG 回退

最后恢复：

```ts
useRealGisOnDashboard: false
```

检查：

- 首页恢复原 SVG 地图；
- KPI、专题、时间轴不受影响。

## 七、完成后执行

```bash
npm.cmd run check
npm.cmd run build
```

## 八、完成后回报

请回报：

1. 修改文件清单；
2. 是否确认问题为 CSS scale 下 Cesium pick 坐标不一致；
3. 首页真实 GIS 点击 2 标段是否能打开 FeatureCard；
4. “查看关联业务”侧浮层是否正常；
5. E02 跳转是否能高亮 `E02-003`；
6. S02 跳转是否能高亮 `S02-002`；
7. `/gis-preview` 是否正常；
8. `useRealGisOnDashboard` 最终是否恢复为 `false`；
9. `npm.cmd run check` 结果；
10. `npm.cmd run build` 结果。
