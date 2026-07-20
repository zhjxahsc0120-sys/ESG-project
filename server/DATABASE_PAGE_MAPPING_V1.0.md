# 罗宜高速 ESG 数据库表级字典与页面映射 V1.0

更新时间：2026-07-17

本文件用于把当前数据库表、页面区域、API、首页指标和动态刷新状态统一映射，便于后续统合、分工和验收。

## 1. 总体链路

```text
数据来源
→ file_asset / 外部接口原始记录 / 人工台账
→ ai_parse_job / ai_parse_field_result / 字段映射
→ 业务闭环表
→ API 聚合
→ 领导首页、专题模块、GIS 摘要、工作台
```

## 2. 领导首页 KPI 映射

| KPI | 页面显示 | API | 主业务表 | 当前状态 | 是否已验证动态刷新 |
|---|---|---|---|---|---|
| E01 | 环境监测超标项次 | `/api/dashboard/kpi/E01` | `env_monitoring_record` | 已接入业务表聚合 | 已验证 |
| E02 | 当前未闭环环保问题事项数 | `/api/dashboard/kpi/E02` | `env_issue_record` | 已接入业务表聚合 | 已验证 |
| E03 | 当前未闭环水保问题事项数 | `/api/dashboard/kpi/E03` | `water_protection_issue` | 已接入业务表聚合 | 已验证 |
| E04 | 碳排放强度/碳排放指标 | `/api/dashboard/kpi/E04` | `carbon_emission_activity` | 已接入业务表聚合 | 已验证 |
| S01 | 连续安全生产天数 | `/api/dashboard/kpi/S01` | `safety_production_record`, `safety_incident_record`, `construction_stage_record` | 已接入业务表派生 | 已验证 |
| S02 | 较大及以上安全风险点数 | `/api/dashboard/kpi/S02` | `safety_risk_point` | 已接入业务表聚合 | 已验证 |
| S03 | 未办结劳务纠纷 | `/api/dashboard/kpi/S03` | `labor_dispute_record` | 已接入业务表聚合 | 已验证 |
| S04 | 未办结群众诉求 | `/api/dashboard/kpi/S04` | `appeal_record` | 已接入业务表聚合 | 已验证 |
| G01 | 未完成法定报批报建事项 | `/api/dashboard/kpi/G01` | `compliance_procedure` | 已接入业务表聚合 | 已验证 |
| G02 | 临期及逾期许可事项 | `/api/dashboard/kpi/G02` | `permit_record` | 已接入业务表聚合 | 已验证 |
| G03 | 未关闭整改事项 | `/api/dashboard/kpi/G03` | `rectification_record` | 已接入业务表聚合 | 已验证 |
| G04 | 待补齐合规资料 | `/api/dashboard/kpi/G04` | `compliance_material_gap` | 已接入业务表聚合 | 已验证 |

首页顶部卡片接口：

```text
GET /api/dashboard/kpis
```

当前已实时覆盖并完成动态刷新验收：

- E01；
- E02；
- E03；
- E04；
- S01；
- S02；
- S03；
- S04；
- G01；
- G02；
- G03；
- G04。

## 3. 右侧专题与专题弹窗映射

| 页面区域 | API | 主表 | 当前状态 |
|---|---|---|---|
| 合规保障与风险防控成效 | `/api/dashboard/panels` | `rectification_record`, `env_issue_record`, `water_protection_issue`, `safety_risk_point`, `compliance_procedure`, `permit_record` | 已接入聚合 |
| 碳足迹与低碳增益面板 | `/api/dashboard/panels` | `carbon_emission_activity`, `carbon_material_usage`, `low_carbon_measure` | 已接入聚合 |
| 月报准备与输出面板 | `/api/dashboard/panels` | `monthly_report_cycle`, `monthly_report_gap`, `monthly_report_status_chain` | 已接入聚合 |
| 碳足迹专题弹窗 | `/api/dashboard/topics/carbon` | `carbon_emission_activity`, `carbon_material_usage`, `low_carbon_measure` | 已接入 |
| 月报专题弹窗 | `/api/dashboard/topics/monthly-report` | `monthly_report_cycle`, `monthly_report_group_progress`, `monthly_report_chapter`, `monthly_report_gap`, `monthly_report_status_chain` | 已接入 |

## 4. GIS 映射

| 能力 | API / 表 | 当前状态 |
|---|---|---|
| 图层列表 | `/api/esg/gis/layers` | 已接入 |
| 图层要素 | `/api/esg/gis/features` | 已接入 |
| 要素业务摘要 | GIS 要素业务摘要表/API | 已接入 |
| 要素关联事项 | `/api/esg/gis/features/{featureId}/relations` | 已接入 |
| 要素关联业务跳转 | `/api/esg/gis/features/{featureId}/business-links` | 已接入 |
| GIS → E02 定位 | `env_issue_record` sourceId | 已接入 |
| GIS → S02 定位 | `safety_risk_point` sourceId | 已接入 |

当前默认策略：

```ts
useRealGisOnDashboard: true
```

说明：领导首页默认采用 Cesium 在线底图 + GIS 业务图层；原 SVG 地图仅作为应急回退组件保留。

## 5. 数据填报与上传工作台映射

### 5.1 P01/P02 上传任务

| 页面区域 | API | 主表 | 当前状态 |
|---|---|---|---|
| 工作台状态卡 | `/api/workspace/summary` | `workspace_summary` / 任务聚合 | 已接入 |
| 工作台任务列表 | `/api/workspace/tasks` | `upload_task` | 已接入 |
| 我的上传任务筛选 | `/api/workspace/tasks` | `upload_task` | 已接入 |
| 任务办理弹窗 | `/api/workspace/tasks/{taskId}/detail` | `upload_task`, `upload_task_requirement`, `document_task_relation`, `review_record` | 已接入 |
| 暂存任务 | `/api/workspace/tasks/{taskId}/save` | 任务办理状态 | 已接入 |
| 关联资料 | `/api/workspace/tasks/{taskId}/link-document` | `document_task_relation`, `upload_task_requirement` | 已接入 |
| 提交审核 | `/api/workspace/tasks/{taskId}/submit` | `review_record`, `upload_task` | 已接入 |

### 5.2 P03 ESG 智能入库

| 功能 | API | 主表 | 当前状态 |
|---|---|---|---|
| 解析队列 | `/api/workspace/ai/parse-queue` | `ai_parse_job`, `file_asset` | 已接入 |
| 真实文件上传 | `/api/workspace/files/upload` | `file_asset` | 已接入 multipart |
| 发起解析 | `/api/workspace/files/{fileId}/parse` | `ai_parse_job`, `ai_parse_field_result`, `task_match_candidate` | 已接入 |
| 查询解析任务 | `/api/workspace/parse-jobs/{jobId}` | `ai_parse_job` | 已接入 |
| 查询抽取字段 | `/api/workspace/parse-jobs/{jobId}/fields` | `ai_parse_field_result` | 已接入 |
| 查询候选任务 | `/api/workspace/parse-jobs/{jobId}/match-candidates` | `task_match_candidate` | 已接入 |
| 确认入库 | `/api/workspace/parse-jobs/{jobId}/confirm` | `document_record` + 目标业务表 + `source_record_trace` | 已接入 |

当前确认入库目标表：

| 资料类型 | 目标表 | 驱动指标 |
|---|---|---|
| 环保问题整改资料 | `env_issue_record` | E02 |
| 水保监测月报 | `water_protection_issue` | E03 |
| 碳排放活动数据表 | `carbon_emission_activity` | E04 / 碳专题 |
| 安全事故台账 | `safety_incident_record` | S01 |
| 高风险作业审批资料 | `safety_risk_point` | S02 |
| 劳务纠纷台账 | `labor_dispute_record` | S03 |
| 群众诉求台账 | `appeal_record` | S04 |
| NCR/整改资料 | `rectification_record` | G03 |
| 环境监测报告 | `env_monitoring_record` | E01 |
| 临时用地/许可资料 | `permit_record` | G02 |
| 报批报建资料 | `compliance_procedure` | G01 |
| 合规资料补齐材料 | `compliance_material_gap` 状态更新 | G04 |
| 工资支付资料 | `salary_payment_record` | 工资支付记录，暂不直接等同 S03 纠纷 |

### 5.3 P04 审核结果

| 功能 | API | 主表 | 当前状态 |
|---|---|---|---|
| 审核列表 | `/api/workspace/reviews` | `review_record` | 已接入 |
| 审核详情 | `/api/workspace/reviews/{reviewId}` | `review_record` | 已接入 |
| 审核轨迹 | `/api/workspace/reviews/{reviewId}/timeline` | `review_timeline` | 已接入 |
| 补正要求 | `/api/workspace/reviews/{reviewId}/requirements` | `review_requirement` | 已接入 |
| 审核通过 | `/api/workspace/reviews/{reviewId}/approve` | `review_record`, `upload_task` | 已接入 |
| 审核退回 | `/api/workspace/reviews/{reviewId}/return` | `review_record`, `review_requirement`, `upload_task` | 已接入 |

### 5.4 P05 资料中心

| 功能 | API | 主表 | 当前状态 |
|---|---|---|---|
| 资料状态卡 | `/api/workspace/documents/summary` | `document_record` | 已接入 |
| 资料列表 | `/api/workspace/documents` | `document_record` | 已接入 |
| 资料详情 | `/api/workspace/documents/{documentId}` | `document_record`, `file_asset` | 已接入 |
| 版本记录 | `/api/workspace/documents/{documentId}/versions` | `document_version` | 已接入 |
| 关联任务 | `/api/workspace/documents/{documentId}/relations` | `document_task_relation`, `upload_task` | 已接入 |

## 6. 数据治理支撑表

| 表名 | 中文说明 | 用途 | 当前状态 |
|---|---|---|---|
| `file_asset` | 文件资产 | 记录上传文件、哈希、存储路径 | 已使用 |
| `ai_parse_job` | AI 解析任务 | 管理一次解析任务 | 已使用 |
| `ai_parse_field_result` | 字段抽取结果 | 存放 AI/规则抽取字段 | 已使用 |
| `ai_field_mapping_rule` | 字段映射规则 | 定义资料字段到业务字段映射 | 已使用 |
| `task_match_candidate` | 候选任务 | 智能推荐资料关联任务 | 已使用 |
| `data_ingestion_job` | 数据入库任务 | 记录确认入库任务 | 已使用 |
| `data_quality_check_result` | 数据质量校核 | 记录字段完整性、合法性等校核结果 | 已使用 |
| `source_record_trace` | 来源追溯 | 记录资料/接口到业务表记录的追溯 | 已使用 |
| `document_record` | 资料档案 | 资料中心主表 | 已使用 |
| `document_version` | 资料版本 | 资料版本管理 | 已使用 |
| `document_task_relation` | 资料任务关系 | 资料复用、任务关联 | 已使用 |

## 7. 快照/兜底表

| 表名 | 当前作用 | 长期定位 |
|---|---|---|
| `indicator_result` | 首页 KPI 基础值 | 兜底/缓存，逐步被业务表聚合覆盖 |
| `dashboard_kpi_detail_snapshot` | KPI 弹窗结构模板与兜底数据 | fallback，不作为长期主数据源 |
| `dashboard_topic_snapshot` | 专题弹窗结构模板 | fallback/模板 |
| `workspace_summary` | 工作台状态卡快照 | 可保留为缓存，也可改为任务聚合 |

## 8. 已验证动态刷新测试

| 测试文件 | 覆盖链路 |
|---|---|
| `ingestion_dashboard_refresh_test.py` | 水保资料 → E03 |
| `carbon_ingestion_dashboard_refresh_test.py` | 碳排资料 → E04 / 碳专题 |
| `ingestion_multi_kpi_refresh_test.py` | 环保问题 → E02；高风险作业 → S02；NCR/整改 → G03 |

一键完整验收：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -Full
```

## 9. 下一批建议补齐

| 优先级 | 指标 | 建议链路 |
|---|---|---|
| A | 外部接口原始数据 | 监测/许可/安全/诉求等接口 → 原始表 → 业务闭环表 |
| A | 真实文件解析 | PDF/Excel/OCR → 字段确认 → 业务闭环表 |
| B | S01 深化 | 事故等级、中断规则、历史连续周期展示 |

## 10. 结论

当前数据库已经可以支撑“业务表驱动首页”的架构方向。

后续重点：

```text
继续补动态刷新链路
继续补外部接口接入
继续弱化页面快照主数据地位
继续完善资料来源追溯和质量校核
```
