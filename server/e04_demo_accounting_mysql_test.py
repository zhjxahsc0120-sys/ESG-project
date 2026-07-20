from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_api import get_carbon_topic_detail, get_dashboard_kpis, get_dashboard_kpi_detail  # noqa: E402
from mysql_db import mysql_connect  # noqa: E402


TOLERANCE = Decimal("0.00001")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def close_enough(actual, expected) -> bool:
    return abs(decimal(actual) - decimal(expected)) <= TOLERANCE


def main() -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT SUM(diesel_usage) AS diesel_usage,
                       SUM(electricity_usage) AS electricity_usage,
                       SUM(transport_usage) AS transport_usage,
                       SUM(diesel_emission) AS diesel_emission,
                       SUM(electricity_emission) AS electricity_emission,
                       SUM(material_emission) AS material_emission,
                       SUM(other_emission) AS transport_emission,
                       SUM(carbon_emission) AS total_emission
                FROM carbon_emission_activity
                WHERE id BETWEEN 720001 AND 720006
                """
            )
            activity = cur.fetchone()
            assert_true(decimal(activity["diesel_usage"]) > 0, "施工用油活动数据仍为0")
            assert_true(decimal(activity["electricity_usage"]) > 0, "施工用电活动数据仍为0")
            assert_true(decimal(activity["transport_usage"]) > 0, "施工运输活动数据仍为0")
            assert_true(close_enough(decimal(activity["diesel_usage"]) * Decimal("2.68") / 1000, Decimal("5627.84")), "施工用油计算不成立")
            assert_true(close_enough(decimal(activity["electricity_usage"]) * Decimal("0.57") / 1000, Decimal("3857.39")), "施工用电计算不成立")
            assert_true(close_enough(decimal(activity["transport_usage"]) * Decimal("0.000885"), Decimal("885.04")), "施工运输计算不成立")
            assert_true(decimal(activity["total_emission"]) == Decimal("12856"), "E04总排放发生变化")

            cur.execute(
                """
                SELECT material_name, SUM(material_usage) AS activity_value,
                       SUM(carbon_emission) AS emission,
                       COUNT(DISTINCT carbon_activity_id) AS linked_months
                FROM carbon_material_usage
                WHERE id BETWEEN 720501 AND 720518 AND data_nature='demo'
                GROUP BY material_name
                """
            )
            materials = {row["material_name"]: row for row in cur.fetchall()}
            expected_materials = {
                "水泥": (Decimal("1591.27") / Decimal("0.80"), Decimal("1591.27")),
                "钢材": (Decimal("745.82") / Decimal("0.75"), Decimal("745.82")),
                "沥青": (Decimal("148.64") / Decimal("0.68"), Decimal("148.64")),
            }
            assert_true(set(materials) == set(expected_materials), f"材料分项不完整：{materials}")
            for name, (usage, emission) in expected_materials.items():
                row = materials[name]
                assert_true(close_enough(row["activity_value"], usage), f"{name}活动量不匹配")
                assert_true(close_enough(row["emission"], emission), f"{name}排放量不匹配")
                assert_true(row["linked_months"] == 6, f"{name}未追溯到6个月度活动记录")

            cur.execute(
                """
                SELECT factor_code, factor_value, factor_unit, factor_version, factor_source,
                       data_nature, verification_status, evidence_document_id
                FROM carbon_emission_factor
                WHERE factor_version='DEMO-EF-2026-v0.1'
                """
            )
            factors = cur.fetchall()
            assert_true(len(factors) == 6, "演示排放因子数量不匹配")
            assert_true(all(row["factor_value"] is not None and row["factor_unit"] for row in factors), "因子值或单位缺失")
            assert_true(all(row["factor_source"] == "当前数据用于功能验证，不作为正式核算或财务确认依据。" for row in factors), "因子来源未正确标注")
            assert_true(all(row["data_nature"] == "demo" for row in factors), "演示标志缺失")
            assert_true(all(row["verification_status"] == "待业务核验" for row in factors), "核验状态不得标记为已通过")
            assert_true(all(row["evidence_document_id"] is None for row in factors), "演示因子不得伪造证据资料")

            cur.execute(
                """
                SELECT period_value, SUM(carbon_emission) AS total
                FROM carbon_emission_activity
                WHERE id BETWEEN 720001 AND 720006
                GROUP BY period_value ORDER BY period_value
                """
            )
            monthly = [(row["period_value"], decimal(row["total"])) for row in cur.fetchall()]
            assert_true(monthly == [
                ("2026-02", Decimal("1857.43")), ("2026-03", Decimal("2236.78")),
                ("2026-04", Decimal("2144.65")), ("2026-05", Decimal("2673.29")),
                ("2026-06", Decimal("2688.41")), ("2026-07", Decimal("1255.44")),
            ], f"月度排放合计发生变化：{monthly}")

    detail = get_dashboard_kpi_detail("E04")
    assert_true(detail is not None, "E04详情未返回")
    sources = {row["sourceCode"]: row for row in detail["detailData"]}
    assert_true(set(sources) == {"diesel", "electricity", "material", "transport"}, "E04来源汇总不完整")
    assert_true(sum(decimal(row["emission"]) for row in sources.values()) == Decimal("12856"), "E04来源合计错误")
    assert_true(sum(decimal(row["share"]) for row in sources.values()) == Decimal("100.0"), "E04占比合计错误")
    assert_true(len(sources["material"]["materialDetails"]) == 3, "材料分项接口不可追溯")
    assert_true(all(row["verificationStatus"] == "待业务核验" for row in sources.values()), "接口核验状态错误")

    kpis = get_dashboard_kpis()
    e04_card = next(item for group in kpis["groups"] for item in group["items"] if item["key"] == "E04")
    topic = get_carbon_topic_detail()
    topic_total = next(item["value"] for item in topic["summary"] if item["label"] == "施工阶段累计碳足迹")
    assert_true(e04_card["value"] == 12856, "首页E04值不一致")
    assert_true(detail["summary"][0]["value"] == 12856, "E04详情总量不一致")
    assert_true(topic_total == 12856, "碳足迹专题总量不一致")
    assert_true(detail["monthlyData"][-1]["cumulativeEmission"] == 12856, "月度累计末值不一致")

    print("[PASS] E04演示活动数据、排放因子、材料追溯及三处总量一致性验证通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] E04演示核算数据验证失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
