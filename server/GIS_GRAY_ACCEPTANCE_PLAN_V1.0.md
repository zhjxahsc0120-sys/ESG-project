# 领导首页真实 GIS 灰度验收方案 V1.0

更新时间：2026-07-17

## 1. 灰度原则

真实 GIS 当前作为增强能力灰度验收，不默认替换领导首页 SVG 地图。

默认配置：

```ts
// src/config/gis.config.ts
useRealGisOnDashboard: false
```

灰度验收时临时修改：

```ts
useRealGisOnDashboard: true
```

验收结束必须恢复：

```ts
useRealGisOnDashboard: false
```

## 2. 当前已具备能力

- `/gis-preview` 可独立预览真实 GIS；
- 首页真实 GIS 通过 `GisOverviewCesiumPanel.vue` 懒加载；
- Cesium 与 GIS 模块已拆分 chunk，不进入首页初始主包；
- API 模式支持图层和要素加载；
- 首页缩放态点击拾取已做 CSS transform 坐标补偿；
- GIS 要素可打开 FeatureCard；
- FeatureCard 可查看关联业务；
- 关联业务可打开 E02/S02 弹窗并定位高亮；
- GIS 来源打开 E02/S02 时只查看，不显示“发起督办”。

## 3. 灰度验收范围

### 3.1 `/gis-preview` 独立页

访问：

```text
http://localhost:5174/#/gis-preview
```

验收项：

1. 可看到路线、弃渣点、水源保护区、生态保护区、边坡监测点；
2. 图层按钮可切换；
3. 复位按钮有效；
4. 点击要素可弹出 FeatureCard；
5. FeatureCard 可查看完整调试信息；
6. 关联业务可打开侧浮层；
7. 控制台无错误。

### 3.2 领导首页灰度态

临时设置：

```ts
useRealGisOnDashboard: true
```

访问：

```text
http://localhost:5174/#/
```

验收项：

1. 首页 GIS 区域内能显示真实线路和点位；
2. 不遮挡右侧三块专题；
3. 不遮挡底部建设时间轴；
4. 页面无额外滚动条；
5. 首页不显示“配置后台”按钮；
6. 图层按钮和复位按钮可用；
7. 点击路线/点位可打开 FeatureCard；
8. FeatureCard 不越界；
9. 点击“查看关联业务”可打开侧浮层；
10. 侧浮层不越界；
11. 点击环保问题来源可打开 E02 并高亮；
12. 点击安全风险来源可打开 S02 并高亮；
13. GIS 来源打开 E02/S02 不显示“发起督办”；
14. 关闭弹窗后首页仍正常。

### 3.3 SVG 回退

恢复：

```ts
useRealGisOnDashboard: false
```

验收项：

1. 首页恢复原 SVG 地图；
2. 12 项 KPI 可正常点击；
3. 右侧专题可正常点击；
4. 底部时间轴无变化；
5. `npm.cmd run check` 通过；
6. `npm.cmd run build` 通过。

## 4. 禁止事项

灰度阶段暂不做：

- 不默认启用真实 GIS；
- 不删除 SVG 地图；
- 不改 DashboardPage 主布局；
- 不新增 GIS 办理、处置、督办动作；
- 不把 GIS 侧关联业务直接跳转到未完成页面；
- 不修改 E02/S02 的普通 KPI 打开逻辑。

## 5. 权限边界

GIS 侧关联业务是“查看线索”，不是“办理入口”。

| 场景 | 可做 | 不可做 |
|---|---|---|
| FeatureCard | 查看要素摘要 | 办理事项 |
| BusinessLinksPanel | 查看关联业务线索 | 处置、派单 |
| GIS 来源打开 E02/S02 | 查看并定位高亮 | 发起督办 |
| 普通 KPI 卡片打开 E02/S02 | 保持原页面策略 | 不受 GIS 权限收口影响 |

## 6. 建议验收命令

灰度态手动验收前后均建议执行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -SkipBuild
```

阶段提交前执行：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -Full
```

## 7. 当前结论

真实 GIS 已具备灰度验收条件，但不建议默认启用。当前最稳策略是：

```text
正式演示：SVG 首页
空间态势演示：/gis-preview 或临时打开真实 GIS 灰度开关
最终替换：等样式、性能、点击拾取、弹窗层级全部稳定后再决定
```

