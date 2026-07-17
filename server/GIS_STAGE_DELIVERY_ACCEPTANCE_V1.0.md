# 罗宜高速 ESG 真实 GIS 阶段交付与验收说明 V1.0

更新时间：2026-07-16  
适用范围：领导层 ESG 看板首页 GIS 区域、`/gis-preview` 隔离预览页、GIS 后端 API、MySQL GIS 业务摘要与关联业务线索。

## 1. 当前结论

真实 GIS 已完成从“隔离预览”到“首页灰度嵌入”的阶段性交付。

当前默认策略是：

- 正式首页默认仍使用原 SVG 地图，保障演示稳定；
- 真实 Cesium GIS 可通过灰度开关启用；
- `/gis-preview` 保留为独立调试与验收入口；
- GIS 要素已接入 MySQL 图层/要素数据；
- GIS 要素已具备业务摘要、关联事项和关联业务线索能力；
- 领导层仅查看，不在地图侧办理、处置或发起督办。

## 2. 页面访问地址

| 页面 | 地址 | 说明 |
|---|---|---|
| 领导层 ESG 看板首页 | `http://localhost:5174/#/` | 默认展示 SVG 地图；灰度开关打开后展示真实 GIS |
| GIS 独立预览页 | `http://localhost:5174/#/gis-preview` | 真实 GIS 调试、图层、点选、配置后台验收页 |
| 后端健康检查 | `http://127.0.0.1:8765/health` | 确认 API 与 MySQL 状态 |

## 3. 灰度开关

配置文件：

`src/config/gis.config.ts`

当前默认：

```ts
useRealGisOnDashboard: false
dashboardDataMode: 'api'
projectId: 'LUOYI-ESG'
```

启用首页真实 GIS：

```ts
useRealGisOnDashboard: true
```

恢复首页 SVG 地图：

```ts
useRealGisOnDashboard: false
```

要求：

- 正式演示前默认保持 `false`；
- 灰度验收、空间态势演示时可临时改为 `true`；
- 每次点测完成后必须恢复为 `false`。

## 4. 已完成前端能力

### 4.1 `/gis-preview`

已完成：

- API 模式加载图层；
- 自动飞到罗宜高速范围；
- 显示 1/2/3 标段路线；
- 显示弃渣点、水源保护区、生态保护区、边坡监测点；
- 图层模式切换：全线、标段、环保点位、风险点；
- 复位；
- 配置后台；
- 点击要素显示 FeatureCard；
- preview 模式显示完整调试字段；
- preview 模式可加载关联事项；
- preview 模式可打开关联业务线索侧浮层；
- 点击“查看来源”显示预留提示，不跳转。

### 4.2 领导层首页真实 GIS 灰度态

已完成：

- 首页 GIS 区域内嵌真实 Cesium GIS；
- 首页默认不启用，需灰度开关打开；
- 首页隐藏“配置后台”按钮；
- 首页工具按钮更紧凑；
- 首页地图亮度降低，避免抢 KPI 与专题模块视觉权重；
- 点击要素展示领导层摘要口径；
- 详情卡显示中文状态，不显示 `normal / attention`；
- dashboard 模式只显示关联事项摘要，不展开长列表；
- 点击“查看关联业务”打开 GIS 面板内侧浮层；
- 侧浮层限制在 GIS 面板内部；
- 不遮挡右侧专题模块；
- 不遮挡底部建设阶段时间轴；
- 不出现“办理 / 处置 / 发起督办”操作。

## 5. 后端 API 清单

基础地址：

`http://127.0.0.1:8765`

前端代理：

`/api` → `http://127.0.0.1:8765`

| 接口 | 用途 |
|---|---|
| `GET /api/esg/gis/layers?projectId=LUOYI-ESG` | 获取 GIS 图层清单 |
| `GET /api/esg/gis/features?projectId=LUOYI-ESG` | 获取 GIS 空间要素 |
| `GET /api/esg/gis/features?projectId=LUOYI-ESG&layerId=section-2` | 按图层获取要素 |
| `GET /api/esg/gis/features?projectId=LUOYI-ESG&sectionId=2标段` | 按标段过滤要素 |
| `GET /api/esg/gis/features/{featureId}?projectId=LUOYI-ESG` | 获取单个要素详情 |
| `GET /api/esg/gis/features/{featureId}/relations?projectId=LUOYI-ESG` | 获取要素关联事项明细 |
| `GET /api/esg/gis/features/{featureId}/business-links?projectId=LUOYI-ESG` | 获取要素关联业务线索，用于侧浮层 |

示例：

```text
GET /api/esg/gis/features/section-2-1/business-links?projectId=LUOYI-ESG
```

核心返回：

```json
{
  "featureName": "2标段",
  "summary": {
    "total": 2,
    "pendingCount": 2,
    "highRiskCount": 1
  },
  "items": [
    {
      "typeLabel": "安全风险",
      "code": "S02-002",
      "title": "高边坡施工较大风险点",
      "status": "持续管控",
      "targetKpiCode": "S02",
      "actionEnabled": false
    },
    {
      "typeLabel": "环保问题",
      "code": "E02-003",
      "title": "弃渣场截排水整改",
      "status": "待复查",
      "targetKpiCode": "E02",
      "actionEnabled": false
    }
  ],
  "permissions": {
    "canView": true,
    "canSupervise": false,
    "canHandle": false
  }
}
```

## 6. MySQL 表与种子脚本

### 6.1 空间图层与要素

| 表 | 说明 |
|---|---|
| `gis_layer` | GIS 图层清单 |
| `gis_feature` | GIS 空间要素，含几何、属性、状态 |

种子脚本：

```text
server/seed_gis_map_v0_8.py
```

### 6.2 业务摘要与关联关系

| 表 | 说明 |
|---|---|
| `gis_feature_business_summary` | 要素业务摘要，用于 FeatureCard |
| `gis_feature_business_relation` | 要素关联事项，用于 relations 与 business-links |

种子脚本：

```text
server/seed_gis_business_summary_v0_9.py
server/gis_business_summary_v0_9_seed.sql
```

推荐优先使用 Python 脚本：

```powershell
$env:PYTHONIOENCODING='utf-8'
& 'C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' server\seed_gis_business_summary_v0_9.py
```

如 Python 环境不可用，可使用 SQL 文件灌库：

```powershell
$env:MYSQL_PWD='Luoyi_App_2026!'
cmd.exe /c ""E:\Mysql\mysql-8.4.9-winx64\bin\mysql.exe" --host=127.0.0.1 --port=3307 --user=luoyi_app --default-character-set=utf8mb4 --database=luoyi_esg < "server\gis_business_summary_v0_9_seed.sql""
```

## 7. 启停与验证命令

### 7.1 启动后端

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\start_backend.ps1
```

### 7.2 停止后端

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\server\stop_backend.ps1
```

### 7.3 后端测试

```powershell
$env:PYTHONIOENCODING='utf-8'
& 'C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' server\gis_api_test.py
& 'C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' server\gis_business_summary_test.py
```

### 7.4 前端检查与构建

```powershell
npm.cmd run check
npm.cmd run build
```

已知说明：

- 构建时可能出现 Sass legacy API deprecation warning；
- 构建时可能出现 chunk size warning；
- 以上目前为非阻塞警告，不影响功能验收。

## 8. 标准验收路径

### 8.1 `/gis-preview` 验收

访问：

```text
http://localhost:5174/#/gis-preview
```

检查：

1. 能看到 1/2/3 标段路线；
2. 能看到弃渣点、水源保护区、生态保护区、边坡监测点；
3. 顶部按钮包含：全线、标段、环保点位、风险点、复位、配置后台；
4. 点击 2 标段；
5. FeatureCard 状态显示“正常”，不显示 `normal`；
6. 点击“加载关联事项”，能看到：
   - 安全风险 `S02-002`；
   - 环保问题 `E02-003`；
7. 点击“查看关联业务”，打开侧浮层；
8. 侧浮层显示：
   - 关联事项 2 项；
   - 待处理 2 项；
   - 高风险 1 项；
   - 安全风险 `S02-002`；
   - 环保问题 `E02-003`；
9. 点击“查看安全风险来源”或“查看环保问题来源”，只显示预留提示，不跳转；
10. 配置后台仍可打开；
11. 控制台无未捕获异常。

### 8.2 首页真实 GIS 灰度验收

临时修改：

```ts
useRealGisOnDashboard: true
```

访问：

```text
http://localhost:5174/#/
```

检查：

1. 首页 GIS 区域显示真实 Cesium GIS；
2. 首页不显示“配置后台”；
3. 点击 2 标段；
4. FeatureCard 显示：
   - 施工标段概览；
   - 建设进度 58%；
   - 环保问题 3项；
   - 风险点 1处；
   - 计划完工 2027年10月；
   - 关联事项 2 项；
   - 待处理 2 项；
   - 高风险 1 项；
   - 安全风险 1；
   - 环保问题 1；
5. 点击“查看关联业务”；
6. 侧浮层在 GIS 面板内部打开；
7. 侧浮层显示“领导层仅查看关联业务线索，不在地图侧办理事项。”；
8. 不出现“办理 / 处置 / 发起督办”；
9. 不遮挡右侧专题模块；
10. 不遮挡底部建设阶段时间轴；
11. 页面无异常滚动条。

验收后恢复：

```ts
useRealGisOnDashboard: false
```

### 8.3 SVG 回退验收

访问：

```text
http://localhost:5174/#/
```

检查：

1. 首页恢复原 SVG 地图；
2. 不加载 Cesium canvas；
3. 不显示“配置后台”；
4. KPI、右侧专题、底部时间轴正常；
5. 页面无异常滚动条。

## 9. 已完成边界

已完成：

- GIS 模块隔离接入；
- Cesium 静态资源复制；
- `/gis-preview` 路由；
- API 模式图层加载；
- 首页灰度嵌入；
- 首页默认 SVG 回退；
- Cesium 懒加载与手动分包；
- API 模式自动定位；
- API 模式 objectType 筛选；
- 首页隐藏配置后台；
- 首页 dashboard/preview 双展示模式；
- FeatureCard 中文状态；
- 业务摘要 `businessSummary`；
- 关联事项 `relations`；
- 关联业务线索 `business-links`；
- 仅查看、不办理、不督办的权限口径。

## 10. 未完成边界

暂未完成：

- 默认启用真实 GIS；
- 3D Tiles 模型 `data/18` 接入；
- 点击关联业务后真实跳转 E02/S02 弹窗；
- 地图侧发起督办；
- 地图侧办理、处置、修改业务数据；
- 与真实施工进度系统、环保巡查系统、安全监测系统实时同步；
- 生产级地图权限控制；
- 生产级地图资源后台。

说明：

当前 GIS 是“可灰度演示、可业务解释、可关联线索”的原型级集成，不应被描述为已完成生产级 GIS 平台。

## 11. 演示话术建议

建议表述：

> 首页默认保持稳定 SVG 地图。真实 GIS 已完成灰度接入，可在配置开关打开后展示路线、标段、环保敏感区、弃渣点和边坡监测点。点击空间要素后，领导层可以看到该要素的业务摘要、关联环保问题和安全风险线索，但不在地图侧办理或督办，避免把领导驾驶舱变成业务办理页面。

避免表述：

- “地图已经可以办理问题”；
- “地图已经接入所有实时系统”；
- “已经完成 3D 模型生产部署”；
- “领导可以在地图里直接督办”。

## 12. 后续建议顺序

推荐后续顺序：

1. 固化当前 GIS 灰度验收版本；
2. 由前端同事统一微调视觉样式；
3. 决定是否接入 3D Tiles；
4. 再设计 E02/S02 弹窗真实跳转协议；
5. 最后考虑真实业务系统同步，不要先做复杂跳转。

