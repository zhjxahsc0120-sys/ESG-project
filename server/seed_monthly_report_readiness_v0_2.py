from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402


REPORT_PERIOD = "2026-07"
SOURCE_TAG = "V0.2_TEST"
MIGRATION_PATH = (
    Path(__file__).resolve().parent
    / "mysql_build_v0.3_monthly_readiness"
    / "01_monthly_report_task_instance.sql"
)


TASKS: list[tuple] = [
    (820001, None, "MR-E-001", "环境监测原始记录及监测报告", "E", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "校验通过", 1, 0, 1, "安全环保部/监测单位", "2026-08-03"),
    (820002, "t8", "MR-E-003", "环保巡查及环保设施运行台账", "E", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "校验通过", 1, 0, 1, "安全环保部/施工单位", "2026-08-03"),
    (820003, "t1", "MR-E-005", "水保监测月度资料包", "E", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "水保监测单位", "2026-08-05"),
    (820004, None, "MR-E-007", "施工能源及主要材料消耗活动数据", "E", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "校验通过", 1, 0, 1, "施工单位/工程管理部", "2026-08-04"),
    (820005, None, "MR-S-001", "安全事故台账及连续安全生产确认资料", "S", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "安全环保部", "2026-08-02"),
    (820006, "t2", "MR-S-002", "较大及以上安全风险管控月末快照", "S", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "校验通过", 1, 0, 1, "安全环保部/施工单位", "2026-08-02"),
    (820007, None, "MR-S-003", "月度安全检查记录", "S", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "校验通过", 1, 0, 1, "安全环保部/施工单位", "2026-08-03"),
    (820008, None, "MR-S-005", "劳务纠纷台账及处理情况", "S", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "工程/劳务管理部门", "2026-08-03"),
    (820009, None, "MR-S-006", "群众诉求台账及处理情况", "S", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "综合/诉求责任部门", "2026-08-03"),
    (820010, None, "MR-G-001", "报批报建事项进度台账", "G", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "工程管理部", "2026-08-03"),
    (820011, None, "MR-G-003", "许可状态及临期续办台账", "G", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "许可责任部门", "2026-08-03"),
    (820012, None, "MR-G-005", "检查及NCR整改事项台账", "G", "MONTHLY_FIXED", "PROJECT", "LUOYI", "校验通过", 1, 0, 1, "工程/安全环保部", "2026-08-03"),
    (820013, None, "MR-X-002", "施工月报", "X", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "校验通过", 1, 0, 1, "施工单位", "2026-08-05"),
    (820014, None, "MR-X-004", "监理月报", "X", "MONTHLY_FIXED", "SUPERVISION_UNIT", "ALL-SUPERVISORS", "校验通过", 1, 0, 1, "监理单位", "2026-08-05"),
    (820015, None, "MR-E-010", "月度工程计量资料", "E", "MONTHLY_FIXED", "SECTION", "ALL-SECTIONS", "待补正", 1, 0, 1, "工程/计量部门", "2026-08-04"),
    (820016, None, "MR-G-011", "资料目录台账及档案检查记录", "G", "MONTHLY_FIXED", "PROJECT", "LUOYI", "待确认", 1, 0, 1, "档案/工程管理部门", "2026-08-04"),
    (820017, None, "MR-E-002", "环境监测超标复测及处置资料", "E", "CONDITIONAL", "ITEM", "ENV-EXCEED-202607", "校验通过", 1, 0, 1, "问题责任单位", "2026-08-05"),
    (820018, None, "MR-E-004", "环保问题整改闭环资料", "E", "CONDITIONAL", "ITEM", "ENV-ISSUE-202607", "校验通过", 1, 0, 1, "问题责任单位", "2026-08-05"),
    (820019, "t4", "MR-G-006", "NCR及检查整改关闭资料", "G", "CONDITIONAL", "ITEM", "NCR-202607", "校验通过", 1, 0, 1, "问题责任单位", "2026-08-05"),
    (820020, None, "MR-G-007", "合规资料补齐材料", "G", "CONDITIONAL", "ITEM", "COMPLIANCE-GAP-202607", "待提交", 1, 0, 1, "缺口责任单位", "2026-08-05"),
    (820021, None, "MR-E-008", "碳排放因子依据及确认资料", "E", "PERIODIC_REFERENCE", "PROJECT", "LUOYI", "校验通过", 1, 1, 1, "技术管理部", "2026-08-04"),
    (820022, "t5", "MR-G-004", "许可证及许可变更文件有效性确认", "G", "PERIODIC_REFERENCE", "PROJECT", "LUOYI", "待补正", 1, 1, 1, "许可责任部门", "2026-08-04"),
]


def apply_migration() -> None:
    migration_sql = MIGRATION_PATH.read_text(encoding="utf-8").strip()
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(migration_sql)


def seed() -> dict:
    apply_migration()
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM monthly_report_cycle WHERE report_period = %s ORDER BY id DESC LIMIT 1",
                (REPORT_PERIOD,),
            )
            cycle = cur.fetchone()
            if cycle is None:
                raise RuntimeError(f"未找到月报周期：{REPORT_PERIOD}")
            cycle_id = cycle["id"]

            rows = []
            for task in TASKS:
                (
                    task_id,
                    upload_task_id,
                    task_code,
                    task_name,
                    group_code,
                    mechanism,
                    scope_type,
                    scope_key,
                    status,
                    triggered_flag,
                    confirmation_required,
                    include_in_denominator,
                    responsible_unit,
                    deadline,
                ) = task
                validation_passed_at = "2026-08-05 12:00:00" if status == "校验通过" else None
                dedup_key = f"{SOURCE_TAG}:{REPORT_PERIOD}:{task_code}:{scope_key}"
                rows.append(
                    (
                        task_id,
                        cycle_id,
                        upload_task_id,
                        task_code,
                        task_name,
                        group_code,
                        mechanism,
                        scope_type,
                        scope_key,
                        status,
                        triggered_flag,
                        confirmation_required,
                        include_in_denominator,
                        responsible_unit,
                        deadline,
                        dedup_key,
                        validation_passed_at,
                        SOURCE_TAG,
                    )
                )

            cur.executemany(
                """
                INSERT INTO monthly_report_task_instance
                (id, report_cycle_id, upload_task_id, task_code, task_name, group_code,
                 task_mechanism, scope_type, scope_key, monthly_status, triggered_flag,
                 confirmation_required, include_in_denominator, responsible_unit, deadline,
                 dedup_key, validation_passed_at, source_tag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  upload_task_id = VALUES(upload_task_id),
                  task_code = VALUES(task_code),
                  task_name = VALUES(task_name),
                  group_code = VALUES(group_code),
                  task_mechanism = VALUES(task_mechanism),
                  scope_type = VALUES(scope_type),
                  scope_key = VALUES(scope_key),
                  monthly_status = VALUES(monthly_status),
                  triggered_flag = VALUES(triggered_flag),
                  confirmation_required = VALUES(confirmation_required),
                  include_in_denominator = VALUES(include_in_denominator),
                  responsible_unit = VALUES(responsible_unit),
                  deadline = VALUES(deadline),
                  dedup_key = VALUES(dedup_key),
                  validation_passed_at = VALUES(validation_passed_at),
                  not_applicable_reason = NULL,
                  not_applicable_confirmed_by = NULL,
                  not_applicable_confirmed_at = NULL,
                  source_tag = VALUES(source_tag)
                """,
                rows,
            )

            cur.execute(
                """
                SELECT task_mechanism, monthly_status, include_in_denominator
                FROM monthly_report_task_instance
                WHERE report_cycle_id = %s AND source_tag = %s
                """,
                (cycle_id, SOURCE_TAG),
            )
            seeded = list(cur.fetchall())

    return {
        "reportPeriod": REPORT_PERIOD,
        "total": len(seeded),
        "mechanisms": dict(Counter(row["task_mechanism"] for row in seeded)),
        "statuses": dict(Counter(row["monthly_status"] for row in seeded)),
        "denominator": sum(int(row["include_in_denominator"]) for row in seeded),
    }


if __name__ == "__main__":
    result = seed()
    print(f"[PASS] V0.2月报资料任务测试数据已就绪：{result}")
