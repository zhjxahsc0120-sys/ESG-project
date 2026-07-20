from __future__ import annotations

"""碳排专题标段明细与成本演示数据迁移 V0.1。

只更新稳定 DEMO 编码记录；不触碰正式记录，不修改其他 KPI/专题数据。
"""

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql_db import mysql_connect  # noqa: E402


D = Decimal
Q8 = D("0.00000001")
TOTAL = D("12856.00")
NOTICE = "当前数据用于功能验证，不作为正式核算或财务确认依据。"
COST_NOTICE = "以上金额为项目初步测算值，尚未纳入正式财务确认。"

SEGMENTS = (
    ("SEG-01", "标段一", 1),
    ("SEG-02", "标段二", 2),
    ("SEG-03", "标段三", 3),
)

SOURCE_META = {
    "DIESEL": ("施工用油", "L", 740001, D("2.68"), "kgCO₂e/L", 1, (D("0.43"), D("0.31"), D("0.26"))),
    "ELECTRICITY": ("施工用电", "kWh", 740002, D("0.57"), "kgCO₂e/kWh", 2, (D("0.27"), D("0.45"), D("0.28"))),
    "MATERIAL": ("主要材料", "t", None, None, "分项核算", 3, None),
    "TRANSPORT": ("施工运输", "t·km", 740006, D("0.000885"), "tCO₂e/(t·km)", 4, (D("0.24"), D("0.29"), D("0.47"))),
}

MATERIAL_META = {
    "CEMENT": ("水泥", 740003, D("0.80"), "tCO₂e/t", 1, (D("0.34"), D("0.25"), D("0.41"))),
    "STEEL": ("钢材", 740004, D("0.75"), "tCO₂e/t", 2, (D("0.28"), D("0.38"), D("0.34"))),
    "ASPHALT": ("沥青", 740005, D("0.68"), "tCO₂e/t", 3, (D("0.22"), D("0.31"), D("0.47"))),
}

MONTH_SOURCE = {
    "2026-02": {"DIESEL": D("808.37"), "ELECTRICITY": D("558.24"), "MATERIAL": D("360.18"), "TRANSPORT": D("130.64")},
    "2026-03": {"DIESEL": D("975.62"), "ELECTRICITY": D("671.83"), "MATERIAL": D("426.19"), "TRANSPORT": D("163.14")},
    "2026-04": {"DIESEL": D("938.41"), "ELECTRICITY": D("644.27"), "MATERIAL": D("412.86"), "TRANSPORT": D("149.11")},
    "2026-05": {"DIESEL": D("1168.73"), "ELECTRICITY": D("801.44"), "MATERIAL": D("518.37"), "TRANSPORT": D("184.75")},
    "2026-06": {"DIESEL": D("1181.56"), "ELECTRICITY": D("806.18"), "MATERIAL": D("516.22"), "TRANSPORT": D("184.45")},
    "2026-07": {"DIESEL": D("555.15"), "ELECTRICITY": D("375.43"), "MATERIAL": D("251.91"), "TRANSPORT": D("72.95")},
}

MONTH_MATERIAL = {
    "2026-02": {"CEMENT": D("230.57"), "STEEL": D("108.12"), "ASPHALT": D("21.49")},
    "2026-03": {"CEMENT": D("272.91"), "STEEL": D("127.85"), "ASPHALT": D("25.43")},
    "2026-04": {"CEMENT": D("264.33"), "STEEL": D("123.86"), "ASPHALT": D("24.67")},
    "2026-05": {"CEMENT": D("331.65"), "STEEL": D("155.45"), "ASPHALT": D("31.27")},
    "2026-06": {"CEMENT": D("330.19"), "STEEL": D("154.97"), "ASPHALT": D("31.06")},
    "2026-07": {"CEMENT": D("161.62"), "STEEL": D("75.57"), "ASPHALT": D("14.72")},
}

REDUCTIONS = {
    "2026-02": D("208.73"), "2026-03": D("251.64"), "2026-04": D("239.18"),
    "2026-05": D("300.57"), "2026-06": D("302.26"), "2026-07": D("142.62"),
}

MEASURES = {
    "DEMO-CARBON-MEASURE-001": (D("318.47"), D("119.38"), D("29.46"), D("39.72")),
    "DEMO-CARBON-MEASURE-002": (D("276.83"), D("69.74"), D("19.87"), D("29.58")),
    "DEMO-CARBON-MEASURE-003": (D("154.26"), D("50.63"), D("15.22"), D("19.63")),
    "DEMO-CARBON-MEASURE-004": (D("200.44"), D("78.85"), D("20.20"), D("29.42")),
}


def allocate(total: Decimal, weights: tuple[Decimal, Decimal, Decimal]) -> tuple[Decimal, Decimal, Decimal]:
    first = (total * weights[0]).quantize(D("0.01"), rounding=ROUND_HALF_UP)
    second = (total * weights[1]).quantize(D("0.01"), rounding=ROUND_HALF_UP)
    return first, second, total - first - second


def activity_for(emission: Decimal, factor: Decimal, factor_unit: str) -> Decimal:
    multiplier = D("1000") if factor_unit.startswith("kgCO₂e/") else D("1")
    return (emission * multiplier / factor).quantize(Q8, rounding=ROUND_HALF_UP)


def ensure_schema(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_emission_segment_detail (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          detail_code VARCHAR(120) NOT NULL,
          accounting_month CHAR(7) NOT NULL,
          segment_code VARCHAR(30) NOT NULL,
          segment_name VARCHAR(100) NOT NULL,
          segment_sort_order INT NOT NULL,
          emission_source_code VARCHAR(30) NOT NULL,
          emission_source_name VARCHAR(100) NOT NULL,
          source_sort_order INT NOT NULL,
          material_type_code VARCHAR(30) NOT NULL DEFAULT '',
          material_type_name VARCHAR(100) NULL,
          material_sort_order INT NULL,
          activity_amount DECIMAL(24,8) NOT NULL,
          activity_unit VARCHAR(30) NOT NULL,
          emission_factor_id BIGINT NULL,
          emission_factor_value DECIMAL(24,12) NOT NULL,
          factor_unit VARCHAR(80) NOT NULL,
          emission_amount DECIMAL(18,8) NOT NULL,
          emission_unit VARCHAR(30) NOT NULL DEFAULT 'tCO₂e',
          boundary_code VARCHAR(80) NOT NULL,
          data_nature VARCHAR(30) NOT NULL,
          verification_status VARCHAR(40) NOT NULL,
          evidence_status VARCHAR(40) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_carbon_segment_detail_code(detail_code),
          UNIQUE KEY uk_carbon_segment_dimension
            (accounting_month, segment_code, emission_source_code, material_type_code, boundary_code),
          INDEX idx_carbon_segment_month(accounting_month, segment_sort_order, source_sort_order),
          INDEX idx_carbon_segment_source(emission_source_code, material_type_code),
          CONSTRAINT fk_carbon_segment_factor FOREIGN KEY (emission_factor_id)
            REFERENCES carbon_emission_factor(id)
        ) ENGINE=InnoDB COMMENT='碳排放月度-标段-来源-材料演示明细'
        """
    )


def upsert_segment_details(cur) -> None:
    sql = """
        INSERT INTO carbon_emission_segment_detail
          (detail_code, accounting_month, segment_code, segment_name, segment_sort_order,
           emission_source_code, emission_source_name, source_sort_order,
           material_type_code, material_type_name, material_sort_order,
           activity_amount, activity_unit, emission_factor_id, emission_factor_value,
           factor_unit, emission_amount, emission_unit, boundary_code, data_nature,
           verification_status, evidence_status, is_demo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'tCO₂e',
                'DEMO-CONSTRUCTION-E04','demo','待业务核验','未关联',1)
        ON DUPLICATE KEY UPDATE
          segment_name=VALUES(segment_name), segment_sort_order=VALUES(segment_sort_order),
          emission_source_name=VALUES(emission_source_name), source_sort_order=VALUES(source_sort_order),
          material_type_name=VALUES(material_type_name), material_sort_order=VALUES(material_sort_order),
          activity_amount=VALUES(activity_amount), activity_unit=VALUES(activity_unit),
          emission_factor_id=VALUES(emission_factor_id), emission_factor_value=VALUES(emission_factor_value),
          factor_unit=VALUES(factor_unit), emission_amount=VALUES(emission_amount),
          data_nature='demo', verification_status='待业务核验', evidence_status='未关联', is_demo=1
    """
    for month, sources in MONTH_SOURCE.items():
        month_key = month.replace("-", "")
        for source_code in ("DIESEL", "ELECTRICITY", "TRANSPORT"):
            source_name, unit, factor_id, factor, factor_unit, sort_order, weights = SOURCE_META[source_code]
            for (segment_code, segment_name, segment_sort), emission in zip(SEGMENTS, allocate(sources[source_code], weights)):
                activity = activity_for(emission, factor, factor_unit)
                cur.execute(sql, (
                    f"DEMO-CARBON-SEG-{month_key}-{source_code}-{segment_code.replace('-', '')}",
                    month, segment_code, segment_name, segment_sort, source_code, source_name, sort_order,
                    "", None, None, activity, unit, factor_id, factor, factor_unit, emission,
                ))
        for material_code, material_total in MONTH_MATERIAL[month].items():
            material_name, factor_id, factor, factor_unit, material_sort, weights = MATERIAL_META[material_code]
            for (segment_code, segment_name, segment_sort), emission in zip(SEGMENTS, allocate(material_total, weights)):
                activity = activity_for(emission, factor, factor_unit)
                cur.execute(sql, (
                    f"DEMO-CARBON-SEG-{month_key}-MATERIAL-{material_code}-{segment_code.replace('-', '')}",
                    month, segment_code, segment_name, segment_sort, "MATERIAL", "主要材料", 3,
                    material_code, material_name, material_sort, activity, "t", factor_id, factor, factor_unit, emission,
                ))


def update_project_demo(cur) -> None:
    activity_ids = {month: 720001 + index for index, month in enumerate(MONTH_SOURCE)}
    material_ids = {}
    next_material_id = 720501
    for month in MONTH_SOURCE:
        for material_code in ("CEMENT", "STEEL", "ASPHALT"):
            material_ids[(month, material_code)] = next_material_id
            next_material_id += 1

    for month, sources in MONTH_SOURCE.items():
        activities = {}
        for source_code in ("DIESEL", "ELECTRICITY", "TRANSPORT"):
            _name, _unit, _factor_id, factor, factor_unit, _sort, weights = SOURCE_META[source_code]
            activities[source_code] = sum(
                activity_for(value, factor, factor_unit) for value in allocate(sources[source_code], weights)
            )
        material_activity = D("0")
        for material_code, emission in MONTH_MATERIAL[month].items():
            _name, _factor_id, factor, factor_unit, _sort, weights = MATERIAL_META[material_code]
            material_activity += sum(activity_for(value, factor, factor_unit) for value in allocate(emission, weights))
        month_total = sum(sources.values())
        baseline = month_total + REDUCTIONS[month]
        cur.execute(
            """
            UPDATE carbon_emission_activity
            SET diesel_usage=%s, electricity_usage=%s, material_usage=%s, transport_usage=%s,
                carbon_emission=%s, baseline_emission=%s, diesel_emission=%s,
                electricity_emission=%s, material_emission=%s, other_emission=%s,
                data_nature='demo', verification_status='待业务核验', demo_note=%s
            WHERE id=%s AND period_value=%s AND data_nature='demo'
            """,
            (activities["DIESEL"], activities["ELECTRICITY"], material_activity, activities["TRANSPORT"],
             month_total, baseline, sources["DIESEL"], sources["ELECTRICITY"], sources["MATERIAL"],
             sources["TRANSPORT"], NOTICE, activity_ids[month], month),
        )
        for material_code, emission in MONTH_MATERIAL[month].items():
            material_name, factor_id, factor, factor_unit, _sort, weights = MATERIAL_META[material_code]
            activity = sum(activity_for(value, factor, factor_unit) for value in allocate(emission, weights))
            cur.execute(
                """
                UPDATE carbon_material_usage
                SET material_usage=%s, carbon_emission=%s, emission_factor_id=%s,
                    data_nature='demo', verification_status='待业务核验', demo_note=%s
                WHERE id=%s AND period_value=%s AND material_name=%s AND data_nature='demo'
                """,
                (activity, emission, factor_id, NOTICE, material_ids[(month, material_code)], month, material_name),
            )

        cur.execute(
            """UPDATE carbon_emission_baseline
               SET baseline_emission=%s, calculation_method='同边界月度功能验证基准方案'
               WHERE baseline_code=%s AND is_demo=1""",
            (baseline, f"DEMO-CARBON-BASE-{month}"),
        )
        cur.execute(
            """UPDATE carbon_reduction_accounting
               SET baseline_emission=%s, actual_emission=%s, accounted_reduction=%s
               WHERE accounting_code=%s AND is_demo=1""",
            (baseline, month_total, REDUCTIONS[month], f"DEMO-CARBON-RED-{month}"),
        )

    cur.execute(
        """UPDATE carbon_emission_factor SET factor_source=%s
           WHERE factor_code IN ('DEMO_DIESEL','DEMO_ELECTRICITY','DEMO_CEMENT','DEMO_STEEL','DEMO_ASPHALT','DEMO_TRANSPORT')
             AND data_nature='demo'""",
        (NOTICE,),
    )

    for code, (estimated, investment, operating, avoided) in MEASURES.items():
        net = investment - operating - avoided
        cur.execute(
            """
            UPDATE carbon_reduction_measure
            SET estimated_reduction=%s, investment_cost=%s, operating_saving=%s,
                avoided_cost=%s, net_cost_impact=%s,
                calculation_method='措施功能验证预计值；成本按投入减运行节约及材料运输处置支出减少计算'
            WHERE measure_code=%s AND is_demo=1 AND data_nature='demo'
            """,
            (estimated, investment, operating, avoided, net, code),
        )


def write_trace(cur) -> None:
    cur.execute(
        """
        INSERT INTO audit_log
          (id, module_name, entity_type, entity_id, action, action_desc, operator_name)
        VALUES
          (790019, 'CARBON', 'demo_data_contract', '20260719-carbon-segment-cost-v0.1',
           'UPSERT', %s, 'Codex migration')
        ON DUPLICATE KEY UPDATE action_desc=VALUES(action_desc), operator_name=VALUES(operator_name)
        """,
        ("幂等更新108条月度-标段-来源/材料明细及稳定编码演示汇总；" + NOTICE,),
    )


def verify(cur) -> dict:
    cur.execute("SELECT SUM(carbon_emission) total, COUNT(*) months FROM carbon_emission_activity WHERE id BETWEEN 720001 AND 720006 AND data_nature='demo'")
    activity = cur.fetchone()
    cur.execute("SELECT SUM(emission_amount) total, COUNT(*) details FROM carbon_emission_segment_detail WHERE is_demo=1 AND boundary_code='DEMO-CONSTRUCTION-E04'")
    segment = cur.fetchone()
    cur.execute("SELECT SUM(accounted_reduction) reduction FROM carbon_reduction_accounting WHERE is_demo=1")
    reduction = cur.fetchone()
    cur.execute("SELECT SUM(estimated_reduction) estimated, SUM(investment_cost) investment, SUM(operating_saving) operating, SUM(avoided_cost) avoided, SUM(net_cost_impact) net FROM carbon_reduction_measure WHERE is_demo=1")
    cost = cur.fetchone()
    actual = (D(activity["total"]), int(activity["months"]), D(segment["total"]), int(segment["details"]), D(reduction["reduction"]), D(cost["estimated"]), D(cost["investment"]), D(cost["operating"]), D(cost["avoided"]), D(cost["net"]))
    expected = (TOTAL, 6, TOTAL, 108, D("1445.00"), D("950.00"), D("318.60"), D("84.75"), D("118.35"), D("115.50"))
    if actual != expected:
        raise RuntimeError(f"碳排演示数据契约校验失败：{actual}")
    return {"total": str(actual[0]), "months": actual[1], "segmentDetails": actual[3], "reduction": str(actual[4]), "netCost": str(actual[9])}


def main() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            ensure_schema(cur)
            upsert_segment_details(cur)
            update_project_demo(cur)
            write_trace(cur)
            result = verify(cur)
    print(f"[PASS] 碳排标段与成本迁移完成（幂等）：{result}")


if __name__ == "__main__":
    main()
