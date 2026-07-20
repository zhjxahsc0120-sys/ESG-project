from __future__ import annotations

import json
import sys
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def summary_value(detail: dict, label: str):
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return item.get("value")
    raise AssertionError(f"summary label missing: {label}")


def kpi_value(kpis: dict, key: str):
    for group in kpis.get("groups", []):
        for item in group.get("items", []):
            if item.get("key") == key:
                return item
    raise AssertionError(f"kpi missing: {key}")


def main() -> int:
    kpis = get_json("/api/dashboard/kpis")
    e03_card = kpi_value(kpis, "E03")
    e04_card = kpi_value(kpis, "E04")
    assert_true(e03_card.get("value") == 7, f"E03 card value mismatch: {e03_card}")
    assert_true(e04_card.get("value") == 12856, f"E04 card value mismatch: {e04_card}")

    e03 = get_json("/api/dashboard/kpi/E03")
    assert_true("water_protection_issue" in e03.get("dataSource", ""), "E03 should come from water_protection_issue")
    assert_true(summary_value(e03, "当前未闭环") == 7, "E03 open count mismatch")
    assert_true(summary_value(e03, "本月新增未闭环") == 3, "E03 monthly open-new mismatch")
    assert_true(summary_value(e03, "本月闭环") == 2, "E03 monthly closed mismatch")
    assert_true(summary_value(e03, "逾期未闭环") == 2, "E03 overdue mismatch")
    assert_true(summary_value(e03, "涉及标段") == 3, "E03 segment count mismatch")
    assert_true(len(e03.get("detailData", [])) == 7, "E03 detail row count mismatch")
    e03_rows = e03.get("detailData", [])
    assert_true(all(isinstance(row.get("id"), int) for row in e03_rows), "E03 stable database id missing")
    assert_true(all(row.get("category") for row in e03_rows), "E03 category missing")
    assert_true(all(row.get("segment") for row in e03_rows), "E03 segment missing")
    assert_true(all(row.get("department") for row in e03_rows), "E03 department missing")
    assert_true(sum(1 for row in e03_rows if row.get("overdue") is True) == 2, "E03 overdue count mismatch")
    overdue_rows = [row for row in e03_rows if row.get("overdue") is True]
    assert_true(all(row.get("mainStatus") == "未闭环" for row in overdue_rows), "E03 overdue main status must not be inferred")
    assert_true(all(row.get("deadlineStatus") == "已逾期" for row in overdue_rows), "E03 overdue deadline status mismatch")
    assert_true(all(row.get("statusStageKnown") is False for row in overdue_rows), "E03 overdue status stage should remain unknown")
    normal_rows = [row for row in e03_rows if row.get("overdue") is False]
    assert_true(all(row.get("deadlineStatus") == "正常" for row in normal_rows), "E03 normal deadline status mismatch")
    assert_true(all(row.get("statusStageKnown") is True for row in normal_rows), "E03 normal status stage should be known")
    segment_totals = {}
    for row in e03_rows:
        segment_totals[row["segment"]] = segment_totals.get(row["segment"], 0) + 1
    assert_true(segment_totals == {"标段一": 3, "标段二": 2, "标段三": 2}, f"E03 segment totals mismatch: {segment_totals}")
    department_totals = {}
    for row in e03_rows:
        department_totals[row["department"]] = department_totals.get(row["department"], 0) + 1
    assert_true(department_totals == {"安全环保部": 3, "工程管理部": 4}, f"E03 department totals mismatch: {department_totals}")

    e04 = get_json("/api/dashboard/kpi/E04")
    assert_true("carbon_emission_activity" in e04.get("dataSource", ""), "E04 should come from carbon_emission_activity")
    assert_true(summary_value(e04, "累计碳排放") == 12856, "E04 total emission mismatch")
    assert_true(summary_value(e04, "本期排放") == 1255.44, "E04 monthly emission mismatch")
    assert_true(summary_value(e04, "核算期间") == "2026年2月—7月", "E04 accounting period mismatch")
    assert_true(summary_value(e04, "排放来源") == 4, "E04 source count mismatch")
    assert_true(summary_value(e04, "数据性质") == "演示数据", "E04 demo nature mismatch")
    assert_true(len(e04.get("detailData", [])) == 4, "E04 source detail row count mismatch")
    assert_true(all(row.get("activityValue", 0) > 0 for row in e04.get("detailData", [])), "E04 activity data missing")
    assert_true(all(row.get("dataNature") == "demo" for row in e04.get("detailData", [])), "E04 demo flag missing")
    assert_true(all(row.get("verificationStatus") == "待业务核验" for row in e04.get("detailData", [])), "E04 verification status mismatch")

    print("[PASS] E03/E04 水保与碳排 KPI MySQL 明细聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] E03/E04 水保与碳排 KPI MySQL 明细聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
