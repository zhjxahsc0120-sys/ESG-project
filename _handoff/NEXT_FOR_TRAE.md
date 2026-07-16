# 领导首页 GIS 嵌入第三阶段任务书：彻底完成 Cesium 懒加载分包

## 一、任务背景

第二阶段已完成：

- `useRealGisOnDashboard: false` 时首页默认显示原 SVG 地图；
- `useRealGisOnDashboard: true` 时首页可显示真实 Cesium GIS；
- `GisOverviewCesiumPanel.vue` 已使用 `defineAsyncComponent`；
- `/gis-preview` API 模式可正常访问。

但当前构建仍提示：

```text
TrafficGisOverview is dynamically imported by GisOverviewCesiumPanel.vue
but also statically imported by GisPreviewPage.vue,
dynamic import will not move module into another chunk.
```

原因是：

```text
src/views/GisPreviewPage.vue
```

仍然静态 import 了：

```ts
import { TrafficGisOverview } from '@/modules/traffic-gis-overview'
```

这会导致 Cesium 仍进入主包，首页首屏包体积没有真正降下来。

## 二、本阶段目标

完成真实懒加载分包：

1. `/gis-preview` 也改成异步加载 `TrafficGisOverview`；
2. 首页真实 GIS 面板继续异步加载；
3. 构建后应出现独立 GIS/Cesium chunk；
4. 首页默认关闭真实 GIS 时，不应把完整 Cesium 地图模块打进首页初始主包；
5. 保持 `/gis-preview` 正常访问；
6. 保持首页默认 SVG 地图正常回退。

## 三、修改范围

### 允许修改

```text
src/views/GisPreviewPage.vue
src/components/gis/GisOverviewCesiumPanel.vue
```

如确实需要，也可轻微调整：

```text
vite.config.ts
```

### 禁止修改

```text
src/views/DashboardPage.vue
src/components/gis/GisOverviewPanel.vue
src/components/gis/RouteMapSvg.vue
src/modules/traffic-gis-overview/
```

不要修改首页 KPI、右侧专题、底部时间轴、弹窗逻辑。

## 四、具体修改要求

### 1. 修改 GisPreviewPage.vue

将静态 import：

```ts
import { TrafficGisOverview } from '@/modules/traffic-gis-overview'
```

改为动态加载：

```ts
import { defineAsyncComponent } from 'vue'

const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview)
)
```

保留现有模板：

```vue
<TrafficGisOverview
  project-id="LUOYI-ESG"
  data-mode="api"
  :show-legend="true"
  :show-mode-switch="true"
/>
```

### 2. 检查 GisOverviewCesiumPanel.vue

确认它也没有静态 import：

```ts
import { TrafficGisOverview } from '@/modules/traffic-gis-overview'
```

必须继续使用：

```ts
const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview)
)
```

### 3. 如分包仍不明显，可补充 manualChunks

仅在动态 import 后构建仍没有独立 chunk 时，再考虑在 `vite.config.ts` 中加入：

```ts
build: {
  rollupOptions: {
    output: {
      manualChunks(id) {
        if (id.includes('node_modules/cesium')) {
          return 'cesium'
        }
        if (id.includes('src/modules/traffic-gis-overview')) {
          return 'traffic-gis-overview'
        }
      },
    },
  },
}
```

注意：优先依靠动态 import，不要一开始就过度改 Vite 配置。

## 五、验收标准

执行：

```powershell
npm.cmd run check
npm.cmd run build
```

构建结果需要检查：

1. 不再出现以下警告：

```text
dynamic import will not move module into another chunk
```

2. `dist/assets` 下应出现独立的 GIS 或 Cesium 相关 JS chunk，例如：

```text
cesium-xxxx.js
traffic-gis-overview-xxxx.js
```

3. 主入口 `index-xxxx.js` 体积应明显小于当前约 `5.5MB`。

4. `/gis-preview` 仍能正常访问：

```text
http://localhost:5174/#/gis-preview
```

5. 首页默认配置：

```ts
useRealGisOnDashboard: false
```

时仍显示原 SVG 地图。

6. 切换为：

```ts
useRealGisOnDashboard: true
```

时首页真实 GIS 能正常显示。

## 六、完成后回报

请将结果写入：

```text
_handoff/TRAE_DONE_REPORT.md
```

回报内容包括：

1. 修改文件清单；
2. 是否已删除 `GisPreviewPage.vue` 的静态 import；
3. `npm.cmd run check` 结果；
4. `npm.cmd run build` 结果；
5. 构建后 `dist/assets` 前 5 个 JS 文件及大小；
6. 是否还存在 `dynamic import will not move module into another chunk` 警告；
7. `/gis-preview` 是否正常；
8. 首页 SVG 回退是否正常；
9. 首页真实 GIS 开关是否正常。
