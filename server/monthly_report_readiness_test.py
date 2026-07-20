from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from monthly_report_readiness import get_monthly_report_readiness  # noqa: E402
from mysql_db import mysql_connect  # noqa: E402
from seed_monthly_report_readiness_v0_2 import REPORT_PERIOD, SOURCE_TAG, seed  # noqa: E402


EXPECTED_STATUS_COUNTS = {
    "待提交": 1,
    "待确认": 1,
    "待补正": 2,
    "校验通过": 18,
    "不适用（已确认）": 0,
}
EXPECTED_EXCEPTION_CODES = {"MR-E-010", "MR-G-011", "MR-G-007", "MR-G-004"}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def execute(sql: str, params: tuple = ()) -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            return cur.execute(sql, params)


def query_one(sql: str, params: tuple = ()) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def assert_baseline(payload: dict) -> None:
    assert_true(payload["metricName"] == "月报资料归集率", "指标名称不匹配")
    assert_true(payload["reportPeriod"] == REPORT_PERIOD, "所属期不匹配")
    assert_true(payload["denominator"] == 22, "分母应为22")
    assert_true(payload["numerator"] == 18, "分子应为18")
    assert_true(payload["exactProgress"] == 81.8, "精确归集率应为81.8")
    assert_true(payload["progress"] == 82, "展示归集率应为82")
    assert_true(payload["deadlineStart"] == "2026-08-02", "最早截止日应为2026-08-02")
    assert_true(payload["deadlineEnd"] == "2026-08-05", "最晚截止日应为2026-08-05")
    assert_true(payload["statusCounts"] == EXPECTED_STATUS_COUNTS, "状态数量不匹配")
    assert_true(len(payload["exceptionTasks"]) == 4, "异常任务应为4条")
    exception_codes = {item["taskCode"] for item in payload["exceptionTasks"]}
    assert_true(exception_codes == EXPECTED_EXCEPTION_CODES, "异常任务编码不匹配")


def test_dynamic_status_change(cycle_id: int) -> None:
    try:
        execute(
            """
            UPDATE monthly_report_task_instance
            SET monthly_status = '待补正', validation_passed_at = NULL
            WHERE report_cycle_id = %s AND task_code = 'MR-E-001' AND source_tag = %s
            """,
            (cycle_id, SOURCE_TAG),
        )
        changed = get_monthly_report_readiness(REPORT_PERIOD)
        assert_true(changed is not None, "状态变更后聚合为空")
        assert_true(changed["denominator"] == 22, "状态变更不应改变分母")
        assert_true(changed["numerator"] == 17, "状态变更后分子应为17")
        assert_true(changed["exactProgress"] == 77.3, "状态变更后精确归集率应为77.3")
        assert_true(changed["progress"] == 77, "状态变更后展示归集率应为77")
        assert_true(len(changed["exceptionTasks"]) == 5, "状态变更后异常任务应为5条")
    finally:
        execute(
            """
            UPDATE monthly_report_task_instance
            SET monthly_status = '校验通过', validation_passed_at = '2026-08-05 12:00:00'
            WHERE report_cycle_id = %s AND task_code = 'MR-E-001' AND source_tag = %s
            """,
            (cycle_id, SOURCE_TAG),
        )


def test_file_requirements_do_not_expand_denominator(cycle_id: int) -> None:
    linked = query_one(
        """
        SELECT upload_task_id
        FROM monthly_report_task_instance
        WHERE report_cycle_id = %s AND task_code = 'MR-E-005'
        """,
        (cycle_id,),
    )
    assert_true(linked is not None and linked["upload_task_id"] == "t1", "水保任务未关联上传任务t1")
    requirement_count = query_one(
        "SELECT COUNT(*) AS count FROM upload_task_requirement WHERE task_id = %s",
        (linked["upload_task_id"],),
    )
    assert_true(int(requirement_count["count"]) > 1, "测试任务包应关联多个资料要求")
    payload = get_monthly_report_readiness(REPORT_PERIOD)
    assert_true(payload is not None and payload["denominator"] == 22, "多个文件要求不得扩张分母")


def test_untriggered_conditional_is_excluded(cycle_id: int) -> None:
    try:
        execute(
            """
            INSERT INTO monthly_report_task_instance
            (id, report_cycle_id, task_code, task_name, group_code, task_mechanism,
             scope_type, scope_key, monthly_status, triggered_flag, confirmation_required,
             include_in_denominator, responsible_unit, deadline, dedup_key, source_tag)
            VALUES
            (829901, %s, 'TEST-COND-OFF', '未触发条件任务', 'E', 'CONDITIONAL',
             'ITEM', 'TEST-COND-OFF', '待提交', 0, 0, 0, '测试单位', '2026-08-05',
             'READINESS-TEST:COND-OFF', 'READINESS_TEST')
            ON DUPLICATE KEY UPDATE triggered_flag = 0, include_in_denominator = 0
            """,
            (cycle_id,),
        )
        payload = get_monthly_report_readiness(REPORT_PERIOD)
        assert_true(payload is not None and payload["denominator"] == 22, "未触发条件任务不得进入分母")
        assert_true(payload["statusCounts"] == EXPECTED_STATUS_COUNTS, "未触发任务不得污染状态数量")
    finally:
        execute("DELETE FROM monthly_report_task_instance WHERE id = 829901")


def test_confirmed_not_applicable_is_excluded(cycle_id: int) -> None:
    try:
        execute(
            """
            INSERT INTO monthly_report_task_instance
            (id, report_cycle_id, task_code, task_name, group_code, task_mechanism,
             scope_type, scope_key, monthly_status, triggered_flag, confirmation_required,
             include_in_denominator, responsible_unit, deadline, dedup_key,
             not_applicable_reason, not_applicable_confirmed_by, not_applicable_confirmed_at,
             source_tag)
            VALUES
            (829902, %s, 'TEST-NA', '已确认不适用任务', 'G', 'CONDITIONAL',
             'ITEM', 'TEST-NA', '不适用（已确认）', 1, 0, 1, '测试单位', '2026-08-05',
             'READINESS-TEST:NA', '本期无对应事项', '测试审核人', '2026-08-05 12:00:00',
             'READINESS_TEST')
            ON DUPLICATE KEY UPDATE monthly_status = '不适用（已确认）', include_in_denominator = 1
            """,
            (cycle_id,),
        )
        payload = get_monthly_report_readiness(REPORT_PERIOD)
        assert_true(payload is not None, "不适用测试聚合为空")
        assert_true(payload["denominator"] == 22, "已确认不适用不得进入分母")
        assert_true(payload["numerator"] == 18, "已确认不适用不得进入分子")
        assert_true(payload["statusCounts"]["不适用（已确认）"] == 1, "不适用状态数量应可追踪")
        assert_true(len(payload["exceptionTasks"]) == 4, "已确认不适用不得进入异常任务")
    finally:
        execute("DELETE FROM monthly_report_task_instance WHERE id = 829902")


def main() -> int:
    seeded = seed()
    assert_true(seeded["total"] == 22, "种子任务数应为22")
    assert_true(
        seeded["mechanisms"]
        == {"MONTHLY_FIXED": 16, "CONDITIONAL": 4, "PERIODIC_REFERENCE": 2},
        "任务机制分布不匹配",
    )
    assert_true(seeded["denominator"] == 22, "种子分母应为22")

    cycle = query_one(
        "SELECT id FROM monthly_report_cycle WHERE report_period = %s ORDER BY id DESC LIMIT 1",
        (REPORT_PERIOD,),
    )
    assert_true(cycle is not None, "月报周期不存在")
    cycle_id = int(cycle["id"])

    baseline = get_monthly_report_readiness(REPORT_PERIOD)
    assert_true(baseline is not None, "基线聚合为空")
    assert_baseline(baseline)
    test_dynamic_status_change(cycle_id)
    assert_baseline(get_monthly_report_readiness(REPORT_PERIOD))
    test_file_requirements_do_not_expand_denominator(cycle_id)
    test_untriggered_conditional_is_excluded(cycle_id)
    test_confirmed_not_applicable_is_excluded(cycle_id)
    assert_baseline(get_monthly_report_readiness(REPORT_PERIOD))

    print("[PASS] 月报资料归集率V0.2：10项验收规则全部通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 月报资料归集率V0.2验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
