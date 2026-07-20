# 罗宜高速 ESG 平台 GitHub 交付与接手说明 V1.1

更新时间：2026-07-20

## 交付组成

- `src/`：Vue 3 前端，包含领导首页、KPI 弹窗、数据上传工作台、ESG 智能助手和 GIS 模块。
- `server/`：Python 后端、MySQL 数据访问、数据库迁移、测试数据和接口测试。
- `public/data/shp/`：前端使用的 WGS84 GeoJSON 业务图层。
- `_handoff/`、`docs/`：接口契约、字段示例和阶段交接文档。
- `server/data/luoyi_esg_dev.db`：经检查的本地 SQLite 演示回退数据库。

## 本地地址

```text
领导层 ESG 看板：http://localhost:5173/#/
GIS 独立预览页：http://localhost:5173/#/gis-preview
数据填报与上传工作台：http://localhost:5173/#/workspace
ESG 智能助手：http://localhost:5173/#/assistant
后端 API：http://127.0.0.1:8765
```

## MySQL 配置

MySQL 默认使用 `127.0.0.1:3307/luoyi_esg`。账号、密码和部署地址均通过环境变量注入，配置项见项目根目录 `.env.example`。

真实密码、Token、内网连接串和正式业务数据不得写入源码、文档或 Git 历史。

## 启动

```powershell
npm.cmd ci
npm.cmd run dev
powershell.exe -ExecutionPolicy Bypass -File .\server\start_backend.ps1
```

## 验证

```powershell
npm.cmd run check
npm.cmd run build
python -m compileall -q server
```

数据库和接口测试位于 `server/*_test.py`，MySQL 建库、迁移及测试数据位于 `server/mysql_build_*`、`server/migrations` 和 `server/seed_*.py`。

## 禁止提交

- `.env`、真实账号密码、Token、API Key 和内网连接串；
- `node_modules/`、`dist/`、构建备份及 Vite 临时文件；
- `__pycache__/`、日志、PID、上传文件和缓存；
- 未脱敏的正式业务数据库或用户资料。

后续开发从最新 `main` 创建独立分支，通过 Issue、PR、CI 和代码审查合入。
