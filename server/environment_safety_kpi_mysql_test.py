from __future__ import annotations

import json
import sys
from urllib.request import urlopen

from mysql_db import mysql_connect


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def summary_value(detail: dict, label: str) -> int:
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return int(item.get("value"))
    raise AssertionError(f"summary label missing: {label}")


def main() -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW COLUMNS FROM env_monitoring_record")
            columns = {row["Field"] for row in cur.fetchall()}
            assert_true("initial_detected_value" in columns, "E01 initial_detected_value column missing")
            assert_true("recheck_detected_value" in columns, "E01 recheck_detected_value column missing")
            cur.execute(
                """
                SELECT detected_value, initial_detected_value, recheck_detected_value, exceed_multiple
                FROM env_monitoring_record
                WHERE id = 410001
                """
            )
            noise_record = cur.fetchone()
            assert_true(noise_record is not None, "E01 confirmed noise record missing")
            assert_true(noise_record.get("detected_value") is None, "E01 legacy detected value must not retain the recheck value")
            assert_true(noise_record.get("initial_detected_value") is None, "E01 missing original noise value must stay NULL")
            assert_true(noise_record.get("recheck_detected_value") == "68.2 dB(A)", "E01 stored noise recheck value mismatch")
            assert_true(noise_record.get("exceed_multiple") is None, "E01 exceed multiple must stay NULL without original value")

    e01 = get_json("/api/dashboard/kpi/E01")
    assert_true("env_monitoring_record" in e01.get("dataSource", ""), "E01 should come from env_monitoring_record")
    assert_true(e01.get("fullName") == "环境监测超标项次", "E01 formal name mismatch")
    assert_true(summary_value(e01, "本月超标项次") == 2, "E01 monthly exceed mismatch")
    assert_true(summary_value(e01, "已完成复测") == 1, "E01 rechecked mismatch")
    assert_true(summary_value(e01, "待复测") == 1, "E01 pending recheck mismatch")
    assert_true(summary_value(e01, "复测仍超标") == 0, "E01 still exceeded mismatch")
    assert_true(all(item.get("unit") == "项次" for item in e01.get("summary", [])[:4]), "E01 summary unit mismatch")
    category = {item["name"]: item["value"] for item in e01.get("categoryData", [])}
    assert_true(category == {"扬尘": 1, "噪声": 1, "合计": 2}, f"E01 category mismatch: {category}")
    assert_true(len(e01.get("detailData", [])) == 2, "E01 detail row count mismatch")
    assert_true(all(item.get("id") is not None for item in e01.get("detailData", [])), "E01 detail id missing")
    assert_true(all(item.get("category") in {"噪声", "扬尘"} for item in e01.get("detailData", [])), "E01 detail category missing")
    assert_true([col.get("key") for col in e01.get("detailColumns", [])][3:5] == ["initialValue", "recheckValue"], "E01 initial/recheck columns mismatch")
    noise_row = next(item for item in e01.get("detailData", []) if item.get("factor") == "噪声/昼间等效声级")
    dust_row = next(item for item in e01.get("detailData", []) if item.get("factor") == "扬尘/PM10")
    assert_true(noise_row.get("id") == 410001 and noise_row.get("category") == "噪声", "E01 noise identity mismatch")
    assert_true(dust_row.get("id") == 410002 and dust_row.get("category") == "扬尘", "E01 dust identity mismatch")
    assert_true(noise_row.get("initialValue") == "—", "E01 missing original noise value must render as dash")
    assert_true(noise_row.get("recheckValue") == "68.2 dB(A)", "E01 noise recheck value mismatch")
    assert_true(noise_row.get("multiple") == "—", "E01 noise exceed multiple must be dash without original value")
    assert_true(noise_row.get("status") == "复测达标", "E01 completed recheck status mismatch")
    assert_true(dust_row.get("status") == "待复测", "E01 pending recheck status mismatch")

    e02 = get_json("/api/dashboard/kpi/E02")
    assert_true("env_issue_record" in e02.get("dataSource", ""), "E02 should come from env_issue_record")
    assert_true(summary_value(e02, "当前未闭环") == 5, "E02 open count mismatch")
    assert_true(summary_value(e02, "整改中") == 2, "E02 rectifying summary mismatch")
    assert_true(summary_value(e02, "待复查") == 2, "E02 pending review summary mismatch")
    assert_true(summary_value(e02, "待销项") == 1, "E02 pending close summary mismatch")
    assert_true(summary_value(e02, "已逾期") == 1, "E02 overdue summary mismatch")
    status_data = {item["name"]: item["value"] for item in e02.get("statusData", [])}
    assert_true(status_data == {"整改中": 2, "待复查": 2, "待销项": 1}, f"E02 statusData mismatch: {status_data}")
    assert_true("逾期" not in status_data, "E02 statusData must not include overdue as primary status")
    e02_rows = e02.get("detailData", [])
    assert_true(len(e02_rows) == 5, "E02 should expose five open issue rows")
    assert_true(all(item.get("id") and item.get("rawId") for item in e02_rows), "E02 rows must expose stable ids")
    assert_true(all(item.get("category") for item in e02_rows), "E02 rows must expose category")
    category_counts = {}
    for item in e02_rows:
        category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1
    assert_true(
        category_counts == {"废水处理": 1, "扬尘管控": 1, "噪声扰民": 1, "水土保持": 1, "生态保护": 1},
        f"E02 category mismatch: {category_counts}",
    )
    overdue_rows = [item for item in e02_rows if item.get("overdue") is True]
    assert_true(len(overdue_rows) == 1, "E02 should expose exactly one overdue row")
    assert_true(
        overdue_rows[0].get("mainStatus") == "整改中" and overdue_rows[0].get("deadlineStatus") == "已逾期",
        "E02 overdue row must keep rectifying main status and expose overdue deadline status",
    )
    assert_true(all(item.get("deadlineStatus") in {"已逾期", "正常"} for item in e02_rows), "E02 deadline status mismatch")
    assert_true(all(item.get("category") != "undefined" for item in e02_rows), "E02 category must not be undefined")
    e02_by_source = {item.get("sourceId"): item for item in e02.get("detailData", [])}
    assert_true("E02-003" in e02_by_source, "E02 detailData should expose sourceId E02-003 for GIS linking")
    assert_true(e02_by_source["E02-003"].get("sourceTable") == "env_issue_record", "E02 sourceTable mismatch")
    assert_true(e02_by_source["E02-003"].get("gisFeatureId") == "section-2-1", "E02-003 GIS feature mapping mismatch")
    assert_true("E02-005" in e02_by_source, "E02 detailData should expose sourceId E02-005 for GIS linking")

    s02 = get_json("/api/dashboard/kpi/S02")
    assert_true("safety_risk_point" in s02.get("dataSource", ""), "S02 should come from safety_risk_point")
    assert_true(summary_value(s02, "较大风险点") == 4, "S02 larger risk mismatch")
    assert_true(summary_value(s02, "重大风险点") == 2, "S02 major risk mismatch")
    assert_true(summary_value(s02, "本月新增") == 1, "S02 monthly new mismatch")
    assert_true(summary_value(s02, "本月销号") == 2, "S02 monthly cancelled mismatch")
    assert_true(summary_value(s02, "涉及工点") == 4, "S02 location count mismatch")
    statuses = {item.get("status") for item in s02.get("detailData", [])}
    assert_true(statuses <= {"持续管控", "正常管控"}, f"S02 status wording mismatch: {statuses}")
    s02_by_source = {item.get("sourceId"): item for item in s02.get("detailData", [])}
    assert_true("S02-002" in s02_by_source, "S02 detailData should expose sourceId S02-002 for GIS linking")
    assert_true(s02_by_source["S02-002"].get("sourceTable") == "safety_risk_point", "S02 sourceTable mismatch")
    assert_true(s02_by_source["S02-002"].get("gisFeatureId") == "section-2-1", "S02-002 GIS feature mapping mismatch")
    assert_true("S02-006" in s02_by_source, "S02 detailData should expose sourceId S02-006 for GIS linking")
    assert_true(s02_by_source["S02-006"].get("gisFeatureId") == "slope-2-1", "S02-006 GIS feature mapping mismatch")

    print("✅ E01/E02/S02 环境与安全 KPI MySQL 明细聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ E01/E02/S02 环境与安全 KPI MySQL 明细聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
