# CARBON 专题数据库校核与四页签重构完成报告

完成日期：2026-07-19

## 数据结论

- E04 冻结值保持 12,856 tCO₂e；四类来源保持 5,628 + 3,857 + 2,486 + 885 = 12,856；材料保持 1,600 + 750 + 136 = 2,486；月度累计末值保持 12,856。
- 1,445 tCO₂e 是同边界六个月核算差额：基准 14,301 − 实际 12,856。
- 2,840 tCO₂e 无库表、稳定 ID、月份或源码快照链，未入库，也未与 1,445 合并。
- 四项措施当前演示预计减排合计为 950 tCO₂e；与核算减排 1,445 tCO₂e 分开展示，不相加；已确认减排为空并显示待核验。
- 320/85/120 万元已按投入/运行节约/避免成本分列；同一演示口径净成本影响为 320 − 85 − 120 = 115 万元。专题原硬编码 0 已取消。3.2 万元未发现可追溯来源，未覆盖或合并。

## 数据库增量

新增表：

1. `carbon_emission_baseline`：6 条月度演示基准。
2. `carbon_reduction_accounting`：6 条月度核算记录，带稳定编码、基准外键和差额检查约束。
3. `carbon_reduction_measure`：4 条措施演示台账；预计/核算/确认减排分列，四类成本分列并带公式约束。
4. `carbon_measure_monthly_performance`：4 条 2026-07 演示成效记录，关联措施外键。
5. `carbon_accounting_evidence_link`：通用证据关联表；当前 0 条，不伪造证据。

迁移：`server/migrations/20260719_carbon_benefit_topic_v0_1.py`。连续执行两次均得到相同记录量与合计，未重复插入、未删除历史记录、未修改 E04 历史迁移。

## 后端与前端

- 新增聚合入口：`GET /api/carbon/benefit-overview`。
- 明确响应元数据：`sourceMode=mysql`、`isMock=false`、`dataNature=demo`、`verificationStatus=待业务核验`、`evidenceStatus=未关联`。
- 返回四页数据块：`overview`、`sources`、`benefit`、`measuresCosts`；同时保留旧专题字段供首页面板兼容。
- 新增独立组件 `src/components/modal/CarbonBenefitModal.vue`，未继续向通用弹窗堆叠 CARBON 分支。
- 页签为：碳排概览、排放来源、低碳增益、措施与成本；材料可展开；所有演示、核验和证据状态均显式展示。
- MySQL → 服务端快照 → 前端 Mock 的回退原则保留；新组件正常路径使用专用 MySQL 聚合接口，Mock 不覆盖成功的 MySQL 结果。

## 验证结果

- 新迁移连续执行两次：通过。
- `python -m compileall -q server`：通过。
- `python server/carbon_topic_mysql_test.py`：通过。
- `python server/dashboard_acceptance_test.py`：通过（UTF-8 控制台）。
- `python server/dashboard_panels_mysql_test.py`：通过。
- `python server/smoke_test.py`：通过。
- `npm run build`：通过，Vite 生产构建完成。
- `npm run check`：本次专题修改完成后曾通过；最终复跑时，工作区外部并发更新的禁止范围文件 `G04ComplianceModal.vue` 出现 4 个颜色字面量类型错误。本任务未修改 G04，故未越界代修；CARBON 专题组件自身已通过此前类型检查和生产构建。
- 浏览器 1920×1080：四页签均打开成功，弹窗/内容区无横纵溢出。
- 浏览器 1366×768：四页签逐页检查均无横纵溢出。
- 冻结 E04 浏览器回归：12,856、四来源、材料展开、演示及核验状态均保持。

## 截图

- `artifacts/carbon-topic-acceptance/carbon-01-overview-1920x1080.png`
- `artifacts/carbon-topic-acceptance/carbon-02-sources-1920x1080.png`
- `artifacts/carbon-topic-acceptance/carbon-03-benefit-1920x1080.png`
- `artifacts/carbon-topic-acceptance/carbon-04-measures-costs-1920x1080.png`
- `artifacts/carbon-topic-acceptance/carbon-overview-1366x768.png`

## 待业务确认

- 2,840 tCO₂e 的口径、月份、稳定 ID 和原始证据。
- 3.2 万元的定义、期间及统计范围。
- 320/85/120 万元是否确属同一正式统计范围；当前只作为演示测算。
- 四项措施的预计减排是否需要替换为正式台账，以及已确认减排的核验/证据标准。
