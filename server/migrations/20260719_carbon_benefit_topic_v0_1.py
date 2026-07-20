from __future__ import annotations

"""CARBON 专题最小增量迁移 V0.1。

只新增专题基准、月度减排核算、措施、措施月效和证据关联表。
演示记录使用稳定编码幂等写入，不修改 E04 历史迁移及其三张既有表。
"""

from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql_db import mysql_connect  # noqa: E402


BOUNDARY = "DEMO-CONSTRUCTION-E04"
UNIT = "tCO₂e"
DATA_NATURE = "demo"
VERIFICATION = "待业务核验"
EVIDENCE = "未关联"
NOTICE = "系统演示测试数据，非正式核算依据。"

MONTHS = (
    ("2026-02", Decimal("2069"), Decimal("1860")),
    ("2026-03", Decimal("2492"), Decimal("2240")),
    ("2026-04", Decimal("2380"), Decimal("2140")),
    ("2026-05", Decimal("2981"), Decimal("2680")),
    ("2026-06", Decimal("2981"), Decimal("2680")),
    ("2026-07", Decimal("1398"), Decimal("1256")),
)

MEASURES = (
    ("DEMO-CARBON-MEASURE-001", "低碳材料应用", "材料替代", "路基填筑、路面结构", "物资设备部", "已实施", Decimal("320"), Decimal("120"), Decimal("30"), Decimal("40")),
    ("DEMO-CARBON-MEASURE-002", "弃渣与旧料资源化利用", "资源循环", "弃渣场、路基", "工程管理部", "已实施", Decimal("280"), Decimal("70"), Decimal("20"), Decimal("30")),
    ("DEMO-CARBON-MEASURE-003", "运输组织优化", "运输优化", "材料运输", "工程管理部", "实施中", Decimal("150"), Decimal("50"), Decimal("15"), Decimal("20")),
    ("DEMO-CARBON-MEASURE-004", "施工工艺节能应用", "能效提升", "隧道、桥梁", "工程管理部", "实施中", Decimal("200"), Decimal("80"), Decimal("20"), Decimal("30")),
)


def ensure_schema(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_emission_baseline (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          baseline_code VARCHAR(80) NOT NULL,
          baseline_name VARCHAR(160) NOT NULL,
          accounting_period CHAR(7) NOT NULL,
          boundary_code VARCHAR(80) NOT NULL,
          baseline_emission DECIMAL(18,4) NOT NULL,
          unit VARCHAR(30) NOT NULL,
          calculation_method VARCHAR(255) NOT NULL,
          factor_version VARCHAR(80) NOT NULL,
          data_nature VARCHAR(30) NOT NULL,
          verification_status VARCHAR(40) NOT NULL,
          evidence_status VARCHAR(40) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_carbon_baseline_code(baseline_code),
          UNIQUE KEY uk_carbon_baseline_period_boundary(accounting_period, boundary_code),
          INDEX idx_carbon_baseline_demo(is_demo, data_nature)
        ) ENGINE=InnoDB COMMENT='碳排放基准方案'
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_reduction_accounting (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          accounting_code VARCHAR(80) NOT NULL,
          accounting_month CHAR(7) NOT NULL,
          baseline_id BIGINT NOT NULL,
          boundary_code VARCHAR(80) NOT NULL,
          baseline_emission DECIMAL(18,4) NOT NULL,
          actual_emission DECIMAL(18,4) NOT NULL,
          accounted_reduction DECIMAL(18,4) NOT NULL,
          unit VARCHAR(30) NOT NULL,
          calculation_formula VARCHAR(255) NOT NULL,
          data_nature VARCHAR(30) NOT NULL,
          verification_status VARCHAR(40) NOT NULL,
          evidence_status VARCHAR(40) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_carbon_reduction_code(accounting_code),
          UNIQUE KEY uk_carbon_reduction_month_boundary(accounting_month, boundary_code),
          INDEX idx_carbon_reduction_baseline(baseline_id),
          CONSTRAINT fk_carbon_reduction_baseline FOREIGN KEY (baseline_id) REFERENCES carbon_emission_baseline(id),
          CONSTRAINT ck_carbon_reduction_formula CHECK (accounted_reduction = baseline_emission - actual_emission)
        ) ENGINE=InnoDB COMMENT='月度低碳增益核算'
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_reduction_measure (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          measure_code VARCHAR(80) NOT NULL,
          measure_name VARCHAR(160) NOT NULL,
          measure_category VARCHAR(80) NOT NULL,
          application_scope VARCHAR(255) NOT NULL,
          responsible_department VARCHAR(100) NULL,
          start_date DATE NULL,
          end_date DATE NULL,
          implementation_status VARCHAR(40) NOT NULL,
          estimated_reduction DECIMAL(18,4) NULL,
          accounted_reduction DECIMAL(18,4) NULL,
          verified_reduction DECIMAL(18,4) NULL,
          reduction_unit VARCHAR(30) NOT NULL,
          investment_cost DECIMAL(18,4) NOT NULL DEFAULT 0,
          operating_saving DECIMAL(18,4) NOT NULL DEFAULT 0,
          avoided_cost DECIMAL(18,4) NOT NULL DEFAULT 0,
          net_cost_impact DECIMAL(18,4) NOT NULL DEFAULT 0,
          currency_unit VARCHAR(30) NOT NULL,
          calculation_method VARCHAR(255) NOT NULL,
          data_nature VARCHAR(30) NOT NULL,
          verification_status VARCHAR(40) NOT NULL,
          evidence_status VARCHAR(40) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_carbon_measure_code(measure_code),
          INDEX idx_carbon_measure_status(implementation_status),
          INDEX idx_carbon_measure_demo(is_demo, data_nature),
          CONSTRAINT ck_carbon_measure_cost CHECK (net_cost_impact = investment_cost - operating_saving - avoided_cost)
        ) ENGINE=InnoDB COMMENT='低碳措施及成本台账'
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_measure_monthly_performance (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          performance_code VARCHAR(80) NOT NULL,
          measure_id BIGINT NOT NULL,
          accounting_month CHAR(7) NOT NULL,
          estimated_reduction DECIMAL(18,4) NULL,
          verified_reduction DECIMAL(18,4) NULL,
          investment_cost DECIMAL(18,4) NOT NULL DEFAULT 0,
          operating_saving DECIMAL(18,4) NOT NULL DEFAULT 0,
          avoided_cost DECIMAL(18,4) NOT NULL DEFAULT 0,
          verification_status VARCHAR(40) NOT NULL,
          evidence_status VARCHAR(40) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_carbon_performance_code(performance_code),
          UNIQUE KEY uk_carbon_performance_measure_month(measure_id, accounting_month),
          CONSTRAINT fk_carbon_performance_measure FOREIGN KEY (measure_id) REFERENCES carbon_reduction_measure(id)
        ) ENGINE=InnoDB COMMENT='低碳措施月度成效'
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_accounting_evidence_link (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          business_type VARCHAR(60) NOT NULL,
          business_id BIGINT NOT NULL,
          document_id BIGINT NOT NULL,
          evidence_role VARCHAR(60) NOT NULL,
          verification_status VARCHAR(40) NOT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY uk_carbon_evidence_business_document(business_type, business_id, document_id),
          INDEX idx_carbon_evidence_document(document_id)
        ) ENGINE=InnoDB COMMENT='碳核算与既有资料关联'
        """
    )


def seed_demo(cur) -> None:
    for month, baseline, actual in MONTHS:
        baseline_code = f"DEMO-CARBON-BASE-{month}"
        cur.execute(
            """
            INSERT INTO carbon_emission_baseline
              (baseline_code, baseline_name, accounting_period, boundary_code, baseline_emission,
               unit, calculation_method, factor_version, data_nature, verification_status,
               evidence_status, is_demo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            ON DUPLICATE KEY UPDATE
              baseline_name=VALUES(baseline_name), baseline_emission=VALUES(baseline_emission),
              unit=VALUES(unit), calculation_method=VALUES(calculation_method),
              factor_version=VALUES(factor_version), data_nature=VALUES(data_nature),
              verification_status=VALUES(verification_status), evidence_status=VALUES(evidence_status),
              is_demo=1
            """,
            (baseline_code, f"{month}施工阶段演示基准", month, BOUNDARY, baseline,
             UNIT, "同边界月度演示基准方案", "DEMO-EF-2026-v0.1", DATA_NATURE,
             VERIFICATION, EVIDENCE),
        )
        cur.execute("SELECT id FROM carbon_emission_baseline WHERE baseline_code=%s", (baseline_code,))
        baseline_id = cur.fetchone()["id"]
        cur.execute(
            """
            INSERT INTO carbon_reduction_accounting
              (accounting_code, accounting_month, baseline_id, boundary_code, baseline_emission,
               actual_emission, accounted_reduction, unit, calculation_formula, data_nature,
               verification_status, evidence_status, is_demo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            ON DUPLICATE KEY UPDATE
              baseline_id=VALUES(baseline_id), baseline_emission=VALUES(baseline_emission),
              actual_emission=VALUES(actual_emission), accounted_reduction=VALUES(accounted_reduction),
              unit=VALUES(unit), calculation_formula=VALUES(calculation_formula),
              data_nature=VALUES(data_nature), verification_status=VALUES(verification_status),
              evidence_status=VALUES(evidence_status), is_demo=1
            """,
            (f"DEMO-CARBON-RED-{month}", month, baseline_id, BOUNDARY, baseline, actual,
             baseline - actual, UNIT, "accounted_reduction = baseline_emission - actual_emission",
             DATA_NATURE, VERIFICATION, EVIDENCE),
        )

    for index, item in enumerate(MEASURES, start=1):
        code, name, category, scope, department, status, estimated, investment, saving, avoided = item
        cur.execute(
            """
            INSERT INTO carbon_reduction_measure
              (measure_code, measure_name, measure_category, application_scope,
               responsible_department, start_date, implementation_status,
               estimated_reduction, accounted_reduction, verified_reduction, reduction_unit,
               investment_cost, operating_saving, avoided_cost, net_cost_impact, currency_unit,
               calculation_method, data_nature, verification_status, evidence_status, is_demo)
            VALUES (%s,%s,%s,%s,%s,'2026-02-01',%s,%s,NULL,NULL,%s,%s,%s,%s,%s,'万元',%s,%s,%s,%s,1)
            ON DUPLICATE KEY UPDATE
              measure_name=VALUES(measure_name), measure_category=VALUES(measure_category),
              application_scope=VALUES(application_scope), responsible_department=VALUES(responsible_department),
              implementation_status=VALUES(implementation_status), estimated_reduction=VALUES(estimated_reduction),
              accounted_reduction=NULL, verified_reduction=NULL, investment_cost=VALUES(investment_cost),
              operating_saving=VALUES(operating_saving), avoided_cost=VALUES(avoided_cost),
              net_cost_impact=VALUES(net_cost_impact), data_nature=VALUES(data_nature),
              verification_status=VALUES(verification_status), evidence_status=VALUES(evidence_status), is_demo=1
            """,
            (code, name, category, scope, department, status, estimated, UNIT, investment, saving,
             avoided, investment - saving - avoided, "措施台账演示预计值；未作为核算或确认减排",
             DATA_NATURE, VERIFICATION, EVIDENCE),
        )
        cur.execute("SELECT id FROM carbon_reduction_measure WHERE measure_code=%s", (code,))
        measure_id = cur.fetchone()["id"]
        cur.execute(
            """
            INSERT INTO carbon_measure_monthly_performance
              (performance_code, measure_id, accounting_month, estimated_reduction,
               verified_reduction, investment_cost, operating_saving, avoided_cost,
               verification_status, evidence_status, is_demo)
            VALUES (%s,%s,'2026-07',%s,NULL,%s,%s,%s,%s,%s,1)
            ON DUPLICATE KEY UPDATE
              estimated_reduction=VALUES(estimated_reduction), verified_reduction=NULL,
              investment_cost=VALUES(investment_cost), operating_saving=VALUES(operating_saving),
              avoided_cost=VALUES(avoided_cost), verification_status=VALUES(verification_status),
              evidence_status=VALUES(evidence_status), is_demo=1
            """,
            (f"DEMO-CARBON-PERF-2026-07-{index:03d}", measure_id, estimated,
             investment, saving, avoided, VERIFICATION, EVIDENCE),
        )


def verify(cur) -> dict:
    cur.execute("SELECT COUNT(*) n, SUM(baseline_emission) baseline, SUM(actual_emission) actual, SUM(accounted_reduction) reduction FROM carbon_reduction_accounting WHERE is_demo=1")
    accounting = cur.fetchone()
    cur.execute("SELECT COUNT(*) n, SUM(estimated_reduction) estimated, SUM(investment_cost) investment, SUM(operating_saving) saving, SUM(avoided_cost) avoided, SUM(net_cost_impact) net FROM carbon_reduction_measure WHERE is_demo=1")
    measures = cur.fetchone()
    expected_accounting = (6, Decimal("14301"), Decimal("12856"), Decimal("1445"))
    actual_accounting = (accounting["n"], accounting["baseline"], accounting["actual"], accounting["reduction"])
    if actual_accounting != expected_accounting:
        raise RuntimeError(f"减排核算校验失败：{actual_accounting}")
    expected_measures = (4, Decimal("950"), Decimal("320"), Decimal("85"), Decimal("120"), Decimal("115"))
    actual_measures = (measures["n"], measures["estimated"], measures["investment"], measures["saving"], measures["avoided"], measures["net"])
    if actual_measures != expected_measures:
        raise RuntimeError(f"措施成本校验失败：{actual_measures}")
    return {"accounting": actual_accounting, "measures": actual_measures}


def main() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            ensure_schema(cur)
            seed_demo(cur)
            result = verify(cur)
    print(f"CARBON专题迁移完成（幂等）：{result}；{NOTICE}")


if __name__ == "__main__":
    main()
