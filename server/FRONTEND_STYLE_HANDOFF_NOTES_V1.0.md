# 罗宜高速 ESG 前端样式对接说明 V1.0

更新时间：2026-07-17

## 一、当前页面访问

| 页面 | 地址 | 说明 |
|---|---|---|
| 领导层 ESG 看板 | `http://localhost:5174/#/` | 12 项 KPI、GIS、右侧专题、底部时间轴 |
| 数据填报与上传工作台 | `http://localhost:5174/#/workspace` | 上传任务、智能入库、审核结果、资料中心 |
| GIS 隔离预览页 | `http://localhost:5174/#/gis-preview` | 真实 GIS 模块独立验收页 |

## 二、后端与数据状态

- 后端 API：`http://127.0.0.1:8765`
- MySQL：`127.0.0.1:3307 / luoyi_esg`
- 领导首页 12 项 KPI 已接入 MySQL/API。
- S01 为专属弹窗，其他 KPI 走通用 `KpiDetailModal.vue`。
- 右侧三块专题面板已接入：
  - 合规保障与风险防控成效；
  - 碳足迹与低碳增益；
  - 月报准备与输出。
- 碳足迹、月报专题弹窗已接入专题 API。
- GIS 默认采用 Cesium 在线底图，SVG 仅作为应急回退入口保留。

## 三、样式同事可重点调整的文件

### 领导首页

| 文件 | 可调整内容 |
|---|---|
| `src/styles/dashboard.scss` | 首页通用视觉、卡片、字体、间距 |
| `src/styles/layout.scss` | 首页整体布局区域、右侧面板尺寸 |
| `src/components/kpi/TopKpiGroups.vue` | 顶部 E/S/G KPI 卡片样式 |
| `src/components/panels/ComplianceRiskPanel.vue` | 合规保障面板样式 |
| `src/components/panels/CarbonBenefitPanel.vue` | 碳足迹面板样式 |
| `src/components/panels/MonthlyReportPanel.vue` | 月报面板样式 |
| `src/components/modal/KpiDetailModal.vue` | 通用 KPI 弹窗、专题弹窗样式 |
| `src/components/modal/S01SafetyProductionModal.vue` | S01 专属弹窗样式 |

### GIS

| 文件 | 可调整内容 |
|---|---|
| `src/components/gis/GisOverviewCesiumPanel.vue` | 首页真实 GIS 外层嵌入容器 |
| `src/modules/traffic-gis-overview/components/MapChrome.vue` | GIS 按钮、罗盘、工具条 |
| `src/modules/traffic-gis-overview/components/FeatureCard.vue` | GIS 要素详情卡 |
| `src/modules/traffic-gis-overview/components/BusinessLinksPanel.vue` | GIS 关联业务侧浮层 |

## 四、样式修改时不要轻易动的逻辑边界

1. 不要修改 API 路径与字段名：
   - `/api/dashboard/kpis`
   - `/api/dashboard/kpi/{key}`
   - `/api/dashboard/topics/carbon`
   - `/api/dashboard/topics/monthly-report`
   - `/api/dashboard/panels`
   - `/api/esg/gis/features/{id}/business-links`

2. 不要移除 GIS 来源查看权限收口：
   - GIS 来源打开 E02/S02 只查看；
   - 不显示“发起督办”；
   - banner 显示“GIS 来源仅用于查看”。

3. `useRealGisOnDashboard` 当前应保持 `true`，不要改回 SVG 默认。
   - 首页默认显示 Cesium 在线底图和 GIS 业务图层；
   - SVG 只作为应急回退入口，不作为正式底图。

4. 不要删除 mock fallback。
   - API 关闭时页面仍需不空白。

5. 不要把专题面板的图表颜色重新写死成另一套口径。
   - 施工用油：蓝色 `#2f9cff`
   - 施工用电：绿色 `#69e36f`
   - 主要材料：紫色 `#a66cff`
   - 其他：橙色 `#ffb347`

## 五、当前已验证的数据口径

### 首页 KPI

- E01/E02/S02：MySQL 明细聚合通过；
- E03/E04：MySQL 明细聚合通过；
- S03/S04：MySQL 明细聚合通过；
- G01-G04：MySQL 明细聚合通过；
- S01：专属安全生产弹窗 API 接入。

### 右侧专题面板

- 合规保障：合规点位、碳排点位、敏感区、风险点从接口读取；
- 碳足迹：来源构成从接口读取，包含“其他”；
- 月报：当前状态、预计完成、待补资料清单从接口读取。

### GIS 关联

- GIS FeatureCard 可查看关联业务；
- E02/S02 来源按钮可打开 KPI 弹窗并定位高亮；
- CSS transform 缩放态点击拾取已修复；
- SVG 回退不受影响。

## 六、样式改完后的最小验证命令

```powershell
npm.cmd run check
npm.cmd run build
```

如涉及领导首页数据展示，建议加跑：

```powershell
$env:PYTHONIOENCODING='utf-8'
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\dashboard_acceptance_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\dashboard_panels_mysql_test.py
```

如涉及 GIS 样式，建议加跑：

```powershell
$env:PYTHONIOENCODING='utf-8'
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\gis_business_summary_test.py
```

## 七、目前建议的下一步

样式同事可以先做首页视觉统一，不需要等待后端：

1. 通用 KPI 弹窗字体、间距、表格行高统一；
2. 右侧三块专题面板视觉密度统一；
3. S01 专属弹窗继续压缩视觉尺度，避免接近全屏；
4. GIS 区域可继续做视觉细化，但不要改回 SVG 默认底图。

