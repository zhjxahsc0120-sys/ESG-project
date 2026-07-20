# 罗宜高速 ESG 前后端联调基线 V1.0

更新时间：2026-07-17

本文件用于固化当前“领导层 ESG 看板 + 数据填报与上传工作台 + GIS 业务联动”的真实库态联调范围。后续 Trae 或样式同事继续修改前端时，建议以本文件作为当前基线，旧版 `FRONTEND_BACKEND_BASELINE.md` 仅作为历史记录参考。

## 1. 运行环境

### 前端

```text
http://localhost:5174/#/
http://localhost:5174/#/workspace
http://localhost:5174/#/gis-preview
```

### 后端

```text
http://127.0.0.1:8765
```

启动：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\start_backend.ps1
```

停止：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\stop_backend.ps1
```

### MySQL

```text
host: 127.0.0.1
port: 3307
database: luoyi_esg
user: luoyi_app
```

当前后端策略：

- MySQL 可用时优先读取 MySQL；
- MySQL 不可用时保留 SQLite/JSON fallback，保证前端原型不空白；
- 验收以 MySQL 真实库态为主。

## 2. 领导层首页 API 接入状态

### 2.1 顶部 12 项 KPI

| KPI | 名称 | 当前状态 |
|---|---|---|
| E01 | 环境监测超标项次 | 已接入 MySQL 明细聚合 |
| E02 | 当前未闭环环保问题事项数 | 已接入 MySQL 明细聚合 |
| E03 | 当前未闭环水保问题事项数 | 已接入 MySQL 明细聚合 |
| E04 | 碳排放强度 / 碳排放专题指标 | 已接入 MySQL 明细聚合 |
| S01 | 连续安全生产天数 | 已接入专属 API 与专属弹窗 |
| S02 | 当前在管较大及以上安全风险点数 | 已接入 MySQL 明细聚合 |
| S03 | 当前未办结劳务纠纷 | 已接入 MySQL 明细聚合 |
| S04 | 当前未办结群众诉求 | 已接入 MySQL 明细聚合 |
| G01 | 当前未完成法定报批报建事项 | 已接入 MySQL 明细聚合 |
| G02 | 当前临期及逾期许可事项 | 已接入 MySQL 明细聚合 |
| G03 | 当前未关闭整改事项 | 已接入 MySQL 明细聚合 |
| G04 | 当前待补齐合规资料 | 已接入 MySQL 明细聚合 |

接口：

```text
GET /api/dashboard/kpis
GET /api/dashboard/kpi/{KPI_CODE}
```

### 2.2 右侧专题面板

接口：

```text
GET /api/dashboard/panels
```

| 面板 | 当前状态 |
|---|---|
| 合规保障与风险防控成效 | 已从合规手续、安全风险、整改、环保/水保问题等业务表聚合 |
| 碳足迹与低碳增益 | 已从碳排放活动表聚合，来源构成包含“其他” |
| 月报准备与输出 | 已从月报周期、章节、缺项、状态链业务表聚合 |

### 2.3 专题弹窗

接口：

```text
GET /api/dashboard/topics/carbon
GET /api/dashboard/topics/monthly-report
```

| 专题 | 当前状态 |
|---|---|
| 碳足迹与低碳增益 | 已接入专题 API，包含累计碳足迹、低碳增益、来源构成、成本影响、主要措施 |
| 月报准备与输出 | 已接入专题 API，包含 E/S/G 进度、章节清单、缺项清单、状态链 |

## 3. GIS 接入状态

### 3.1 默认策略

文件：

```text
src/config/gis.config.ts
```

默认：

```ts
useRealGisOnDashboard: true
```

说明：

- 领导首页默认采用 Cesium 在线底图 + GIS 业务图层；
- 原 SVG 地图仅作为应急回退入口保留，不作为默认底图；
- `/gis-preview` 始终用于独立预览和调试。

### 3.2 GIS API

```text
GET /api/esg/gis/layers
GET /api/esg/gis/features
GET /api/esg/gis/features/{featureId}/relations
GET /api/esg/gis/features/{featureId}/business-links
```

当前已完成：

- API 模式图层可加载；
- 首页缩放态 Cesium 点击拾取已修复；
- GIS FeatureCard 可查看关联业务；
- GIS 关联业务可跳转 E02/S02 弹窗；
- E02/S02 弹窗可按 sourceId 定位并高亮；
- GIS 来源打开 E02/S02 时仅查看，不显示“发起督办”。

## 4. 数据填报与上传工作台接入状态

访问：

```text
http://localhost:5174/#/workspace
```

### P01/P02 任务

```text
GET /api/workspace/summary
GET /api/workspace/tasks
GET /api/workspace/tasks/{taskId}/detail
POST /api/workspace/tasks/{taskId}/save
POST /api/workspace/tasks/{taskId}/link-document
POST /api/workspace/tasks/{taskId}/submit
```

当前状态：

- 工作台首页状态卡、任务列表已接入；
- 我的上传任务筛选已接入；
- 任务办理中央弹窗资料要求、已关联资料、校验问题、审核记录已接入；
- 暂存、关联资料、提交审核已接入；
- 待补正任务按钮文案为“重新提交审核”。

### P03 ESG 智能入库

```text
GET /api/workspace/ai/parse-queue
POST /api/workspace/files/upload
POST /api/workspace/files/{fileId}/parse
GET /api/workspace/parse-jobs/{jobId}
GET /api/workspace/parse-jobs/{jobId}/fields
GET /api/workspace/parse-jobs/{jobId}/match-candidates
POST /api/workspace/parse-jobs/{jobId}/confirm
```

当前状态：

- 上传/解析/字段查询/候选任务/确认入库闭环已接入；
- 文件上传已支持 `multipart/form-data` 真实文件上传；
- 环境监测报告确认入库后会写入 `env_monitoring_record`，并可驱动首页 E01 指标动态变化；
- 环保问题资料确认入库后会写入 `env_issue_record`，并可驱动首页 E02 指标动态变化；
- 水保资料确认入库后会写入 `water_protection_issue`，并可驱动首页 E03 指标动态变化；
- 碳排放活动资料确认入库后会写入 `carbon_emission_activity`，并可驱动首页 E04 与碳足迹专题动态变化；
- 安全事故台账确认入库后会写入 `safety_incident_record`，并可驱动首页 S01 连续安全生产天数重新累计；
- 高风险作业审批资料确认入库后会写入 `safety_risk_point`，并可驱动首页 S02 指标动态变化；
- 劳务纠纷台账确认入库后会写入 `labor_dispute_record`，并可驱动首页 S03 指标动态变化；
- 群众诉求台账确认入库后会写入 `appeal_record`，并可驱动首页 S04 指标动态变化；
- 临时用地/许可资料确认入库后会写入 `permit_record`，并可驱动首页 G02 指标动态变化；
- 报批报建资料确认入库后会写入 `compliance_procedure`，并可驱动首页 G01 指标动态变化；
- NCR/整改资料确认入库后会写入 `rectification_record`，并可驱动首页 G03 指标动态变化；
- 合规资料补齐材料确认入库后会更新 `compliance_material_gap`，并可驱动首页 G04 指标动态变化；
- 字段在线编辑器、真实文件预览仍为预留。

### P04 审核结果

```text
GET /api/workspace/reviews
GET /api/workspace/reviews/{reviewId}
GET /api/workspace/reviews/{reviewId}/timeline
GET /api/workspace/reviews/{reviewId}/requirements
POST /api/workspace/reviews/{reviewId}/approve
POST /api/workspace/reviews/{reviewId}/return
```

当前状态：

- 审核列表、右侧详情、审核轨迹、补正要求已接入；
- 待审核记录支持审核通过/审核退回；
- 已退回记录支持进入补正任务弹窗；
- 补正要求展示“待补正/已补正”状态标签。

### P05 资料中心与档案

```text
GET /api/workspace/documents/summary
GET /api/workspace/documents
GET /api/workspace/documents/{documentId}
GET /api/workspace/documents/{documentId}/versions
GET /api/workspace/documents/{documentId}/relations
```

当前状态：

- 状态卡、资料列表、分类筛选、类型筛选已接入；
- 点击资料行加载详情、版本、关联任务；
- 预览、版本回滚、下载、复用到其他任务仍为预留。

## 5. 当前仍保留 mock / 预留的范围

以下不是错误，是原型阶段保留能力：

1. API 不可用时的 mock fallback；
2. 工作台智能助手真实问答；
3. 资料预览、版本回滚、文件下载；
4. P03 字段在线编辑器；
5. 真实二进制文件内容解析；
6. 月报上传、编辑、发布；
7. GIS 业务跳转到完整业务办理页面；
8. 领导层发起督办真实流程。

## 6. 权限边界

领导层首页当前定位：

- 可查看；
- 可定位；
- 可进入 KPI/专题/GIS 详情；
- 不在 GIS 侧办理事项；
- 不在 GIS 来源打开的 E02/S02 弹窗里发起督办；
- 普通 KPI 卡片打开的原有按钮策略暂保持不变。

上传用户工作台当前定位：

- 可办理资料上传、补正、提交审核；
- 可在原型范围内进行审核处理；
- 不涉及领导层看板权限。

## 7. 核心回归命令

### 一键本地验收

轻量验收，包含领导首页、右侧专题、碳/月报专题、GIS 业务摘要、前端类型检查：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -SkipBuild
```

完整验收，包含全量 KPI 接口测试、工作台接口、智能入库真实文件上传/解析/确认入库链路与前端构建：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -Full
```

说明：

- `-Full` 会真实执行文件上传、解析、确认入库、业务表同步；
- 脚本开始前会执行 `server\reset_acceptance_baseline.py`；
- 脚本结束后无论成功失败都会再次执行 `server\reset_acceptance_baseline.py`；
- 这样可以验证“上传资料会动态影响业务表/首页指标”的真实链路，同时避免测试数据污染 E03/G03 等首页基线。

### 后端/接口

```powershell
$env:PYTHONIOENCODING='utf-8'
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\dashboard_acceptance_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\environment_safety_kpi_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\e03_e04_kpi_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\social_kpi_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\governance_kpi_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\dashboard_panels_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\carbon_topic_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\monthly_topic_mysql_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\gis_business_summary_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\workspace_acceptance_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\multipart_upload_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\ingestion_api_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\ingestion_dashboard_refresh_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\carbon_ingestion_dashboard_refresh_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\ingestion_multi_kpi_refresh_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\parse_rule_dedup_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\confirm_ingestion_trace_test.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\confirm_updates_task_test.py
```

### 前端

```powershell
npm.cmd run check
npm.cmd run build
```

## 8. 当前建议的推进顺序

1. 样式同事先做首页视觉统一和弹窗视觉密度优化；
2. 后端继续补强真实文件解析与字段确认入库；
3. GIS 底图采用 Cesium 在线加载模式，后续只做视觉细化与业务联动校核；
4. 下一轮再设计“业务闭环表 → 首页指标实时聚合”的治理层规范，减少长期依赖快照表。
