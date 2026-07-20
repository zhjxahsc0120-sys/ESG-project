# 阶段交付文件范围说明 V1.0

更新时间：2026-07-17

## 1. 正式交付文件

### 1.1 前端源码

| 路径 | 说明 |
|---|---|
| `src/` | 前端页面、组件、类型、服务、状态管理 |
| `public/` | 静态资源、GIS GeoJSON 数据 |
| `package.json` | 前端依赖与脚本 |
| `vite.config.ts` | Vite、Cesium 静态资源、代理配置 |
| `tsconfig.json` | TypeScript 配置 |

### 1.2 后端源码

| 路径 | 说明 |
|---|---|
| `server/app.py` | HTTP API 服务 |
| `server/mysql_api.py` | MySQL 业务接口与聚合逻辑 |
| `server/mysql_db.py` | MySQL 连接 |
| `server/start_backend.ps1` | 后端启动脚本 |
| `server/stop_backend.ps1` | 后端停止脚本 |
| `server/*_test.py` | 当前阶段自动化验收脚本 |
| `scripts/run-local-acceptance.ps1` | 一键验收脚本 |

### 1.3 数据库脚本与设计文档

| 路径 | 说明 |
|---|---|
| `server/mysql_build_v0.1/` | MySQL 初始建库脚本 |
| `server/intelligent_ingestion/` | 智能入库设计与扩展说明 |
| `server/DATABASE_PAGE_MAPPING_V1.0.md` | 表级字典与页面映射 |
| `server/DASHBOARD_DATA_GOVERNANCE_DESIGN_V1.0.md` | 首页指标数据治理设计 |
| `server/EXTERNAL_DATA_INGESTION_DESIGN_V1.0.md` | 外部接口接入设计 |
| `server/PHASE_DELIVERY_PACKAGE_V1.0.md` | 阶段交付说明 |
| `server/FRONTEND_BACKEND_BASELINE_V1.0.md` | 前后端联调基线 |
| `server/GIS_GRAY_ACCEPTANCE_PLAN_V1.0.md` | GIS 灰度验收方案 |

## 2. 运行生成文件，不建议打包为正式源码

| 路径/类型 | 说明 |
|---|---|
| `server/__pycache__/` | Python 缓存 |
| `server/*.pyc` | Python 编译缓存 |
| `server/server.pid` | 后端运行进程号 |
| `dist/` | 前端构建产物，可按需单独交付 |
| `node_modules/` | 前端依赖 |
| `.vite/` | Vite 缓存 |
| `server/storage/uploads/` | 本地测试上传文件，可按需清理或另行归档 |
| `scripts/pr-checker.log` | 本地日志 |

## 3. 当前阶段建议保留但标注为测试/验收文件

| 文件 | 说明 |
|---|---|
| `server/dashboard_acceptance_test.py` | 领导首页总体验收 |
| `server/environment_safety_kpi_mysql_test.py` | E01/E02/S02 验收 |
| `server/e03_e04_kpi_mysql_test.py` | E03/E04 验收 |
| `server/social_kpi_mysql_test.py` | S03/S04 验收 |
| `server/governance_kpi_mysql_test.py` | G01-G04 验收 |
| `server/dashboard_panels_mysql_test.py` | 右侧专题面板验收 |
| `server/carbon_topic_mysql_test.py` | 碳专题验收 |
| `server/monthly_topic_mysql_test.py` | 月报专题验收 |
| `server/gis_business_summary_test.py` | GIS 摘要与联动验收 |
| `server/workspace_acceptance_test.py` | 工作台只读验收 |
| `server/multipart_upload_test.py` | 真实文件上传验收 |
| `server/ingestion_api_test.py` | 智能入库端到端验收 |
| `server/ingestion_dashboard_refresh_test.py` | 水保资料驱动 E03 验收 |
| `server/carbon_ingestion_dashboard_refresh_test.py` | 碳排资料驱动 E04/专题验收 |
| `server/ingestion_multi_kpi_refresh_test.py` | E02/S02/G03 动态刷新验收 |
| `server/reset_acceptance_baseline.py` | 验收前后数据复位 |

## 4. 不建议前端样式同事修改的文件

| 文件/目录 | 原因 |
|---|---|
| `server/` | 后端 API、数据库、验收脚本 |
| `src/services/api.ts` | API 合同 |
| `src/stores/dashboard.store.ts` | 首页数据装载逻辑 |
| `src/config/gis.config.ts` | GIS 灰度开关，默认应保持 false |
| `src/modules/traffic-gis-overview/adapters/` | GIS API 适配 |
| `src/modules/traffic-gis-overview/cesium/interaction/PickManager.ts` | 首页缩放态点击拾取修复 |
| `scripts/run-local-acceptance.ps1` | 一键验收脚本 |

## 5. 样式同事可以安全修改的范围

| 文件/目录 | 可修改内容 |
|---|---|
| `src/styles/dashboard.scss` | 首页样式 |
| `src/styles/layout.scss` | 布局密度 |
| `src/components/kpi/` | KPI 卡片视觉 |
| `src/components/panels/` | 右侧专题面板视觉 |
| `src/components/modal/` | 弹窗视觉 |
| `src/components/workspace/` | 工作台视觉，但不要改 API 调用 |
| `src/modules/traffic-gis-overview/components/MapChrome.vue` | GIS 工具条视觉 |
| `src/modules/traffic-gis-overview/components/FeatureCard.vue` | GIS 要素卡片视觉 |
| `src/modules/traffic-gis-overview/components/BusinessLinksPanel.vue` | GIS 关联业务侧浮层视觉 |

## 6. 打包建议

### 6.1 源码交付包

建议包含：

```text
src/
server/
scripts/
public/
package.json
vite.config.ts
tsconfig.json
README / 阶段说明文档
```

建议排除：

```text
node_modules/
dist/
server/__pycache__/
server/server.pid
server/storage/uploads/
*.log
```

### 6.2 演示交付包

如需交付可直接打开的演示包，可单独包含：

```text
dist/
server/
MySQL 建库脚本
启动说明
```

## 7. 交付前必须执行

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run-local-acceptance.ps1 -Full
```

通过后再打包。
