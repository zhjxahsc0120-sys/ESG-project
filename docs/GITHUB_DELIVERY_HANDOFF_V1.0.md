# 罗宜高速 ESG 平台 GitHub 交付与接手说明 V1.0

更新时间：2026-07-17

## 1. 交付目标

本交付包用于把当前阶段的前端、后端、数据库脚本、测试脚本、GIS 资源与阶段说明统一纳入 GitHub 管理，便于后续由 Codex、Trae、样式同事和后端/数据同事继续协作。

当前建议作为一个完整原型工程提交，而不是只提交前端页面。原因是首页 KPI、数据上传工作台、GIS 地图、MySQL 测试数据和后端 API 已经形成联调关系，拆开提交会降低可复现性。

## 2. 当前项目组成

| 范围 | 目录/文件 | 说明 |
|---|---|---|
| 前端源码 | `src/` | Vue 3 + Vite，包含领导首页、工作台、KPI 弹窗、GIS 模块 |
| 前端依赖 | `package.json`、`package-lock.json` | 包含 Cesium、ECharts、Pinia、Vue Router 等 |
| 后端服务 | `server/app.py`、`server/mysql_api.py` | 本地 HTTP API 服务与 MySQL 数据访问层 |
| 数据库结构 | `server/schema.sql` | MySQL 表结构基础脚本 |
| 数据库初始化 | `server/init_db.py`、`server/seed_*.py`、`server/*_seed.sql` | 测试数据与专题/地图/KPI 数据补种脚本 |
| GIS 资源 | `public/data/shp/` | 由 SHP 转换后的 WGS84 GeoJSON 业务图层 |
| GIS 模块 | `src/modules/traffic-gis-overview/` | Cesium 地图、在线卫星底图、业务图层、关联业务侧浮层 |
| 验收脚本 | `server/*_test.py`、`scripts/run-local-acceptance.ps1` | KPI、工作台、GIS、上传入库等接口测试 |
| 交付文档 | `server/*.md`、`docs/*.md`、根目录阶段说明 | 阶段成果、协议、边界、下一步任务 |

## 3. 当前运行地址

当前本地 Vite 端口以实际启动为准。用户当前环境使用：

```text
领导层 ESG 看板：http://localhost:5173/#/
GIS 独立预览页：http://localhost:5173/#/gis-preview
数据填报与上传工作台：http://localhost:5173/#/workspace
```

后端默认：

```text
http://127.0.0.1:8765
```

MySQL 当前约定：

```text
host: 127.0.0.1
port: 3307
database: luoyi_esg
user: luoyi_app
password: Luoyi_App_2026!
```

注意：以上账号仅用于本地原型联调。如进入正式仓库，建议改为 `.env.example` + 本地 `.env`，不要把真实生产口令提交。

## 4. 启动方式

### 4.1 前端

```powershell
npm.cmd install
npm.cmd run dev
```

### 4.2 后端

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\start_backend.ps1
```

停止：

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\stop_backend.ps1
```

### 4.3 数据库初始化

建议先执行结构脚本，再执行初始化/补种脚本：

```powershell
python .\server\init_db.py
python .\server\seed_dashboard_snapshots_v0_2.py
python .\server\seed_environment_safety_detail_v0_4.py
python .\server\seed_governance_detail_v0_3.py
python .\server\seed_social_detail_v0_5.py
python .\server\seed_e03_e04_detail_v0_6.py
python .\server\seed_monthly_report_topic_v0_7.py
python .\server\seed_gis_map_v0_8.py
python .\server\seed_gis_business_summary_v0_9.py
python .\server\seed_multisource_data_flow_v1_0.py
```

## 5. 验证命令

前端：

```powershell
npm.cmd run check
npm.cmd run build
```

后端/接口可按阶段选择执行：

```powershell
python .\server\dashboard_acceptance_test.py
python .\server\environment_safety_kpi_mysql_test.py
python .\server\social_kpi_mysql_test.py
python .\server\governance_kpi_mysql_test.py
python .\server\s01_safety_production_business_test.py
python .\server\gis_api_test.py
python .\server\gis_business_summary_test.py
python .\server\workspace_acceptance_test.py
python .\server\ingestion_api_test.py
```

## 6. GitHub 建议提交范围

建议提交：

- `src/`
- `server/` 中源码、SQL、测试脚本和说明文档
- `public/data/shp/`
- `docs/`
- `scripts/`
- `package.json`
- `package-lock.json`
- `vite.config.ts`
- `tsconfig.json`
- `README.md`
- 根目录阶段说明文档
- `.gitignore`

不建议提交：

- `node_modules/`
- `dist/`
- `server/__pycache__/`
- `server/server.pid`
- `*.log`
- `server/storage/uploads/`
- `server/storage/cache/`
- 本地 IDE 配置、临时备份、个人环境文件

当前 `.gitignore` 已覆盖大部分不应提交范围。

## 7. GitHub 上传当前阻塞

当前机器 shell 中未找到：

```text
git.exe
gh.exe
```

因此暂时无法由 Codex 直接完成本地 `commit / push / PR`。解锁方式二选一：

1. 安装 Git for Windows 和 GitHub CLI，并完成：

```powershell
gh auth login
gh auth status
```

2. 或者由项目负责人先在 GitHub 创建空仓库并提供远端地址，安装 Git 后再由 Codex 执行首次提交。

建议首次分支：

```text
agent/luoyi-esg-stage-delivery
```

建议提交信息：

```text
deliver luoyi esg dashboard backend db and gis baseline
```

## 8. 当前功能边界

已完成：

- 领导首页 12 项 KPI 汇总；
- 12 项 KPI 弹窗基础 API 接入与真实库态联动；
- S01 专属连续安全生产弹窗；
- 合规保障、碳足迹与低碳增益、月报准备与输出专题；
- 数据填报与上传工作台 P01-P05；
- P03 智能入库原型闭环接口；
- P04 审核处理、退回、补正要求；
- P05 资料详情、版本、关联任务；
- Cesium 在线卫星底图 + GIS 业务图层；
- GIS 要素业务摘要、关联业务侧浮层；
- GIS 关联业务跳转 E02/S02 弹窗定位高亮；
- 高德卫星底图下 WGS84 → GCJ-02 展示坐标转换。

仍为预留/待对接：

- 真实文件内容解析模型；
- 外部业务系统接口数据源；
- 正式权限体系；
- 正式文件存储与预览服务；
- 生产级部署、鉴权、审计、日志治理；
- 天地图/正式影像服务 token 或政务内网地图服务。

## 9. 接手建议

1. 先保证本地能跑通前端、后端、MySQL；
2. 再跑 `dashboard_acceptance_test.py` 和 `gis_business_summary_test.py`；
3. 样式同事优先做首页视觉密度、弹窗字体、地图叠加层视觉；
4. 数据同事优先确认外部接口字段、文件解析字段和业务闭环表；
5. 后端同事继续把快照口径逐步替换为业务闭环表实时聚合；
6. GitHub 首次提交建议保持为“原型基线交付”，后续每阶段开独立分支。
