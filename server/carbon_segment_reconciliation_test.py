from __future__ import annotations

from decimal import Decimal
import importlib.util
from pathlib import Path
import sys

from mysql_db import mysql_connect


D = Decimal
TOLERANCE = D("0.000001")
MIGRATION = Path(__file__).resolve().parent / "migrations" / "20260719_carbon_segment_and_cost_detail_v0_1.py"


def query_all(sql: str) -> list[dict]:
    with mysql_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return list(cursor.fetchall())


def query_one(sql: str) -> dict:
    return query_all(sql)[0]


def load_migration():
    spec = importlib.util.spec_from_file_location("carbon_segment_migration", MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load migration")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot() -> dict:
    return {
        "details": int(query_one("SELECT COUNT(*) n FROM carbon_emission_segment_detail WHERE is_demo=1")["n"]),
        "g04": int(query_one("SELECT COUNT(*) n FROM compliance_material_gap")["n"]),
        "monthly": int(query_one("SELECT COUNT(*) n FROM monthly_report_task_instance WHERE source_tag='V0.2_TEST'")["n"]),
    }


def main() -> int:
    migration = load_migration()
    before = snapshot()
    migration.main()
    once = snapshot()
    migration.main()
    twice = snapshot()
    assert once == twice
    assert before["g04"] == once["g04"] and before["monthly"] == once["monthly"]
    assert once["details"] == 108

    activities = query_all(
        "SELECT * FROM carbon_emission_activity WHERE id BETWEEN 720001 AND 720006 AND data_nature='demo' ORDER BY period_value"
    )
    details = query_all(
        "SELECT * FROM carbon_emission_segment_detail WHERE is_demo=1 ORDER BY accounting_month, id"
    )
    assert len(activities) == 6 and len(details) == 108
    assert sum(D(row["carbon_emission"]) for row in activities) == D("12856.00")
    assert sum(D(row["emission_amount"]) for row in details) == D("12856.00")

    monthly_values = [D(row["carbon_emission"]) for row in activities]
    assert len(set(monthly_values)) == 6
    assert all(value != value.to_integral_value() for value in monthly_values)
    for activity in activities:
        rows = [row for row in details if row["accounting_month"] == activity["period_value"]]
        assert sum(D(row["emission_amount"]) for row in rows) == D(activity["carbon_emission"])

    source_columns = {"DIESEL": "diesel_emission", "ELECTRICITY": "electricity_emission", "MATERIAL": "material_emission", "TRANSPORT": "other_emission"}
    source_rankings = set()
    for source_code, column in source_columns.items():
        detail_total = sum(D(row["emission_amount"]) for row in details if row["emission_source_code"] == source_code)
        project_total = sum(D(row[column]) for row in activities)
        assert detail_total == project_total
        segment_totals = tuple(
            sum(D(row["emission_amount"]) for row in details if row["emission_source_code"] == source_code and row["segment_code"] == segment)
            for segment in ("SEG-01", "SEG-02", "SEG-03")
        )
        assert len(set(segment_totals)) == 3
        source_rankings.add(tuple(sorted(range(3), key=lambda index: segment_totals[index], reverse=True)))
    assert len(source_rankings) >= 3

    material_project = {row["material_name"]: D(row["total"]) for row in query_all(
        "SELECT material_name, SUM(carbon_emission) total FROM carbon_material_usage WHERE id BETWEEN 720501 AND 720518 GROUP BY material_name"
    )}
    material_codes = {"水泥": "CEMENT", "钢材": "STEEL", "沥青": "ASPHALT"}
    for name, code in material_codes.items():
        segment_total = sum(D(row["emission_amount"]) for row in details if row["material_type_code"] == code)
        assert segment_total == material_project[name]
    assert sum(material_project.values()) == sum(D(row["material_emission"]) for row in activities) == D("2485.73")

    for row in details:
        activity = D(row["activity_amount"])
        factor = D(row["emission_factor_value"])
        calculated = activity * factor
        if str(row["factor_unit"]).startswith("kgCO₂e/"):
            calculated /= D("1000")
        assert abs(calculated - D(row["emission_amount"])) <= TOLERANCE

    reductions = query_all("SELECT * FROM carbon_reduction_accounting WHERE is_demo=1 ORDER BY accounting_month")
    assert sum(D(row["accounted_reduction"]) for row in reductions) == D("1445.00")
    assert len({D(row["accounted_reduction"]) for row in reductions}) == 6
    assert all(D(row["baseline_emission"]) - D(row["actual_emission"]) == D(row["accounted_reduction"]) for row in reductions)

    measures = query_all("SELECT * FROM carbon_reduction_measure WHERE is_demo=1 ORDER BY measure_code")
    assert sum(D(row["estimated_reduction"]) for row in measures) == D("950.00")
    investment = sum(D(row["investment_cost"]) for row in measures)
    operating = sum(D(row["operating_saving"]) for row in measures)
    avoided = sum(D(row["avoided_cost"]) for row in measures)
    net = sum(D(row["net_cost_impact"]) for row in measures)
    assert (investment, operating, avoided, net) == (D("318.60"), D("84.75"), D("118.35"), D("115.50"))
    assert net == investment - operating - avoided
    assert all(D(row["net_cost_impact"]) == D(row["investment_cost"]) - D(row["operating_saving"]) - D(row["avoided_cost"]) for row in measures)

    print("[PASS] 碳排项目/月度/来源/标段/材料/因子、减排与成本多级Decimal勾稽通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 碳排多级勾稽失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
