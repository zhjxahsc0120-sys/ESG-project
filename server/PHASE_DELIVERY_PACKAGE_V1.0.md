# 罗宜高速 ESG 数字化管理平台阶段交付说明 V1.0

更新时间：2026-07-17

本说明用于当前阶段对外交付、内部统合和后续样式/前端同事接续开发。当前阶段重点是：领导层首页、数据填报与上传工作台、真实 MySQL 后端、智能入库动态刷新、GIS 业务联动的联调基线。

## 1. 页面访问

| 用户端 | 地址 | 说明 |
|---|---|---|
| 领导层 ESG 看板 | `http://localhost:5174/#/` | 12 项 KPI、GIS、右侧专题、建设时间轴 |
| 数据填报与上传工作台 | `http://localhost:5174/#/workspace` | 上传任务、智能入库、审核结果、资料中心 |
| GIS 隔离预览页 | `http://localhost:5174/#/gis-preview` | 真实 GIS 独立预览、图层/要素/关联业务调试 |

## 2. 服务启动

### 2.1 MySQL

```text
host: 127.0.0.1
port: 3307
database: luoyi_esg
user: luoyi_app
```

如需手动启动本地 MySQL：

```powershell
Start-Process -FilePath 'E:\mysql\mysql-8.4.9-winx64\bin\mysqld.exe' -ArgumentList '--defaults-file=E:\mysql\my-luoyi.cnf' -WindowStyle Hidden
```

### 2.2 后端 API

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\start_backend.ps1
```

停止：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\stop_backend.ps1
```

后端地址：

```text
http://127.0.0.1:8765
```

### 2.3 前端

前端开发服务器当前通常为：

```text
http://localhost:5174
```

如需重新启动，请在项目目录执行现有前端启动命令。

## 3. 当前已完成范围

### 3.1 领导层首页

- 顶部 E/S/G 12 项 KPI 已接入后端；
- 11 个通用 KPI 弹窗已接入 API；
- S01 连续安全生产天数为专属弹窗；
- 右侧三块专题面板已接入：
  - 合规保障与风险防控成效；
  - 碳足迹与低碳增益；
  - 月报准备与输出；
- 碳足迹专题弹窗已接入；
- 月报准备与输出专题弹窗已接入；
- 领导首页默认采用 Cesium 在线底图 + GIS 业务图层，SVG 仅作为应急回退入口保留。

### 3.2 数据填报与上传工作台

- P01 工作台首页：状态卡、任务列表接入；
- P02 我的上传任务：筛选、任务列表接入；
- P03 ESG 智能入库：真实文件上传、解析、字段、候选任务、确认入库接入；
- P04 审核结果：列表、详情、轨迹、补正要求、审核通过/退回接入；
- P05 资料中心：状态卡、资料列表、详情、版本、关联任务接入；
- S01 任务办理中央弹窗：资料要求、关联资料、校验问题、审核记录、暂存、提交审核接入。

### 3.3 智能入库动态刷新

当前已固化 12 条“资料上传 → 业务表 → 首页/专题指标变化”链路：

| 上传资料类型 | 写入业务表 | 驱动指标 |
|---|---|---|
| 环境监测报告 | `env_monitoring_record` | E01 环境监测超标项次 |
| 环保问题整改资料 | `env_issue_record` | E02 当前未闭环环保问题 |
| 水保监测月报 | `water_protection_issue` | E03 当前未闭环水保问题 |
| 碳排放活动数据表 | `carbon_emission_activity` | E04 / 碳足迹专题 |
| 安全事故台账 | `safety_incident_record` | S01 连续安全生产天数重新累计 |
| 高风险作业审批资料 | `safety_risk_point` | S02 较大及以上安全风险点 |
| 劳务纠纷台账 | `labor_dispute_record` | S03 当前未办结劳务纠纷 |
| 群众诉求台账 | `appeal_record` | S04 当前未办结群众诉求 |
| 临时用地/许可资料 | `permit_record` | G02 当前临期及逾期许可事项 |
| 报批报建资料 | `compliance_procedure` | G01 当前未完成法定报批报建事项 |
| NCR/整改关闭资料 | `rectification_record` | G03 未关闭整改事项 |
| 合规资料补齐材料 | `compliance_material_gap` 状态更新 | G04 当前待补齐合规资料 |

这说明当前架构已不是单纯“页面快照展示”，而是具备“业务表动态驱动首页指标”的基本能力。

### 3.4 GIS 业务联动

- GIS API 模式可读取图层和要素；
- GIS 要素支持业务摘要；
- GIS 要素支持关联业务侧浮层；
- GIS 关联业务可跳转 E02/S02 弹窗；
- E02/S02 弹窗可按来源记录定位并高亮；
- GIS 来源打开 E02/S02 时仅查看，不显示“发起督办”；
- 领导首页 GIS 默认启用 Cesium 在线加载模式，SVG 仅作为应急回退入口保留。

## 4. 当前仍预留的范围

以下属于原型或后续增强，不作为当前阶段缺陷：

1. 真实文件内容 OCR/大模型解析；
2. 字段在线编辑器；
3. 文件预览、下载、版本回滚；
4. 月报编辑、生成、发布；
5. 领导层真实督办流程；
6. GIS 业务跳转到完整办理页面；
7. 更多外部接口数据源同步；
8. 权限系统、登录系统、组织机构真实鉴权。

## 5. 一键验收

轻量验收：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -SkipBuild
```

完整验收：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -Full
```

完整验收会真实写入测试数据，并在开始和结束时自动执行：

```powershell
server\reset_acceptance_baseline.py
```

用于保证：

- 可以验证真实入库链路；
- 验收结束后首页 KPI 基线恢复；
- 多次执行不会持续污染演示数据。

## 6. 当前核心基线值

| 指标 | 基线值 |
|---|---:|
| E01 当前环境监测超标 | 2 项 |
| E02 当前未闭环环保问题 | 5 项 |
| E03 当前未闭环水保问题 | 7 项 |
| E04 累计碳排放 | 12,856 tCO₂e |
| S01 连续安全生产天数 | 368 天 |
| S02 较大及以上安全风险点 | 6 项 |
| S03 当前未办结劳务纠纷 | 4 项 |
| S04 当前未办结群众诉求 | 3 项 |
| G01 当前未完成法定报批报建事项 | 5 项 |
| G02 当前临期及逾期许可事项 | 5 项 |
| G03 未关闭整改事项 | 6 项 |
| G04 当前待补齐合规资料 | 4 项 |

完整验收中的动态测试会临时增加这些值，结束后自动复位。

## 7. 文件边界提醒

前端样式同事可优先修改：

- `src/styles/dashboard.scss`
- `src/styles/layout.scss`
- `src/components/panels/*.vue`
- `src/components/modal/*.vue`
- `src/components/kpi/*.vue`

不建议前端样式同事修改：

- `server/`
- `src/services/api.ts`
- `src/stores/dashboard.store.ts`
- `src/config/gis.config.ts` 中默认灰度开关；
- GIS → E02/S02 的来源定位协议；
- `scripts/run-local-acceptance.ps1`。

## 8. 下一阶段建议

1. 前端样式统一完成后，统一跑完整验收；
2. 继续完善外部接口数据源同步，不把上传资料作为唯一来源；
3. 推进真实文件内容解析、OCR 和字段在线确认；
4. 对 GIS 在线底图和业务图层进行最终视觉校核，确认首页嵌入态稳定后进入正式验收。
