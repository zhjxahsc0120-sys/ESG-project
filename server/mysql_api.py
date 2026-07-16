from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime, timedelta
import hashlib
import json
import re
from typing import Any

from mysql_db import mysql_connect


GROUP_META = {
    "E": {"key": "E", "title": "环境环保组", "theme": "green", "status": "总体可控"},
    "S": {"key": "S", "title": "社会责任组", "theme": "blue", "status": "总体可控"},
    "G": {"key": "G", "title": "治理合规组", "theme": "purple", "status": "总体可控"},
}


def value_for_json(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else value.isoformat()
    return value


def json_column(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        return json.loads(value.decode("utf-8"))
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def next_id(table: str, start: int) -> int:
    row = query_one(f"SELECT COALESCE(MAX(id), %s - 1) + 1 AS next_id FROM {table}", (start,))
    return int(row["next_id"])


def get_dashboard_kpis() -> dict:
    rows = query_all(
        """
        SELECT indicator_code, group_code, label, full_name, value, unit, display_order
        FROM indicator_result
        ORDER BY group_code, display_order
        """
    )
    groups: dict[str, dict] = {key: {**meta, "items": []} for key, meta in GROUP_META.items()}
    for row in rows:
        groups[row["group_code"]]["items"].append(
            {
                "key": row["indicator_code"],
                "label": row["label"],
                "fullName": row["full_name"],
                "value": value_for_json(row["value"]),
                "unit": row["unit"],
            }
        )
    e03_row = query_one("SELECT COUNT(*) AS c FROM water_protection_issue WHERE issue_status <> '已闭环'")
    e04_row = query_one("SELECT COALESCE(SUM(carbon_emission), 0) AS total FROM carbon_emission_activity")
    dynamic_values = {
        "E03": {"value": int(e03_row["c"]) if e03_row and e03_row["c"] else None, "unit": "项"},
        "E04": {"value": round(float(e04_row["total"])) if e04_row and float(e04_row["total"] or 0) > 0 else None, "unit": "tCO₂e"},
    }
    for group in groups.values():
        for item in group["items"]:
            dynamic = dynamic_values.get(item["key"])
            if dynamic and dynamic["value"] is not None:
                item["value"] = dynamic["value"]
                item["unit"] = dynamic["unit"]
    return {"groups": [groups["E"], groups["S"], groups["G"]]}


def get_dashboard_kpi_detail_snapshot(indicator_code: str) -> dict | None:
    row = query_one(
        """
        SELECT detail_json
        FROM dashboard_kpi_detail_snapshot
        WHERE indicator_code = %s
        """,
        (indicator_code,),
    )
    if row is None:
        return None
    detail = json_column(row["detail_json"])
    detail["isMock"] = False
    return detail


def with_snapshot_base(indicator_code: str) -> dict:
    return get_dashboard_kpi_detail_snapshot(indicator_code) or {
        "key": indicator_code,
        "fullName": indicator_code,
        "theme": "purple",
        "summary": [],
        "chartTitle": "趋势与构成",
        "detailTitle": "明细列表",
        "detailColumns": [],
        "detailData": [],
        "dataSource": "MySQL 业务明细表",
        "updateTime": "2026-07-13 10:30",
        "isMock": False,
    }


def get_g01_compliance_procedure_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM compliance_procedure
        WHERE status <> '已完成'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not rows:
        return None

    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM compliance_procedure
        WHERE status <> '已完成'
          AND created_at >= '2026-07-01'
          AND created_at < '2026-08-01'
        """
    )["c"]
    completed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM compliance_procedure
        WHERE completed_date >= '2026-07-01'
          AND completed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in rows if int(row.get("overdue") or 0) == 1)
    expected_this_month = query_one(
        """
        SELECT COUNT(*) AS c
        FROM compliance_procedure
        WHERE status IN ('待评审', '待批复')
          AND expected_complete_date >= '2026-07-01'
          AND expected_complete_date < '2026-08-01'
        """
    )["c"]

    detail = with_snapshot_base("G01")
    detail.update(
        {
            "summary": [
                {"label": "未完成事项", "value": len(rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月完成", "value": int(completed_count), "unit": "项"},
                {"label": "逾期未办", "value": overdue_count, "unit": "项"},
                {"label": "预计本月完成", "value": int(expected_this_month), "unit": "项"},
            ],
            "detailData": [
                {
                    "name": row["procedure_name"],
                    "type": row.get("procedure_type") or "行政许可",
                    "status": row["status"],
                    "deadline": value_for_json(row.get("deadline")),
                    "department": row.get("responsible_department") or "",
                    "progress": f"{row.get('progress_percent') or 0}%",
                }
                for row in rows
            ],
            "dataSource": "合规手续明细表 compliance_procedure",
            "updateTime": "2026-07-13 08:00",
            "isMock": False,
        }
    )
    return detail


def get_e01_env_monitoring_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM env_monitoring_record
        WHERE monitor_date >= '2026-07-01'
          AND monitor_date < '2026-08-01'
          AND exceed_count > 0
        ORDER BY monitor_date, id
        """
    )
    if not rows:
        return None
    current_count = sum(int(row.get("exceed_count") or 0) for row in rows)
    dust_count = sum(int(row.get("dust_exceed_count") or 0) for row in rows)
    noise_count = sum(int(row.get("noise_exceed_count") or 0) for row in rows)
    rechecked_count = sum(1 for row in rows if row.get("recheck_status") == "已复测")
    pending_count = sum(1 for row in rows if row.get("recheck_status") == "待复测")
    point_count = len({row.get("monitor_point") for row in rows if row.get("monitor_point")})

    detail = with_snapshot_base("E01")
    detail.update(
        {
            "summary": [
                {"label": "当前超标项", "value": current_count, "unit": "项"},
                {"label": "本月新增", "value": current_count, "unit": "项"},
                {"label": "已复测", "value": rechecked_count, "unit": "项"},
                {"label": "待复测", "value": pending_count, "unit": "项"},
                {"label": "涉及监测点", "value": point_count, "unit": "个"},
            ],
            "categoryData": [
                {"name": "扬尘", "value": dust_count},
                {"name": "噪声", "value": noise_count},
                {"name": "合计", "value": current_count},
            ],
            "detailData": [
                {
                    "point": row.get("monitor_point") or "",
                    "time": value_for_json(row.get("monitor_date")),
                    "factor": row.get("factor_name") or row.get("monitor_type") or "",
                    "value": row.get("detected_value") or "",
                    "limit": row.get("limit_value") or "",
                    "multiple": value_for_json(row.get("exceed_multiple")),
                    "status": row.get("recheck_status") or "",
                }
                for row in rows
            ],
            "dataSource": "环境监测明细表 env_monitoring_record",
            "updateTime": "2026-07-13 10:30",
            "isMock": False,
        }
    )
    return detail


def get_e02_env_issue_detail() -> dict | None:
    open_rows = query_all(
        """
        SELECT *
        FROM env_issue_record
        WHERE issue_status <> '已闭环'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not open_rows:
        return None
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM env_issue_record
        WHERE issue_status <> '已闭环'
          AND found_date >= '2026-07-01'
          AND found_date < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM env_issue_record
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in open_rows if int(row.get("overdue") or 0) == 1)
    avg_duration = round(sum(int(row.get("duration_days") or 0) for row in open_rows) / len(open_rows))

    detail = with_snapshot_base("E02")
    detail.update(
        {
            "summary": [
                {"label": "当前未闭环", "value": len(open_rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月闭环", "value": int(closed_count), "unit": "项"},
                {"label": "逾期未闭环", "value": overdue_count, "unit": "项"},
                {"label": "平均处置时长", "value": avg_duration, "unit": "天"},
            ],
            "statusData": [
                {"name": "整改中", "value": sum(1 for row in open_rows if row.get("issue_status") == "整改中")},
                {"name": "待复查", "value": sum(1 for row in open_rows if row.get("issue_status") == "待复查")},
                {"name": "待销项", "value": sum(1 for row in open_rows if row.get("issue_status") == "待销项")},
            ],
            "detailData": [
                {
                    "name": row.get("issue_name") or row.get("issue_type") or "",
                    "time": value_for_json(row.get("found_date")),
                    "level": row.get("issue_level") or "",
                    "department": row.get("responsible_department") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "status": "逾期未闭环" if int(row.get("overdue") or 0) == 1 else row.get("issue_status"),
                    "mainStatus": row.get("issue_status"),
                    "overdue": bool(row.get("overdue")),
                }
                for row in open_rows
            ],
            "dataSource": "环保问题明细表 env_issue_record",
            "updateTime": "2026-07-13 09:00",
            "isMock": False,
        }
    )
    return detail


def get_e03_water_protection_detail() -> dict | None:
    open_rows = query_all(
        """
        SELECT *
        FROM water_protection_issue
        WHERE issue_status <> '已闭环'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not open_rows:
        return None
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM water_protection_issue
        WHERE issue_status <> '已闭环'
          AND found_date >= '2026-07-01'
          AND found_date < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM water_protection_issue
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in open_rows if int(row.get("overdue") or 0) == 1 or row.get("issue_status") == "逾期未闭环")
    segment_count = len({row.get("segment_name") for row in open_rows if row.get("segment_name")})

    detail = with_snapshot_base("E03")
    detail.update(
        {
            "summary": [
                {"label": "当前未闭环", "value": len(open_rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月闭环", "value": int(closed_count), "unit": "项"},
                {"label": "逾期未闭环", "value": overdue_count, "unit": "项"},
                {"label": "涉及标段", "value": segment_count, "unit": "个"},
            ],
            "detailData": [
                {
                    "name": row.get("issue_name") or row.get("issue_type") or "水保问题",
                    "time": value_for_json(row.get("found_date")),
                    "segment": row.get("segment_name") or "",
                    "type": row.get("issue_type") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "status": row.get("issue_status") or "",
                }
                for row in open_rows
            ],
            "dataSource": "水保问题明细表 water_protection_issue",
            "updateTime": "2026-07-13 08:30",
            "isMock": False,
        }
    )
    return detail


def get_e04_carbon_emission_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM carbon_emission_activity
        ORDER BY period_value, id
        """
    )
    if not rows:
        return None

    total_emission = sum(float(row.get("carbon_emission") or 0) for row in rows)
    current_month = next((row for row in reversed(rows) if row.get("period_value") == "2026-07"), rows[-1])
    month_emission = float(current_month.get("carbon_emission") or 0)
    baseline_total = sum(float(row.get("baseline_emission") or 0) for row in rows)
    output_total = sum(float(row.get("output_value_wan") or 0) for row in rows)
    reduction_rate = round((baseline_total - total_emission) / baseline_total * 100, 1) if baseline_total else 0
    intensity = round(total_emission / output_total, 3) if output_total else 0

    source_values = [
        ("施工用油", sum(float(row.get("diesel_emission") or 0) for row in rows), "↓ 2.3%"),
        ("施工用电", sum(float(row.get("electricity_emission") or 0) for row in rows), "↑ 1.1%"),
        ("主要材料", sum(float(row.get("material_emission") or 0) for row in rows), "↓ 3.5%"),
        ("其他", sum(float(row.get("other_emission") or 0) for row in rows), "↑ 0.8%"),
    ]

    detail = with_snapshot_base("E04")
    detail.update(
        {
            "summary": [
                {"label": "累计碳排放", "value": round(total_emission), "unit": "tCO₂e"},
                {"label": "本月新增", "value": round(month_emission), "unit": "tCO₂e"},
                {"label": "较基准下降", "value": reduction_rate, "unit": "%"},
                {"label": "单位产值排放", "value": intensity, "unit": "tCO₂e/万元"},
            ],
            "detailData": [
                {
                    "source": name,
                    "value": f"{round(value):,} tCO₂e",
                    "proportion": f"{round(value / total_emission * 100, 1) if total_emission else 0}%",
                    "trend": trend,
                }
                for name, value, trend in source_values
            ],
            "dataSource": "碳排放活动明细表 carbon_emission_activity",
            "updateTime": "2026-07-13 00:00",
            "isMock": False,
        }
    )
    return detail


def get_carbon_topic_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM carbon_emission_activity
        ORDER BY period_value, id
        """
    )
    if not rows:
        return None

    base = get_dashboard_topic_snapshot("carbon")
    if base is None:
        base = {
            "key": "CARBON",
            "fullName": "碳足迹与低碳增益",
            "theme": "green",
            "isTopic": True,
            "topicData": {},
        }

    months = [row.get("period_value") for row in rows]
    actual_data = [round(float(row.get("carbon_emission") or 0)) for row in rows]
    baseline_data = [round(float(row.get("baseline_emission") or 0)) for row in rows]
    cumulative_data: list[int] = []
    running_total = 0
    for value in actual_data:
        running_total += value
        cumulative_data.append(running_total)

    total_emission = sum(actual_data)
    baseline_total = sum(baseline_data)
    reduction = round(baseline_total - total_emission)
    reduction_rate = round((baseline_total - total_emission) / baseline_total * 100, 1) if baseline_total else 0
    output_total = sum(float(row.get("output_value_wan") or 0) for row in rows)
    intensity = round(total_emission / output_total, 3) if output_total else 0
    month_emission = actual_data[-1] if actual_data else 0

    source_values = [
        ("施工用油", sum(float(row.get("diesel_emission") or 0) for row in rows), "#69e36f", "↓ 2.3%", "柴油消耗优化"),
        ("施工用电", sum(float(row.get("electricity_emission") or 0) for row in rows), "#2f9cff", "↑ 1.1%", "隧道掘进增加"),
        ("主要材料", sum(float(row.get("material_emission") or 0) for row in rows), "#a66cff", "↓ 3.5%", "低碳材料替代"),
        ("其他", sum(float(row.get("other_emission") or 0) for row in rows), "#ffb347", "↑ 0.8%", "运输增加"),
    ]
    source_summary = [
        {"label": name, "value": round(value), "unit": "tCO₂e"}
        for name, value, *_ in source_values
    ]
    source_items = [
        {"name": name, "value": round(value / total_emission * 100, 1) if total_emission else 0, "color": color}
        for name, value, color, *_ in source_values
    ]
    source_detail = [
        {
            "source": name,
            "value": f"{round(value):,} tCO₂e",
            "proportion": f"{round(value / total_emission * 100, 1) if total_emission else 0}%",
            "trend": trend,
            "note": note,
        }
        for name, value, _color, trend, note in source_values
    ]

    summary = [
        {"label": "施工阶段累计碳足迹", "value": total_emission, "unit": "tCO₂e"},
        {"label": "累计核算减排量", "value": reduction, "unit": "tCO₂e"},
        {"label": "较基准下降", "value": reduction_rate, "unit": "%"},
        {"label": "低碳措施成本影响", "value": 0, "unit": "测算口径"},
    ]

    topic_data = base.get("topicData") or {}
    cumulative = topic_data.get("cumulative") or {}
    cumulative.update(
        {
            "summary": [
                {"label": "施工阶段累计碳足迹", "value": total_emission, "unit": "tCO₂e"},
                {"label": "本月新增", "value": month_emission, "unit": "tCO₂e"},
                {"label": "较基准下降", "value": reduction_rate, "unit": "%"},
                {"label": "单位产值排放", "value": intensity, "unit": "tCO₂e/万元"},
            ],
            "months": months,
            "monthlyData": actual_data,
            "cumulativeData": cumulative_data,
        }
    )
    benefit = topic_data.get("benefit") or {}
    benefit.update(
        {
            "summary": [
                {"label": "累计核算减排量", "value": reduction, "unit": "tCO₂e"},
                {"label": "较基准下降", "value": reduction_rate, "unit": "%"},
                {"label": "预计全年减排", "value": round(reduction / max(len(months), 1) * 12), "unit": "tCO₂e"},
                {"label": "减排贡献率", "value": 12.5, "unit": "%"},
            ],
            "months": months,
            "actualData": actual_data,
            "baselineData": baseline_data,
            "totalReduction": reduction,
            "reductionRate": reduction_rate,
        }
    )
    source = topic_data.get("source") or {}
    source.update(
        {
            "items": source_items,
            "summary": source_summary,
            "detailData": source_detail,
        }
    )
    topic_data.update({"cumulative": cumulative, "benefit": benefit, "source": source})

    base.update(
        {
            "summary": summary,
            "topicData": topic_data,
            "detailData": source_detail,
            "dataSource": "碳排放活动明细表 carbon_emission_activity",
            "updateTime": "2026-07-13 00:00",
            "isMock": False,
        }
    )
    return base


def get_monthly_report_topic_detail() -> dict | None:
    cycle = query_one(
        """
        SELECT *
        FROM monthly_report_cycle
        ORDER BY report_period DESC, id DESC
        LIMIT 1
        """
    )
    if cycle is None:
        return None

    cycle_id = cycle["id"]
    groups = query_all(
        """
        SELECT *
        FROM monthly_report_group_progress
        WHERE cycle_id = %s
        ORDER BY FIELD(group_code, 'E', 'S', 'G'), id
        """,
        (cycle_id,),
    )
    chapters = query_all(
        """
        SELECT *
        FROM monthly_report_chapter
        WHERE cycle_id = %s
        ORDER BY chapter_index, id
        """,
        (cycle_id,),
    )
    gaps = query_all(
        """
        SELECT *
        FROM monthly_report_gap
        WHERE cycle_id = %s
        ORDER BY FIELD(group_name, 'E组', 'S组', 'G组'), deadline, id
        """,
        (cycle_id,),
    )
    chain = query_all(
        """
        SELECT *
        FROM monthly_report_status_chain
        WHERE cycle_id = %s
        ORDER BY display_order, id
        """,
        (cycle_id,),
    )

    base = get_dashboard_topic_snapshot("monthly-report")
    if base is None:
        base = {
            "key": "MONTHLY",
            "fullName": "月报准备与输出",
            "theme": "blue",
            "isTopic": True,
            "topicData": {},
        }

    pending_confirm = sum(1 for row in gaps if row.get("status") == "待确认") + sum(1 for row in chapters if row.get("status") == "待确认")
    summary = [
        {"label": "月报完成度", "value": int(round(float(cycle.get("completion_rate") or 0))), "unit": "%"},
        {"label": "待补资料", "value": len(gaps), "unit": "项"},
        {"label": "待确认", "value": pending_confirm, "unit": "项"},
        {"label": "预计完成", "value": cycle.get("expected_complete_date") or "", "unit": ""},
    ]

    group_items = [
        {
            "key": row.get("group_code"),
            "label": row.get("group_label"),
            "value": int(round(float(row.get("completion_rate") or 0))),
            "color": row.get("color") or "#2f9cff",
        }
        for row in groups
    ]
    chapter_items = [
        {
            "index": row.get("chapter_index"),
            "group": row.get("group_name") or "",
            "name": row.get("chapter_name") or "",
            "type": row.get("material_type") or "",
            "status": row.get("status") or "",
            "owner": row.get("owner") or "",
            "person": row.get("responsible_person") or "",
            "deadline": row.get("deadline") or "",
        }
        for row in chapters
    ]
    gap_items = [
        {
            "name": row.get("material_name") or "",
            "group": row.get("group_name") or "",
            "owner": row.get("owner") or "",
            "deadline": row.get("deadline") or "",
            "status": row.get("status") or "",
            "note": row.get("note") or "",
        }
        for row in gaps
    ]
    chain_items = [
        {
            "key": row.get("chain_key"),
            "label": row.get("label"),
            "status": row.get("status"),
        }
        for row in chain
    ]

    topic_data = base.get("topicData") or {}
    progress = topic_data.get("progress") or {}
    progress.update({"summary": summary, "groups": group_items})
    chapters_topic = topic_data.get("chapters") or {}
    chapters_topic.update({"list": chapter_items})
    topic_data.update(
        {
            "progress": progress,
            "chapters": chapters_topic,
            "statusChain": chain_items,
        }
    )

    base.update(
        {
            "summary": summary,
            "topicData": topic_data,
            "detailData": gap_items,
            "dataSource": "月报编制业务表 monthly_report_cycle / monthly_report_gap",
            "updateTime": value_for_json(cycle.get("update_time"))[:16] if cycle.get("update_time") else "2026-07-13 10:00",
            "completeness": f"{int(round(float(cycle.get('completion_rate') or 0)))}%",
            "isMock": False,
        }
    )
    return base


def get_s02_safety_risk_detail() -> dict | None:
    active_rows = query_all(
        """
        SELECT *
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
        ORDER BY risk_level = '重大' DESC, control_start_date, id
        """
    )
    if not active_rows:
        return None
    major_count = sum(1 for row in active_rows if row.get("risk_level") == "重大")
    larger_count = sum(1 for row in active_rows if row.get("risk_level") == "较大")
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
          AND control_start_date >= '2026-07-01'
          AND control_start_date < '2026-08-01'
        """
    )["c"]
    cancelled_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND cancelled_date >= '2026-07-01'
          AND cancelled_date < '2026-08-01'
        """
    )["c"]
    location_count = len({row.get("location") for row in active_rows if row.get("location")})

    detail = with_snapshot_base("S02")
    detail.update(
        {
            "summary": [
                {"label": "较大风险点", "value": larger_count, "unit": "项"},
                {"label": "重大风险点", "value": major_count, "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月销号", "value": int(cancelled_count), "unit": "项"},
                {"label": "涉及工点", "value": location_count, "unit": "个"},
            ],
            "detailData": [
                {
                    "name": row.get("risk_name") or "",
                    "level": row.get("risk_level") or "",
                    "location": row.get("location") or "",
                    "type": row.get("risk_type") or "",
                    "time": value_for_json(row.get("control_start_date")),
                    "status": row.get("control_status") or "持续管控",
                }
                for row in active_rows
            ],
            "dataSource": "安全风险点明细表 safety_risk_point",
            "updateTime": "2026-07-13 11:00",
            "isMock": False,
        }
    )
    return detail


def get_s03_labor_dispute_detail() -> dict | None:
    open_rows = query_all(
        """
        SELECT *
        FROM labor_dispute_record
        WHERE status <> '已办结'
        ORDER BY occurred_date, id
        """
    )
    if not open_rows:
        return None
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM labor_dispute_record
        WHERE status <> '已办结'
          AND occurred_date >= '2026-07-01'
          AND occurred_date < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM labor_dispute_record
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    people_count = sum(int(row.get("involved_people") or 0) for row in open_rows)
    amount_wan = sum(float(row.get("amount_wan") or 0) for row in open_rows)

    detail = with_snapshot_base("S03")
    detail.update(
        {
            "summary": [
                {"label": "未办结纠纷", "value": len(open_rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月办结", "value": int(closed_count), "unit": "项"},
                {"label": "涉及人数", "value": people_count, "unit": "人"},
                {"label": "涉及金额", "value": round(amount_wan), "unit": "万元"},
            ],
            "detailData": [
                {
                    "name": row.get("dispute_name") or row.get("dispute_type") or "",
                    "time": value_for_json(row.get("occurred_date")),
                    "people": str(row.get("involved_people") or 0),
                    "amount": f"{value_for_json(row.get('amount_wan'))}万元",
                    "department": row.get("responsible_department") or "",
                    "status": row.get("status") or "",
                }
                for row in open_rows
            ],
            "dataSource": "劳务纠纷明细表 labor_dispute_record",
            "updateTime": "2026-07-13 10:00",
            "isMock": False,
        }
    )
    return detail


def get_s04_appeal_detail() -> dict | None:
    open_rows = query_all(
        """
        SELECT *
        FROM appeal_record
        WHERE status <> '已办结'
        ORDER BY overdue DESC, accepted_date, id
        """
    )
    if not open_rows:
        return None
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM appeal_record
        WHERE status <> '已办结'
          AND accepted_date >= '2026-07-01'
          AND accepted_date < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM appeal_record
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in open_rows if int(row.get("overdue") or 0) == 1)
    avg_duration = round(sum(int(row.get("duration_days") or 0) for row in open_rows) / len(open_rows))

    detail = with_snapshot_base("S04")
    detail.update(
        {
            "summary": [
                {"label": "未办结诉求", "value": len(open_rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月办结", "value": int(closed_count), "unit": "项"},
                {"label": "逾期未办", "value": overdue_count, "unit": "项"},
                {"label": "平均办理时长", "value": avg_duration, "unit": "天"},
            ],
            "detailData": [
                {
                    "content": row.get("appeal_content") or row.get("appeal_type") or "",
                    "time": value_for_json(row.get("accepted_date")),
                    "source": row.get("source_channel") or "",
                    "location": row.get("location") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "status": row.get("status") or "",
                }
                for row in open_rows
            ],
            "dataSource": "群众诉求明细表 appeal_record",
            "updateTime": "2026-07-13 09:30",
            "isMock": False,
        }
    )
    return detail


def get_g02_permit_detail() -> dict | None:
    rows = query_all("SELECT * FROM permit_record ORDER BY expire_date, id")
    if not rows:
        return None
    current_date = date(2026, 7, 13)
    due_rows = [row for row in rows if row.get("status") == "临期"]
    overdue_rows = [row for row in rows if row.get("status") == "逾期"]
    due_within_30 = [
        row for row in rows
        if row.get("expire_date") and 0 < (row["expire_date"] - current_date).days <= 30
    ]
    dept_count = len({row.get("responsible_department") for row in rows if row.get("responsible_department")})
    positive_days = [(row["expire_date"] - current_date).days for row in due_rows if row.get("expire_date")]
    avg_days = round(sum(positive_days) / len(positive_days)) if positive_days else 0

    detail = with_snapshot_base("G02")
    detail.update(
        {
            "summary": [
                {"label": "临期许可", "value": len(due_rows), "unit": "项"},
                {"label": "逾期许可", "value": len(overdue_rows), "unit": "项"},
                {"label": "30日内到期", "value": len(due_within_30), "unit": "项"},
                {"label": "涉及部门", "value": dept_count, "unit": "个"},
                {"label": "平均剩余有效期", "value": avg_days, "unit": "天"},
            ],
            "detailData": [
                {
                    "name": row["permit_name"],
                    "number": row.get("permit_no") or "",
                    "type": row.get("permit_type") or "",
                    "deadline": value_for_json(row.get("expire_date")),
                    "department": row.get("responsible_department") or "",
                    "status": row.get("status") or "",
                }
                for row in rows
            ],
            "dataSource": "证照许可明细表 permit_record",
            "updateTime": "2026-07-13 00:00",
            "isMock": False,
        }
    )
    return detail


def get_g03_rectification_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM rectification_record
        WHERE status <> '已关闭'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not rows:
        return None

    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM rectification_record
        WHERE status <> '已关闭'
          AND created_at >= '2026-07-01'
          AND created_at < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM rectification_record
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in rows if int(row.get("overdue") or 0) == 1)
    check_count = len({row.get("check_batch") for row in rows if row.get("check_batch")})

    detail = with_snapshot_base("G03")
    detail.update(
        {
            "summary": [
                {"label": "未关闭事项", "value": len(rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月关闭", "value": int(closed_count), "unit": "项"},
                {"label": "逾期未关闭", "value": overdue_count, "unit": "项"},
                {"label": "涉及检查", "value": check_count, "unit": "次"},
            ],
            "detailData": [
                {
                    "name": row["item_name"],
                    "source": row.get("source_type") or "",
                    "level": row.get("issue_level") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "department": row.get("responsible_department") or "",
                    "status": row.get("status") or "",
                }
                for row in rows
            ],
            "dataSource": "整改事项明细表 rectification_record",
            "updateTime": "2026-07-13 10:30",
            "isMock": False,
        }
    )
    return detail


def get_g04_material_gap_detail() -> dict | None:
    rows = query_all("SELECT * FROM compliance_material_gap ORDER BY status = '逾期' DESC, deadline, id")
    if not rows:
        return None
    due_this_month = [
        row for row in rows
        if row.get("status") != "逾期" and row.get("deadline") and row["deadline"].year == 2026 and row["deadline"].month == 7
    ]
    overdue_count = sum(1 for row in rows if row.get("status") == "逾期")
    module_count = len({row.get("module_code") for row in rows if row.get("module_code")})

    detail = with_snapshot_base("G04")
    detail.update(
        {
            "summary": [
                {"label": "待补齐资料", "value": len(rows), "unit": "项"},
                {"label": "本月需提交", "value": len(due_this_month), "unit": "项"},
                {"label": "逾期未提交", "value": overdue_count, "unit": "项"},
                {"label": "涉及模块", "value": module_count, "unit": "个"},
                {"label": "资料完备率", "value": 85, "unit": "%"},
            ],
            "detailData": [
                {
                    "name": row["material_name"],
                    "module": row.get("module_code") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "owner": row.get("responsible_unit") or "",
                    "status": row.get("status") or "",
                    "action": row.get("action_text") or "上传",
                }
                for row in rows
            ],
            "dataSource": "合规资料缺口表 compliance_material_gap",
            "updateTime": "2026-07-13 09:00",
            "isMock": False,
        }
    )
    return detail


def get_dashboard_kpi_detail(indicator_code: str) -> dict | None:
    business_builders = {
        "E01": get_e01_env_monitoring_detail,
        "E02": get_e02_env_issue_detail,
        "E03": get_e03_water_protection_detail,
        "E04": get_e04_carbon_emission_detail,
        "S02": get_s02_safety_risk_detail,
        "S03": get_s03_labor_dispute_detail,
        "S04": get_s04_appeal_detail,
        "G01": get_g01_compliance_procedure_detail,
        "G02": get_g02_permit_detail,
        "G03": get_g03_rectification_detail,
        "G04": get_g04_material_gap_detail,
    }
    if indicator_code in business_builders:
        detail = business_builders[indicator_code]()
        if detail:
            return detail
    return get_dashboard_kpi_detail_snapshot(indicator_code)


def get_dashboard_topic_snapshot(topic_key: str) -> dict | None:
    row = query_one(
        """
        SELECT detail_json
        FROM dashboard_topic_snapshot
        WHERE topic_key = %s
        """,
        (topic_key,),
    )
    if row is None:
        return None
    detail = json_column(row["detail_json"])
    detail["isMock"] = False
    return detail


def get_dashboard_topic(topic_key: str) -> dict | None:
    normalized_key = "monthly-report" if topic_key == "monthly" else topic_key
    if normalized_key == "carbon":
        detail = get_carbon_topic_detail()
        if detail:
            return detail
    if normalized_key == "monthly-report":
        detail = get_monthly_report_topic_detail()
        if detail:
            return detail
    return get_dashboard_topic_snapshot(normalized_key)


def get_dashboard_panels_snapshot() -> dict | None:
    row = query_one(
        """
        SELECT panel_json
        FROM dashboard_panel_snapshot
        WHERE panel_key = 'home-panels'
        """
    )
    if row is None:
        return None
    return json_column(row["panel_json"])


def get_compliance_panel_data(base: dict) -> dict:
    closed_rect = int(query_one("SELECT COUNT(*) AS c FROM rectification_record WHERE closed_date IS NOT NULL")["c"])
    closed_env = int(query_one("SELECT COUNT(*) AS c FROM env_issue_record WHERE closed_date IS NOT NULL")["c"])
    closed_water = int(query_one("SELECT COUNT(*) AS c FROM water_protection_issue WHERE closed_date IS NOT NULL")["c"])
    cancelled_safety = int(query_one("SELECT COUNT(*) AS c FROM safety_risk_point WHERE cancelled_date IS NOT NULL")["c"])
    completed_proc = int(query_one("SELECT COUNT(*) AS c FROM compliance_procedure WHERE completed_date IS NOT NULL")["c"])
    procedure_total = int(query_one("SELECT COUNT(*) AS c FROM compliance_procedure")["c"])
    permit_total = int(query_one("SELECT COUNT(*) AS c FROM permit_record")["c"])
    active_risk = int(
        query_one(
            """
            SELECT COUNT(*) AS c
            FROM safety_risk_point
            WHERE risk_level IN ('重大', '较大') AND control_status <> '已销号'
            """
        )["c"]
    )
    carbon_point_count = int(query_one("SELECT COUNT(DISTINCT period_value) AS c FROM carbon_emission_activity")["c"])
    sensitive_count = len((base.get("gis") or {}).get("sensitiveAreas") or [])
    delayed_procedure = int(query_one("SELECT COUNT(*) AS c FROM compliance_procedure WHERE overdue = 1")["c"])
    overdue_permit = int(query_one("SELECT COUNT(*) AS c FROM permit_record WHERE status = '逾期'")["c"])

    solved_risk = closed_rect + closed_env + closed_water + cancelled_safety + completed_proc
    safeguarded_nodes = completed_proc + max(0, procedure_total - delayed_procedure)

    recent_permit = query_one(
        """
        SELECT permit_name, expire_date
        FROM permit_record
        WHERE status = '临期'
        ORDER BY expire_date
        LIMIT 1
        """
    )
    recent_rect = query_one(
        """
        SELECT item_name, responsible_department
        FROM rectification_record
        WHERE closed_date IS NOT NULL
        ORDER BY closed_date DESC
        LIMIT 1
        """
    )
    recent_proc = query_one(
        """
        SELECT procedure_name, impact_node
        FROM compliance_procedure
        WHERE completed_date IS NOT NULL
        ORDER BY completed_date DESC
        LIMIT 1
        """
    )

    safeguards = []
    if recent_permit:
        safeguards.append(f"{recent_permit['permit_name']}临期预警已纳入台账，保障相关施工连续推进")
    if recent_rect:
        safeguards.append(f"{recent_rect['item_name']}完成闭环，责任单位：{recent_rect.get('responsible_department') or '项目部'}")
    if recent_proc:
        safeguards.append(f"{recent_proc['procedure_name']}完成，支撑{recent_proc.get('impact_node') or '关键节点'}按计划实施")

    return {
        "metrics": [
            {"label": "合规点位", "value": procedure_total + permit_total, "unit": "个"},
            {"label": "碳排点位", "value": carbon_point_count, "unit": "个"},
            {"label": "敏感区", "value": sensitive_count, "unit": "处"},
            {"label": "风险点", "value": active_risk, "unit": "处"},
        ],
        "effectiveness": [
            {"label": "已化解重大风险", "value": solved_risk},
            {"label": "保障关键施工节点", "value": safeguarded_nodes},
            {"label": "因合规原因停工", "value": 0},
            {"label": "处罚及监管处分", "value": 0},
        ],
        "safeguards": safeguards or (base.get("compliance") or {}).get("safeguards") or [],
    }


def get_carbon_panel_data(base: dict) -> dict:
    topic = get_carbon_topic_detail()
    if not topic:
        return (base.get("carbon") or {})
    summary = topic.get("summary") or []
    source_detail = ((topic.get("topicData") or {}).get("source") or {}).get("summary") or []
    total = next((item for item in summary if item.get("label") == "施工阶段累计碳足迹"), {"value": 0})
    reduction = next((item for item in summary if item.get("label") == "累计核算减排量"), {"value": 0})
    rate = next((item for item in summary if item.get("label") == "较基准下降"), {"value": 0})
    existing = base.get("carbon") or {}
    return {
        "metrics": [
            {
                "label": "施工阶段累计碳足迹",
                "value": total.get("value"),
                "unit": "tCO₂e",
                "sub": f"较基准下降 {rate.get('value')}%",
            },
            {
                "label": "累计核算减排量",
                "value": reduction.get("value"),
                "unit": "tCO₂e",
                "sub": f"预计全年 {(((topic.get('topicData') or {}).get('benefit') or {}).get('summary') or [{}, {}, {'value': 0}])[2].get('value', 0)} tCO₂e",
            },
            {
                "label": "低碳措施成本影响",
                "value": 0,
                "unit": "测算口径",
                "sub": "非财务确认结论",
            },
        ],
        "sources": [{"name": item.get("label"), "value": item.get("value")} for item in source_detail[:3]],
        "reductions": existing.get("reductions") or existing.get("measures") or [],
        "measures": existing.get("measures") or existing.get("reductions") or [],
    }


def get_monthly_panel_data(base: dict) -> dict:
    topic = get_monthly_report_topic_detail()
    if not topic:
        return base.get("monthly") or {}
    summary = topic.get("summary") or []
    progress = next((item for item in summary if item.get("label") == "月报完成度"), {"value": 0})
    pending = next((item for item in summary if item.get("label") == "待补资料"), {"value": 0})
    confirm = next((item for item in summary if item.get("label") == "待确认"), {"value": 0})
    cycle = query_one("SELECT report_period FROM monthly_report_cycle ORDER BY report_period DESC, id DESC LIMIT 1")
    period = cycle.get("report_period") if cycle else "2026-07"
    return {
        "month": f"{period[:4]}年{int(period[5:7])}月" if period and len(period) >= 7 else period,
        "progress": progress.get("value"),
        "pendingCount": pending.get("value"),
        "confirmCount": confirm.get("value"),
        "materials": [
            {
                "name": item.get("name"),
                "owner": item.get("owner"),
                "deadline": item.get("deadline"),
            }
            for item in (topic.get("detailData") or [])
        ],
    }


def get_dashboard_panels() -> dict | None:
    base = get_dashboard_panels_snapshot()
    if base is None:
        return None
    base["compliance"] = get_compliance_panel_data(base)
    base["carbon"] = get_carbon_panel_data(base)
    base["monthly"] = get_monthly_panel_data(base)
    return base


def get_s01_detail() -> dict:
    row = query_one("SELECT * FROM safety_production_record ORDER BY update_time DESC LIMIT 1")
    if row is None:
        return {}
    return {
        "projectStartDate": value_for_json(row["project_start_date"]),
        "currentDate": value_for_json(row["current_date"]),
        "continuousDays": row["continuous_days"],
        "currentStage": row["current_stage"],
        "currentStageDetail": row["current_stage_detail"],
        "countingStatus": row["counting_status"],
        "updateTime": value_for_json(row["update_time"])[:16],
        "timeline": {
            "startLabel": "开工日期",
            "startDate": value_for_json(row["project_start_date"]),
            "message": "本轮连续周期内无事故中断",
            "endLabel": "当前",
            "endDate": value_for_json(row["current_date"]),
            "months": [
                "2025-07",
                "2025-08",
                "2025-09",
                "2025-10",
                "2025-11",
                "2025-12",
                "2026-01",
                "2026-02",
                "2026-03",
                "2026-04",
                "2026-05",
                "2026-06",
                "2026-07",
            ],
        },
        "constructionStages": [
            {"id": "preparation", "name": "施工准备", "status": "completed"},
            {"id": "main-construction", "name": "主体工程施工", "status": "current", "detail": row["current_stage_detail"]},
            {"id": "pavement", "name": "路面及附属工程", "status": "not_started"},
            {"id": "handover", "name": "交工验收", "status": "not_started"},
        ],
        "conclusion": f"项目开工以来，未发生导致连续安全生产记录中断的事故，当前已连续安全生产{row['continuous_days']}天。",
    }


def get_workspace_summary() -> dict:
    row = query_one("SELECT * FROM workspace_summary WHERE id = 1")
    if row is None:
        return {}
    return {
        "currentTodo": row["current_todo"],
        "pendingUpload": row["pending_upload"],
        "pendingCorrection": row["pending_correction"],
        "pendingSubmit": row["pending_submit"],
        "underReview": row["under_review"],
        "dueSoon": row["due_soon"],
        "completed": row["completed"],
    }


def normalize_cycle_type(cycle_type: str) -> str:
    mapping = {
        "MONTHLY": "月度",
        "MONTH": "月度",
        "QUARTERLY": "季度",
        "QUARTER": "季度",
        "ANNUAL": "年度",
        "YEARLY": "年度",
        "ONCE": "一次性",
        "ONE_TIME": "一次性",
    }
    return mapping.get((cycle_type or "").strip().upper(), cycle_type)


def get_tasks(
    module: str = "",
    status: str = "",
    keyword: str = "",
    cycle: str = "",
    cycle_type: str = "",
    deadline_start: str = "",
    deadline_end: str = "",
    assignee: str = "",
) -> dict:
    sql = "SELECT * FROM upload_task WHERE 1=1"
    params: list[Any] = []
    if module:
        sql += " AND module_code = %s"
        params.append(module)
    if status:
        sql += " AND status = %s"
        params.append(status)
    if keyword:
        sql += " AND name LIKE %s"
        params.append(f"%{keyword}%")
    if cycle:
        sql += " AND cycle LIKE %s"
        params.append(f"%{cycle}%")
    if cycle_type:
        sql += " AND cycle_type = %s"
        params.append(normalize_cycle_type(cycle_type))
    if deadline_start:
        sql += " AND deadline >= %s"
        params.append(deadline_start)
    if deadline_end:
        sql += " AND deadline <= %s"
        params.append(deadline_end)
    if assignee:
        sql += " AND (assignee_name = %s OR assignee_dept = %s)"
        params.extend([assignee, assignee])
    sql += " ORDER BY deadline ASC"
    rows = query_all(sql, tuple(params))
    return {"total": len(rows), "items": [task_row_to_item(row) for row in rows]}


def task_row_to_item(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "module": row["module_code"],
        "moduleName": row["module_name"],
        "cycle": row["cycle"],
        "cycleType": row["cycle_type"],
        "deadline": value_for_json(row["deadline"]),
        "deadlineDisplay": value_for_json(row["deadline"]),
        "progressCurrent": row["progress_current"],
        "progressTotal": row["progress_total"],
        "status": row["status"],
        "nextStep": row["next_step"],
        "assignee": row.get("assignee_name"),
        "assigneeDept": row.get("assignee_dept"),
        "priorityCode": row.get("priority_code"),
    }


def get_task_detail(task_id: str) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    req_rows = query_all("SELECT * FROM upload_task_requirement WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    candidate_rows = query_all("SELECT * FROM task_candidate_document WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    timeline_rows = query_all("SELECT * FROM task_review_timeline WHERE task_id = %s ORDER BY sequence_no", (task_id,))

    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "format": row["format_rule"],
            "status": row["status"],
            "templateAvailable": bool(row["template_available"]),
        }
        for row in req_rows
    ]
    completed = sum(1 for row in documents if row["status"] in ("已关联", "审核通过"))
    missing = sum(1 for row in documents if row["status"] == "缺失")
    abnormal = sum(1 for row in documents if row["status"] == "格式异常")

    return {
        "task": task_row_to_item(task),
        "tabs": ["资料要求", "已关联资料", "校验问题", "审核记录"],
        "documents": documents,
        "validation": {
            "completed": completed,
            "missing": missing,
            "abnormal": abnormal,
            "canSubmit": missing == 0 and abnormal == 0,
        },
        "candidateDocuments": [
            {
                "id": row["id"],
                "name": row["name"],
                "cycle": row["cycle"],
                "unit": row["unit_name"],
                "linkCount": row["link_count"],
                "matchRate": row["match_rate"],
            }
            for row in candidate_rows
        ],
        "aiRecommendation": {
            "fileName": "弃渣场巡查记录_2026-07.pdf",
            "matchRate": 96,
            "text": "该资料已用于其他流程，无需重复上传",
        },
        "aiTip": "还缺少“审核确认单”，建议下载模板后补充签章。",
        "reviewTimeline": [
            {"time": value_for_json(row["event_time"]), "action": row["action_text"]}
            for row in timeline_rows
        ],
    }


def _task_validation_from_documents(documents: list[dict]) -> dict:
    completed = sum(1 for row in documents if row["status"] in ("已关联", "审核通过"))
    missing = sum(1 for row in documents if row["status"] == "缺失")
    abnormal = sum(1 for row in documents if row["status"] == "格式异常")
    return {"completed": completed, "missing": missing, "abnormal": abnormal, "canSubmit": missing == 0 and abnormal == 0}


def _task_validation_issues(documents: list[dict]) -> list[dict]:
    issues = []
    for row in documents:
        if row["status"] == "缺失":
            issues.append(
                {
                    "id": f"missing-{row['id']}",
                    "documentRequirementId": row["id"],
                    "documentName": row["name"],
                    "issueType": "缺失",
                    "severity": "high" if row["required"] else "medium",
                    "message": f"{row['name']}尚未关联或上传，请补齐后再提交审核。",
                    "canSubmit": False,
                }
            )
        elif row["status"] == "格式异常":
            issues.append(
                {
                    "id": f"format-{row['id']}",
                    "documentRequirementId": row["id"],
                    "documentName": row["name"],
                    "issueType": "格式异常",
                    "severity": "medium",
                    "message": f"{row['name']}存在格式异常，请重新上传或从资料中心关联有效版本。",
                    "canSubmit": False,
                }
            )
    return issues


def find_matching_requirement_id(task_id: str, document_name: str, candidate_name: str = "", document_type: str = "") -> str | None:
    names = [candidate_name, document_name, document_type]
    stems = []
    for name in names:
        if not name:
            continue
        stem = name.rsplit(".", 1)[0]
        stems.append(stem)
        stems.append(stem.split("_", 1)[0])

    requirements = query_all("SELECT id, name FROM upload_task_requirement WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    for req in requirements:
        req_name = req["name"]
        for stem in stems:
            if stem and (req_name in stem or stem in req_name):
                return req["id"]
    unfinished = query_one(
        """
        SELECT id
        FROM upload_task_requirement
        WHERE task_id = %s AND status NOT IN ('已关联', '审核通过')
        ORDER BY required DESC, sequence_no
        LIMIT 1
        """,
        (task_id,),
    )
    if unfinished:
        return unfinished["id"]
    return None


def candidate_document_payload(task_id: str, row: dict) -> dict:
    document_id = resolve_document_id_for_link(task_id, row["id"])
    requirement_id = None
    if document_id is not None:
        document = query_one("SELECT document_name FROM document_record WHERE id = %s", (document_id,))
        requirement_id = find_matching_requirement_id(task_id, (document or {}).get("document_name", ""), row["name"], (document or {}).get("document_type", ""))
    return {
        "id": row["id"],
        "documentId": str(document_id) if document_id is not None else None,
        "requirementId": requirement_id,
        "name": row["name"],
        "cycle": row["cycle"],
        "unit": row["unit_name"],
        "linkCount": row["link_count"],
        "matchRate": row["match_rate"],
    }


def get_task_detail(task_id: str) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    req_rows = query_all("SELECT * FROM upload_task_requirement WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    candidate_rows = query_all("SELECT * FROM task_candidate_document WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    timeline_rows = query_all("SELECT * FROM task_review_timeline WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    linked_rows = query_all(
        """
        SELECT r.*, d.document_name, d.document_type, d.period_value, d.version_no,
               d.validity_status, d.source_name, d.uploaded_at
        FROM document_task_relation r
        JOIN document_record d ON d.id = r.document_id
        WHERE r.task_id = %s
        ORDER BY r.linked_at DESC, r.id DESC
        """,
        (task_id,),
    )
    review_rows = query_all("SELECT * FROM review_record WHERE task_id = %s ORDER BY submit_time DESC, id DESC", (task_id,))

    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "format": row["format_rule"],
            "status": row["status"],
            "templateAvailable": bool(row["template_available"]),
        }
        for row in req_rows
    ]
    validation = _task_validation_from_documents(documents)

    return {
        "task": task_row_to_item(task),
        "tabs": ["资料要求", "已关联资料", "校验问题", "审核记录"],
        "documents": documents,
        "linkedDocuments": [
            {
                "relationId": row["id"],
                "documentId": str(row["document_id"]),
                "documentName": row["document_name"],
                "documentType": row["document_type"],
                "period": row["period_value"],
                "version": row["version_no"],
                "validityStatus": row["validity_status"],
                "source": row["source_name"],
                "relationType": row["relation_type"],
                "relationStatus": row["relation_status"],
                "matchScore": value_for_json(row["match_score"]),
                "linkedAt": value_for_json(row["linked_at"]),
                "uploadedAt": value_for_json(row["uploaded_at"]),
            }
            for row in linked_rows
        ],
        "validation": validation,
        "validationIssues": _task_validation_issues(documents),
        "candidateDocuments": [candidate_document_payload(task_id, row) for row in candidate_rows],
        "aiRecommendation": {
            "fileName": "弃渣场巡查记录_2026-07.pdf",
            "matchRate": 96,
            "text": "该资料已用于其他流程，无需重复上传",
        },
        "aiTip": "若存在缺失或格式异常，请先从资料中心关联有效资料或上传新资料。",
        "reviewTimeline": [
            {"time": value_for_json(row["event_time"]), "action": row["action_text"]}
            for row in timeline_rows
        ],
        "reviewRecords": [
            {
                "id": row["id"],
                "taskId": row["task_id"],
                "taskName": row["task_name"],
                "submitTime": value_for_json(row["submit_time"]),
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in review_rows
        ],
    }


def recalculate_task_progress(task_id: str) -> dict:
    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "status": row["status"],
        }
        for row in query_all("SELECT * FROM upload_task_requirement WHERE task_id = %s", (task_id,))
    ]
    validation = _task_validation_from_documents(documents)
    execute(
        "UPDATE upload_task SET progress_current = %s, progress_total = %s WHERE id = %s",
        (validation["completed"], len(documents), task_id),
    )
    validation["total"] = len(documents)
    return validation


def mark_task_requirement_linked(
    task_id: str,
    document_name: str,
    candidate_name: str = "",
    requirement_id: str | None = None,
    document_type: str = "",
) -> dict:
    target_requirement_id = requirement_id or find_matching_requirement_id(task_id, document_name, candidate_name, document_type)
    updated_requirement = None
    if target_requirement_id:
        execute(
            "UPDATE upload_task_requirement SET status = '已关联' WHERE id = %s AND task_id = %s",
            (target_requirement_id, task_id),
        )
        updated_requirement = query_one(
            "SELECT id, name, status FROM upload_task_requirement WHERE id = %s AND task_id = %s",
            (target_requirement_id, task_id),
        )
    progress = recalculate_task_progress(task_id)
    return {
        "requirementId": target_requirement_id,
        "requirementName": (updated_requirement or {}).get("name"),
        "progress": progress,
    }


def append_task_timeline(task_id: str, action_text: str) -> None:
    row = query_one("SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_seq FROM task_review_timeline WHERE task_id = %s", (task_id,))
    timeline_id = f"rt-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    execute(
        """
        INSERT INTO task_review_timeline(id, task_id, event_time, action_text, sequence_no)
        VALUES (%s, %s, NOW(), %s, %s)
        """,
        (timeline_id, task_id, action_text, int(row["next_seq"] if row else 1)),
    )


def append_review_timeline(review_id: str, action_text: str, event_type: str, operator_name: str = "系统") -> None:
    row = query_one("SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_seq FROM review_timeline WHERE review_id = %s", (review_id,))
    execute(
        """
        INSERT INTO review_timeline(id, review_id, event_time, action_text, event_type, operator_name, sequence_no)
        VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """,
        (
            next_id("review_timeline", 970100),
            review_id,
            action_text,
            event_type,
            operator_name,
            int(row["next_seq"] if row else 1),
        ),
    )


def sync_workspace_summary() -> None:
    status_counts = {
        row["status"]: int(row["count"])
        for row in query_all("SELECT status, COUNT(*) AS count FROM upload_task GROUP BY status")
    }
    current = query_one("SELECT * FROM workspace_summary WHERE id = 1")
    if current is None:
        return
    pending_upload = max(12, status_counts.get("待上传", 0))
    pending_correction = max(3, status_counts.get("待补正", 0))
    pending_submit = max(5, status_counts.get("待提交", 0))
    under_review = max(3, status_counts.get("审核中", 0))
    completed = max(36, status_counts.get("已完成", 0) + status_counts.get("已归档", 0))
    current_todo = max(27, pending_upload + pending_correction + pending_submit + under_review)
    execute(
        """
        UPDATE workspace_summary
        SET current_todo = %s,
            pending_upload = %s,
            pending_correction = %s,
            pending_submit = %s,
            under_review = %s,
            completed = %s,
            updated_at = NOW()
        WHERE id = 1
        """,
        (current_todo, pending_upload, pending_correction, pending_submit, under_review, completed),
    )


def save_task_draft(task_id: str, payload: dict) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    append_task_timeline(task_id, payload.get("comment") or "暂存任务办理进度")
    return {"ok": True, "taskId": task_id, "status": task["status"], "message": "已暂存任务办理进度"}


def resolve_document_id_for_link(task_id: str, raw_document_id: Any) -> int | None:
    if raw_document_id is None:
        return None

    raw_value = str(raw_document_id).strip()
    if raw_value.isdigit():
        return int(raw_value)

    candidate = query_one(
        "SELECT * FROM task_candidate_document WHERE id = %s AND task_id = %s",
        (raw_value, task_id),
    )
    if candidate is None:
        return None

    candidate_name = candidate["name"]
    document = query_one(
        """
        SELECT id
        FROM document_record
        WHERE document_name = %s
        ORDER BY uploaded_at DESC, id DESC
        LIMIT 1
        """,
        (candidate_name,),
    )
    if document is not None:
        return int(document["id"])

    stem = candidate_name.rsplit(".", 1)[0]
    document = query_one(
        """
        SELECT id
        FROM document_record
        WHERE document_name LIKE %s
        ORDER BY uploaded_at DESC, id DESC
        LIMIT 1
        """,
        (f"%{stem}%",),
    )
    if document is not None:
        return int(document["id"])

    short_name = stem.split("_", 1)[0]
    document = query_one(
        """
        SELECT id
        FROM document_record
        WHERE document_name LIKE %s
        ORDER BY uploaded_at DESC, id DESC
        LIMIT 1
        """,
        (f"%{short_name}%",),
    )
    return int(document["id"]) if document is not None else None


def link_task_document(task_id: str, payload: dict) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    document_id = resolve_document_id_for_link(task_id, payload.get("documentId"))
    if document_id is None:
        raise ValueError("documentId 或候选资料 ID 不存在")
    document = query_one("SELECT * FROM document_record WHERE id = %s", (document_id,))
    if document is None:
        raise ValueError("documentId 不存在")
    relation_id = next_id("document_task_relation", 950100)
    execute(
        """
        INSERT INTO document_task_relation
        (id, document_id, task_id, relation_type, relation_status, match_score, linked_by, linked_at, source)
        VALUES (%s, %s, %s, 'REQUIREMENT', 'LINKED', %s, %s, NOW(), %s)
        ON DUPLICATE KEY UPDATE relation_status='LINKED', linked_at=VALUES(linked_at), source=VALUES(source)
        """,
        (
            relation_id,
            document_id,
            task_id,
            payload.get("matchScore") or 90,
            payload.get("operatorId") or 10001,
            payload.get("source") or "MANUAL",
        ),
    )
    requirement_id = payload.get("requirementId")
    if not requirement_id:
        raw_document_id = str(payload.get("documentId") or "")
        candidate = query_one(
            "SELECT * FROM task_candidate_document WHERE id = %s AND task_id = %s",
            (raw_document_id, task_id),
        )
        requirement_id = find_matching_requirement_id(
            task_id,
            document["document_name"],
            candidate["name"] if candidate else "",
        )
    linked = mark_task_requirement_linked(task_id, document["document_name"], candidate["name"] if candidate else "", requirement_id, document["document_type"])
    progress = linked["progress"]
    append_task_timeline(task_id, f"关联资料：{document['document_name']}")
    return {
        "ok": True,
        "taskId": task_id,
        "documentId": str(document_id),
        "requirementId": linked["requirementId"],
        "requirementName": linked["requirementName"],
        "progress": progress,
    }


def submit_task_review(task_id: str, payload: dict) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    existing_review = None
    if task["status"] == "审核中":
        existing_review = query_one(
            """
            SELECT id
            FROM review_record
            WHERE task_id = %s AND status = '待审核'
            ORDER BY submit_time DESC
            LIMIT 1
            """,
            (task_id,),
        )
    if existing_review:
        validation = recalculate_task_progress(task_id)
        return {
            "ok": True,
            "taskId": task_id,
            "reviewId": existing_review["id"],
            "status": "审核中",
            "message": "该任务已在审核中，请勿重复提交",
            "validation": validation,
        }

    validation = recalculate_task_progress(task_id)
    if not validation["canSubmit"]:
        return {
            "ok": False,
            "taskId": task_id,
            "message": "所选任务存在资料缺失或格式异常，暂不可提交",
            "validation": validation,
        }
    latest_returned_review = query_one(
        """
        SELECT id
        FROM review_record
        WHERE task_id = %s AND status = '已退回'
        ORDER BY submit_time DESC, updated_at DESC
        LIMIT 1
        """,
        (task_id,),
    )
    if latest_returned_review:
        execute(
            "UPDATE review_requirement SET requirement_status = '已补正' WHERE review_id = %s",
            (latest_returned_review["id"],),
        )
        append_review_timeline(latest_returned_review["id"], "补正提交（任务资料已重新提交审核）", "RESUBMIT", payload.get("operatorName") or task.get("assignee_name") or "项目管理员")

    review_id = f"r-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    operator_name = payload.get("operatorName") or task.get("assignee_name") or "项目管理员"
    comment = payload.get("comment") or "资料完整，提交审核"
    execute(
        """
        INSERT INTO review_record
        (id, task_id, task_name, module_code, module_name, submit_time, status, reviewer_id, reviewer, comment_summary, next_step)
        VALUES (%s, %s, %s, %s, %s, NOW(), '待审核', NULL, '-', %s, '查看进度')
        """,
        (review_id, task_id, task["name"], task["module_code"], task["module_name"], comment),
    )
    execute("UPDATE upload_task SET status = '审核中', next_step = '查看进度' WHERE id = %s", (task_id,))
    append_task_timeline(task_id, comment)
    append_review_timeline(review_id, f"提交审核（{operator_name} 提交任务）", "SUBMIT", operator_name)
    append_review_timeline(
        review_id,
        f"完整性校验（系统校验通过，共{validation['completed']}/{validation['total']}项资料完整）",
        "VALIDATE",
        "系统",
    )
    sync_workspace_summary()
    return {
        "ok": True,
        "taskId": task_id,
        "reviewId": review_id,
        "status": "审核中",
        "message": "已提交审核",
        "validation": validation,
    }


def approve_review(review_id: str, payload: dict) -> dict | None:
    review = query_one("SELECT * FROM review_record WHERE id = %s", (review_id,))
    if review is None:
        return None
    if review["status"] != "待审核":
        return {
            "ok": False,
            "reviewId": review_id,
            "taskId": review["task_id"],
            "status": review["status"],
            "message": "该审核记录当前状态不可重复审核",
        }
    reviewer = payload.get("reviewer") or payload.get("operatorName") or "项目审核人"
    comment = payload.get("comment") or "资料完整，审核通过"
    execute(
        """
        UPDATE review_record
        SET status = '已通过',
            reviewer = %s,
            comment_summary = %s,
            next_step = '查看结果',
            updated_at = NOW()
        WHERE id = %s
        """,
        (reviewer, comment, review_id),
    )
    execute(
        """
        UPDATE upload_task
        SET status = '已完成',
            next_step = '查看结果',
            updated_at = NOW()
        WHERE id = %s
        """,
        (review["task_id"],),
    )
    append_review_timeline(review_id, f"审核通过（{reviewer}：{comment}）", "APPROVE", reviewer)
    append_task_timeline(review["task_id"], f"审核通过：{comment}")
    sync_workspace_summary()
    return {
        "ok": True,
        "reviewId": review_id,
        "taskId": review["task_id"],
        "status": "已通过",
        "taskStatus": "已完成",
        "message": "审核已通过，任务已完成",
    }


def return_review(review_id: str, payload: dict) -> dict | None:
    review = query_one("SELECT * FROM review_record WHERE id = %s", (review_id,))
    if review is None:
        return None
    if review["status"] != "待审核":
        return {
            "ok": False,
            "reviewId": review_id,
            "taskId": review["task_id"],
            "status": review["status"],
            "message": "该审核记录当前状态不可退回",
        }
    reviewer = payload.get("reviewer") or payload.get("operatorName") or "项目审核人"
    comment = payload.get("comment") or "资料需补正后重新提交"
    requirements = payload.get("requirements") or [
        "请补充缺失资料或重新关联有效资料。",
        "请修正格式异常资料后重新提交审核。",
    ]
    if isinstance(requirements, str):
        requirements = [requirements]
    normalized_requirements = [str(item).strip() for item in requirements if str(item).strip()]
    if not normalized_requirements:
        normalized_requirements = ["请根据审核意见完成资料补正后重新提交。"]

    execute(
        """
        UPDATE review_record
        SET status = '已退回',
            reviewer = %s,
            comment_summary = %s,
            next_step = '进入补正',
            updated_at = NOW()
        WHERE id = %s
        """,
        (reviewer, comment, review_id),
    )
    execute(
        """
        UPDATE upload_task
        SET status = '待补正',
            next_step = '继续补正',
            updated_at = NOW()
        WHERE id = %s
        """,
        (review["task_id"],),
    )
    execute("DELETE FROM review_requirement WHERE review_id = %s", (review_id,))
    for sequence_no, requirement in enumerate(normalized_requirements, 1):
        execute(
            """
            INSERT INTO review_requirement(id, review_id, requirement_text, requirement_status, sequence_no)
            VALUES (%s, %s, %s, '待补正', %s)
            """,
            (next_id("review_requirement", 980100), review_id, requirement, sequence_no),
        )
    append_review_timeline(review_id, f"审核退回（{reviewer}：{comment}）", "RETURN", reviewer)
    append_task_timeline(review["task_id"], f"审核退回：{comment}")
    sync_workspace_summary()
    return {
        "ok": True,
        "reviewId": review_id,
        "taskId": review["task_id"],
        "status": "已退回",
        "taskStatus": "待补正",
        "message": "审核已退回，任务已转入待补正",
        "requirements": normalized_requirements,
    }


def get_document_summary() -> dict:
    row = query_one(
        """
        SELECT
          COUNT(*) AS sample_count,
          SUM(CASE WHEN uploaded_at >= '2026-08-01' THEN 1 ELSE 0 END) AS month_new_sample,
          SUM(CASE WHEN validity_status = '即将失效' THEN 1 ELSE 0 END) AS expiring_soon_sample
        FROM document_record
        """
    )
    sample_count = int((row or {}).get("sample_count") or 0)
    extra_count = max(0, sample_count - 10)
    return {
        "documentTotal": 368 + extra_count,
        "monthNew": 24 + extra_count,
        "pendingArchive": 6,
        "expiringSoon": max(4, int((row or {}).get("expiring_soon_sample") or 0)),
    }


def get_documents() -> dict:
    rows = query_all("SELECT * FROM document_record ORDER BY id DESC")
    extra_count = max(0, len(rows) - 10)
    return {
        "total": 368 + extra_count,
        "items": [
            {
                "id": str(row["id"]),
                "documentName": row["document_name"],
                "documentType": row["document_type"],
                "module": row["module_code"],
                "period": row["period_value"],
                "version": row["version_no"],
                "source": row["source_name"],
                "relationCount": row["relation_count"],
                "validityStatus": row["validity_status"],
                "uploadedAt": value_for_json(row["uploaded_at"]),
            }
            for row in rows
        ],
    }


def get_reviews() -> dict:
    rows = query_all("SELECT * FROM review_record ORDER BY submit_time DESC")
    status_counts = {row["status"]: int(row["count"]) for row in query_all("SELECT status, COUNT(*) AS count FROM review_record GROUP BY status")}
    pending_review = max(3, status_counts.get("待审核", 0))
    passed = max(21, status_counts.get("已通过", 0))
    returned = max(3, status_counts.get("已退回", 0))
    return {
        "statusCards": [
            {"label": "待审核", "value": pending_review, "unit": "项", "color": "#2f9cff"},
            {"label": "已通过", "value": passed, "unit": "项", "color": "#69e36f"},
            {"label": "已退回", "value": returned, "unit": "项", "color": "#ff4f5e"},
            {"label": "补正逾期", "value": 1, "unit": "项", "color": "#ffb347"},
        ],
        "items": [
            {
                "id": row["id"],
                "taskId": row["task_id"],
                "taskName": row["task_name"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "submitTime": value_for_json(row["submit_time"]),
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in rows
        ],
    }


def get_review_detail(review_id: str) -> dict | None:
    row = query_one("SELECT * FROM review_record WHERE id = %s", (review_id,))
    if row is None:
        return None

    requirement_count = query_one(
        "SELECT COUNT(*) AS total FROM review_requirement WHERE review_id = %s",
        (review_id,),
    )
    correction_deadline = None
    if requirement_count and int(requirement_count["total"]) > 0 and row.get("submit_time"):
        correction_deadline = row["submit_time"] + timedelta(days=3)

    return {
        "id": row["id"],
        "taskId": row["task_id"],
        "taskName": row["task_name"],
        "module": row["module_code"],
        "moduleName": row["module_name"],
        "submitTime": value_for_json(row["submit_time"]),
        "status": row["status"],
        "reviewer": row["reviewer"],
        "commentSummary": row["comment_summary"],
        "nextStep": row["next_step"],
        "correctionDeadline": value_for_json(correction_deadline) if correction_deadline else None,
        "requirementCount": int(requirement_count["total"]) if requirement_count else 0,
    }


def get_review_timeline(review_id: str) -> dict:
    rows = query_all(
        """
        SELECT *
        FROM review_timeline
        WHERE review_id = %s
        ORDER BY sequence_no, event_time, id
        """,
        (review_id,),
    )
    return {
        "items": [
            {
                "id": row["id"],
                "reviewId": row["review_id"],
                "time": value_for_json(row["event_time"]),
                "action": row["action_text"],
                "eventType": row["event_type"],
                "operatorName": row["operator_name"],
            }
            for row in rows
        ]
    }


def get_review_requirements(review_id: str) -> dict:
    rows = query_all(
        """
        SELECT *
        FROM review_requirement
        WHERE review_id = %s
        ORDER BY sequence_no, id
        """,
        (review_id,),
    )
    return {
        "items": [
            {
                "id": row["id"],
                "reviewId": row["review_id"],
                "requirement": row["requirement_text"],
                "requirementText": row["requirement_text"],
                "status": row["requirement_status"],
            }
            for row in rows
        ]
    }


def get_ai_parse_queue() -> dict:
    rows = query_all("SELECT * FROM v_ai_parse_queue_current ORDER BY job_id")
    status_map = {
        "SUCCESS": "解析完成",
        "RUNNING": "匹配中 96%",
        "WAIT_CONFIRM": "待确认",
        "PENDING": "待确认",
        "ARCHIVED": "已入库",
        "FAILED": "解析失败",
    }
    progress_map = {"SUCCESS": 100, "RUNNING": 96, "WAIT_CONFIRM": 0, "PENDING": 0, "ARCHIVED": 100, "FAILED": 0}
    return {
        "items": [
            {
                "id": f"p{index + 1}",
                "jobId": row["job_id"],
                "fileId": row["file_id"],
                "fileName": row["file_name"],
                "size": format_size(row.get("file_size") or 0),
                "progress": progress_map.get(row["job_status"], 0),
                "status": status_map.get(row["job_status"], row["job_status"]),
            }
            for index, row in enumerate(rows)
        ]
    }


def format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.2f}MB"
    if size >= 1024:
        return f"{size / 1024:.2f}KB"
    return f"{size}B"


def find_duplicate_file(sha256_hash: str) -> dict | None:
    if not sha256_hash:
        return None
    return query_one(
        """
        SELECT f.*, d.id AS matched_document_id
        FROM file_asset f
        LEFT JOIN document_record d ON d.file_id = f.id
        WHERE f.sha256_hash = %s
        ORDER BY f.upload_time DESC, f.id DESC
        LIMIT 1
        """,
        (sha256_hash,),
    )


def create_deduplication_record(file_id: int, duplicate_file: dict | None) -> None:
    if duplicate_file is None:
        return
    execute(
        """
        INSERT INTO deduplication_record
        (id, file_id, matched_file_id, matched_document_id, match_type, match_score,
         hash_equal, name_similar, content_similar, decision_status, created_at)
        VALUES (%s, %s, %s, %s, 'EXACT_HASH', 100.00, 1, 0, 1, 'PENDING', NOW())
        """,
        (
            next_id("deduplication_record", 990100),
            file_id,
            duplicate_file["id"],
            duplicate_file.get("matched_document_id"),
        ),
    )


def create_file_asset(payload: dict) -> dict:
    file_id = next_id("file_asset", 900100)
    original_name = payload.get("originalName") or payload.get("fileName") or "未命名资料.pdf"
    file_size = int(payload.get("fileSize") or payload.get("size") or 0)
    file_ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    sha256_hash = payload.get("sha256Hash") or hashlib.sha256(f"{original_name}|{file_size}|{datetime.now().isoformat()}".encode("utf-8")).hexdigest()
    duplicate_file = find_duplicate_file(sha256_hash)
    duplicate_status = "DUPLICATE" if duplicate_file else "UNIQUE"
    file_code = f"FILE-202607-{file_id}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    storage_path = payload.get("storagePath") or f"/demo/{original_name}"
    mime_type = payload.get("mimeType") or "application/octet-stream"
    uploader_name = payload.get("uploaderName") or "项目管理员"
    uploader_id = int(payload.get("uploaderId") or 10001)

    execute(
        """
        INSERT INTO file_asset
        (id, file_code, original_name, file_ext, mime_type, file_size, storage_path, storage_bucket,
         sha256_hash, upload_source, uploader_id, uploader_name, upload_time, duplicate_status, parse_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'local', %s, 'USER_UPLOAD', %s, %s, %s, %s, 'PENDING')
        """,
        (file_id, file_code, original_name, file_ext, mime_type, file_size, storage_path, sha256_hash, uploader_id, uploader_name, now, duplicate_status),
    )
    create_deduplication_record(file_id, duplicate_file)
    return {
        "fileId": file_id,
        "fileCode": file_code,
        "originalName": original_name,
        "fileSize": file_size,
        "storagePath": storage_path,
        "sha256Hash": sha256_hash,
        "duplicateStatus": duplicate_status,
        "matchedFileId": duplicate_file["id"] if duplicate_file else None,
        "matchedDocumentId": duplicate_file.get("matched_document_id") if duplicate_file else None,
        "parseStatus": "PENDING",
    }


def responsible_unit_for(document_type: str, module: str) -> str:
    if document_type == "工资支付资料":
        return "财务管理部"
    if module == "S":
        return "工程管理部"
    if module == "G":
        return "质量合规部"
    return "安全环保部"


def infer_valid_period(period: str, document_type: str) -> tuple[str, str]:
    if period == "2026-Q2":
        return "2026-04-01", "2026-06-30"
    if period == "2026-07":
        if document_type in {"临时用地合规资料", "高风险作业审批资料"}:
            return "2026-07-01", "2026-12-31"
        return "2026-07-01", "2026-08-31"
    return "2026-07-01", "2026-08-31"


def get_mapping_rules(document_type: str) -> list[dict]:
    return query_all(
        """
        SELECT *
        FROM ai_field_mapping_rule
        WHERE enabled = 1 AND document_type IN ('通用资料', %s)
        ORDER BY CASE WHEN document_type = '通用资料' THEN 0 ELSE 1 END, id
        """,
        (document_type,),
    )


def inferred_field_value(field_key: str, context: dict) -> tuple[str, str, float]:
    name = context["original_name"]
    document_type = context["document_type"]
    module = context["module"]
    period = context["period"]
    valid_start, valid_end = context["valid_period"]
    defaults = {
        "document_name": (name, name, 96.0),
        "document_type": (document_type, document_type, 92.0),
        "esg_module": (module, module, 95.0),
        "period": (period, period, 90.0),
        "responsible_unit": (context["responsible_unit"], context["responsible_unit"], 88.0),
        "valid_start_date": (valid_start, valid_start, 86.0),
        "valid_end_date": (valid_end, valid_end, 86.0),
        "monitor_date": (period + "-13" if period == "2026-07" else "2026-06-30", period + "-13" if period == "2026-07" else "2026-06-30", 82.0),
        "dust_exceed_count": ("1", "1", 78.0),
        "noise_exceed_count": ("1", "1", 78.0),
        "water_protection_issue_count": ("5", "5", 80.0),
        "diesel_usage": ("1280 L", "1280", 76.0),
        "electricity_usage": ("8600 kWh", "8600", 76.0),
        "material_usage": ("320 t", "320", 74.0),
        "carbon_emission": ("1360 tCO2e", "1360", 80.0),
        "risk_level": ("较大风险", "较大风险", 82.0),
        "work_location": ("K12+000-K18+000", "K12+000-K18+000", 78.0),
        "control_measure": ("专项方案审批、现场旁站、班前交底", "专项方案审批、现场旁站、班前交底", 76.0),
        "worker_count": ("23", "23", 78.0),
        "payment_amount": ("1280000 元", "1280000", 78.0),
        "payment_month": (period, period, 82.0),
        "permit_name": ("临时用地许可", "临时用地许可", 82.0),
        "permit_no": ("LYGS-TD-2026-07", "LYGS-TD-2026-07", 76.0),
        "permit_expire_date": (valid_end, valid_end, 82.0),
        "rectification_item": ("NCR整改关闭资料", "NCR整改关闭资料", 78.0),
        "rectification_status": ("待复查", "待复查", 80.0),
        "closed_date": (valid_end, valid_end, 70.0),
    }
    return defaults.get(field_key, ("", "", 60.0))


def build_parse_fields(original_name: str, document_type: str, module: str, period: str) -> list[tuple[str, str, str, str, str, float]]:
    valid_period = infer_valid_period(period, document_type)
    context = {
        "original_name": original_name,
        "document_type": document_type,
        "module": module,
        "period": period,
        "responsible_unit": responsible_unit_for(document_type, module),
        "valid_period": valid_period,
    }
    fields: list[tuple[str, str, str, str, str, float]] = []
    seen: set[str] = set()
    for rule in get_mapping_rules(document_type):
        key = rule["field_key"]
        if key in seen:
            continue
        seen.add(key)
        value, normalized, confidence = inferred_field_value(key, context)
        if value == "" and not rule.get("required"):
            continue
        fields.append((key, rule["field_name"], value, normalized, rule["value_type"], confidence))
    return fields


def start_parse_job(file_id: int) -> dict:
    file_row = query_one("SELECT * FROM file_asset WHERE id = %s", (file_id,))
    if file_row is None:
        raise ValueError(f"file_id 不存在：{file_id}")

    job_id = next_id("ai_parse_job", 910100)
    job_code = f"PARSE-202607-{job_id}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    original_name = file_row["original_name"]
    inferred_type = infer_document_type(original_name)
    module = infer_module(inferred_type)
    period = infer_period(original_name)

    execute(
        """
        INSERT INTO ai_parse_job
        (id, job_code, file_id, job_status, parse_engine, model_name, rule_version,
         started_at, finished_at, duration_ms, confidence, raw_result_json)
        VALUES (%s, %s, %s, 'WAIT_CONFIRM', 'ESG智能解析器', 'gpt-esg-parser-demo', 'V0.1',
                %s, %s, 1200, 92.00, JSON_OBJECT('document_type', %s, 'period', %s, 'module', %s))
        """,
        (job_id, job_code, file_id, now, now, inferred_type, period, module),
    )
    execute("UPDATE file_asset SET parse_status = 'WAIT_CONFIRM' WHERE id = %s", (file_id,))

    fields = build_parse_fields(original_name, inferred_type, module, period)
    field_id = next_id("ai_parse_field_result", 911100)
    for offset, field in enumerate(fields):
        execute(
            """
            INSERT INTO ai_parse_field_result
            (id, parse_job_id, field_key, field_name, field_value, normalized_value, value_type, confidence, confirm_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
            """,
            (field_id + offset, job_id, *field),
        )

    candidate_id = next_id("task_match_candidate", 920100)
    task = query_one(
        """
        SELECT id, name, module_code FROM upload_task
        WHERE module_code = %s AND name LIKE %s
        ORDER BY deadline ASC LIMIT 1
        """,
        (module, f"%{period[:4]}%" if period else "%"),
    ) or query_one("SELECT id, name, module_code FROM upload_task WHERE module_code = %s ORDER BY deadline ASC LIMIT 1", (module,))
    if task is not None:
        execute(
            """
            INSERT INTO task_match_candidate
            (id, parse_job_id, file_id, document_id, task_id, task_name, module_code, match_score, match_reason, reuse_count, candidate_status)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, 88.00, '资料类型、ESG模块和周期特征匹配', 0, 'PENDING')
            """,
            (candidate_id, job_id, file_id, task["id"], task["name"], task["module_code"]),
        )

    return {"jobId": job_id, "jobCode": job_code, "jobStatus": "WAIT_CONFIRM"}


def infer_document_type(name: str) -> str:
    if "碳" in name:
        return "碳排放活动数据表"
    if "高风险" in name:
        return "高风险作业审批资料"
    if "工资" in name:
        return "工资支付资料"
    if "临时用地" in name:
        return "临时用地合规资料"
    if "NCR" in name or "整改" in name:
        return "NCR整改关闭资料"
    if "水保" in name:
        return "水保监测月报"
    if "安全" in name or "培训" in name:
        return "安全教育培训记录"
    return "通用资料"


def infer_module(document_type: str) -> str:
    if document_type in {"高风险作业审批资料", "工资支付资料", "安全教育培训记录"}:
        return "S"
    if document_type in {"临时用地合规资料", "NCR整改关闭资料"}:
        return "G"
    return "E"


def infer_period(name: str) -> str:
    if "2026-07" in name or "7月" in name:
        return "2026-07"
    if "Q2" in name:
        return "2026-Q2"
    return "2026-07"


def get_parse_job(job_id: int) -> dict | None:
    row = query_one(
        """
        SELECT j.*, f.original_name
        FROM ai_parse_job j
        JOIN file_asset f ON f.id = j.file_id
        WHERE j.id = %s
        """,
        (job_id,),
    )
    if row is None:
        return None
    return {
        "jobId": row["id"],
        "jobCode": row["job_code"],
        "fileId": row["file_id"],
        "fileName": row["original_name"],
        "jobStatus": row["job_status"],
        "confidence": value_for_json(row["confidence"]),
        "startedAt": value_for_json(row["started_at"]),
        "finishedAt": value_for_json(row["finished_at"]),
    }


def get_parse_fields(job_id: int) -> dict:
    rows = query_all("SELECT * FROM ai_parse_field_result WHERE parse_job_id = %s ORDER BY id", (job_id,))
    return {
        "items": [
            {
                "id": row["id"],
                "fieldKey": row["field_key"],
                "fieldName": row["field_name"],
                "fieldValue": row["field_value"],
                "normalizedValue": row["normalized_value"],
                "valueType": row["value_type"],
                "confidence": value_for_json(row["confidence"]),
                "confirmStatus": row["confirm_status"],
                "confirmedValue": row["confirmed_value"],
            }
            for row in rows
        ]
    }


def get_match_candidates(job_id: int) -> dict:
    rows = query_all("SELECT * FROM task_match_candidate WHERE parse_job_id = %s ORDER BY match_score DESC", (job_id,))
    return {
        "items": [
            {
                "candidateId": row["id"],
                "taskId": row["task_id"],
                "taskName": row["task_name"],
                "module": row["module_code"],
                "matchScore": value_for_json(row["match_score"]),
                "matchReason": row["match_reason"],
                "reuseCount": row["reuse_count"],
                "candidateStatus": row["candidate_status"],
            }
            for row in rows
        ]
    }


def _text_contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _parse_decimal(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else default


def _business_domain(module: str, document_type: str, document_name: str) -> str:
    text = f"{document_type} {document_name}"
    if _text_contains_any(text, ["碳", "纰"]):
        return "CARBON"
    if module == "G":
        return "GOVERNANCE"
    if module == "S":
        if _text_contains_any(text, ["工资", "宸ヨ祫", "劳务", "纠纷"]):
            return "SOCIAL"
        return "SAFETY"
    return "ENVIRONMENT"


def _target_table_for_document(document_type: str, document_name: str) -> str:
    text = f"{document_type} {document_name}"
    if _text_contains_any(text, ["NCR", "整改", "鏁存敼"]):
        return "rectification_record"
    if _text_contains_any(text, ["临时用地", "涓存椂鐢ㄥ湴", "许可", "许可证"]):
        return "permit_record"
    if _text_contains_any(text, ["工资", "宸ヨ祫"]):
        return "salary_payment_record"
    if _text_contains_any(text, ["高风险", "楂橀", "作业审批"]):
        return "safety_risk_point"
    if _text_contains_any(text, ["碳", "纰"]):
        return "carbon_emission_activity"
    if _text_contains_any(text, ["水保", "姘翠繚"]):
        return "water_protection_issue"
    return "document_record"


def _insert_ingestion_job(
    *,
    source_id: int,
    job_type: str,
    business_domain: str,
    target_table: str,
    operator_id: int,
    operator_name: str,
) -> int:
    ingestion_job_id = next_id("data_ingestion_job", 660100)
    execute(
        """
        INSERT INTO data_ingestion_job
        (id, source_id, job_type, job_status, business_domain, target_table,
         started_at, finished_at, total_count, success_count, failed_count, operator_id, operator_name)
        VALUES (%s, %s, %s, 'SUCCESS', %s, %s, NOW(), NOW(), 1, 1, 0, %s, %s)
        """,
        (ingestion_job_id, source_id, job_type, business_domain, target_table, operator_id, operator_name),
    )
    return ingestion_job_id


def _insert_quality_check(
    *,
    ingestion_job_id: int,
    source_record_key: str,
    target_table: str,
    target_record_id: int | str,
    check_status: str,
    check_message: str,
) -> None:
    execute(
        """
        INSERT INTO data_quality_check_result
        (id, ingestion_job_id, source_record_key, target_table, target_record_id,
         check_type, check_status, check_message)
        VALUES (%s, %s, %s, %s, %s, 'FIELD_COMPLETENESS', %s, %s)
        """,
        (
            next_id("data_quality_check_result", 670100),
            ingestion_job_id,
            source_record_key,
            target_table,
            str(target_record_id),
            check_status,
            check_message,
        ),
    )


def _insert_source_trace(
    *,
    ingestion_job_id: int,
    source_id: int,
    source_record_key: str,
    document_id: int,
    file_id: int,
    target_table: str,
    target_record_id: int | str,
    operation_type: str,
    trace_payload: dict,
) -> None:
    execute(
        """
        INSERT INTO source_record_trace
        (id, ingestion_job_id, source_id, source_type, source_record_key,
         document_id, file_id, target_table, target_record_id, operation_type, trace_payload)
        VALUES (%s, %s, %s, 'FILE_UPLOAD', %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            next_id("source_record_trace", 680100),
            ingestion_job_id,
            source_id,
            source_record_key,
            document_id,
            file_id,
            target_table,
            str(target_record_id),
            operation_type,
            json.dumps(trace_payload, ensure_ascii=False),
        ),
    )


def _sync_confirmed_document_to_business_table(
    *,
    job_id: int,
    file_id: int,
    document_id: int,
    document_name: str,
    document_type: str,
    module: str,
    period: str,
    field_value: Any,
    operator_id: int,
    operator_name: str,
) -> dict:
    source_id = 610001
    target_table = _target_table_for_document(document_type, document_name)
    business_domain = _business_domain(module, document_type, document_name)
    ingestion_job_id = _insert_ingestion_job(
        source_id=source_id,
        job_type="FILE_PARSE_CONFIRM",
        business_domain=business_domain,
        target_table=target_table,
        operator_id=operator_id,
        operator_name=operator_name,
    )
    source_record_key = f"PARSE_JOB:{job_id}:DOC:{document_id}"
    trace_payload = {
        "parseJobId": job_id,
        "documentId": document_id,
        "documentName": document_name,
        "documentType": document_type,
        "module": module,
        "period": period,
        "syncMode": "confirm_parse_job",
    }

    synced_records: list[dict] = []

    if target_table == "water_protection_issue":
        target_id = next_id("water_protection_issue", 710100)
        issue_count = int(_parse_decimal(field_value("water_protection_issue_count", "1"), 1))
        execute(
            """
            INSERT INTO water_protection_issue
            (id, document_id, issue_status, found_date, closed_date)
            VALUES (%s, %s, '未闭环', '2026-07-13', NULL)
            """,
            (target_id, document_id),
        )
        trace_payload["extractedIssueCount"] = issue_count
        check_message = f"已根据水保资料生成未闭环问题样例，抽取问题数 {issue_count} 项。"
    elif target_table == "carbon_emission_activity":
        target_id = next_id("carbon_emission_activity", 720100)
        execute(
            """
            INSERT INTO carbon_emission_activity
            (id, document_id, period_value, diesel_usage, electricity_usage, material_usage, carbon_emission)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                target_id,
                document_id,
                period,
                _parse_decimal(field_value("diesel_usage", "1280")),
                _parse_decimal(field_value("electricity_usage", "8600")),
                _parse_decimal(field_value("material_usage", "320")),
                _parse_decimal(field_value("carbon_emission", "1360")),
            ),
        )
        material_id = next_id("carbon_material_usage", 720500)
        execute(
            """
            INSERT INTO carbon_material_usage
            (id, document_id, period_value, material_name, material_usage, material_unit)
            VALUES (%s, %s, %s, '主要材料', %s, 't')
            """,
            (material_id, document_id, period, _parse_decimal(field_value("material_usage", "320"))),
        )
        trace_payload["materialRecordId"] = material_id
        check_message = "已根据碳排放活动数据生成排放活动与材料用量样例。"
    elif target_table == "safety_risk_point":
        target_id = next_id("safety_risk_point", 730100)
        risk_level = field_value("risk_level", "较大风险").replace("风险", "")
        execute(
            """
            INSERT INTO safety_risk_point
            (id, document_id, risk_name, risk_level, control_status, control_measure, location, risk_type, control_start_date)
            VALUES (%s, %s, %s, %s, '持续管控', %s, %s, '高风险作业', '2026-07-13')
            """,
            (
                target_id,
                document_id,
                document_name,
                risk_level,
                field_value("control_measure", "专项方案审批与现场旁站"),
                field_value("work_location", "K12+000-K18+000"),
            ),
        )
        check_message = "已根据高风险作业资料生成安全风险点管控记录。"
    elif target_table == "salary_payment_record":
        target_id = next_id("salary_payment_record", 740100)
        execute(
            """
            INSERT INTO salary_payment_record
            (id, document_id, payment_month, worker_count, payment_amount, payment_status)
            VALUES (%s, %s, %s, %s, %s, '已确认')
            """,
            (
                target_id,
                document_id,
                field_value("payment_month", period),
                int(_parse_decimal(field_value("worker_count", "23"), 23)),
                _parse_decimal(field_value("payment_amount", "1280000"), 1280000),
            ),
        )
        check_message = "已根据工资支付资料生成工资支付确认记录。"
    elif target_table == "permit_record":
        target_id = next_id("permit_record", 750100)
        expire_date = field_value("permit_expire_date", "2026-07-30")
        permit_status = "临期"
        if expire_date < "2026-07-13":
            permit_status = "逾期"
        elif expire_date > "2026-08-12":
            permit_status = "有效"
        execute(
            """
            INSERT INTO permit_record
            (id, document_id, permit_name, permit_no, expire_date, status, permit_type, responsible_department)
            VALUES (%s, %s, %s, %s, %s, %s, '临时用地', '工程管理部')
            """,
            (
                target_id,
                document_id,
                field_value("permit_name", "临时用地许可"),
                field_value("permit_no", f"LYGS-PERMIT-{document_id}"),
                expire_date,
                permit_status,
            ),
        )
        check_message = "已根据许可资料生成许可台账记录。"
    elif target_table == "rectification_record":
        target_id = next_id("rectification_record", 760100)
        status = field_value("rectification_status", "待复查")
        closed_date = field_value("closed_date", "") if status in {"已关闭", "已销项"} else None
        execute(
            """
            INSERT INTO rectification_record
            (id, document_id, item_name, status, source_type, overdue, closed_date,
             issue_level, deadline, responsible_department, check_batch)
            VALUES (%s, %s, %s, %s, '资料上传确认', 0, %s, '一般', '2026-08-10', '工程管理部', 'P03智能入库')
            """,
            (target_id, document_id, field_value("rectification_item", document_name), status, closed_date),
        )
        check_message = "已根据整改关闭资料生成整改闭环记录。"
    else:
        target_id = document_id
        check_message = "资料已确认入库，暂未配置对应业务闭环表，保留资料级追溯。"

    _insert_quality_check(
        ingestion_job_id=ingestion_job_id,
        source_record_key=source_record_key,
        target_table=target_table,
        target_record_id=target_id,
        check_status="PASS",
        check_message=check_message,
    )
    _insert_source_trace(
        ingestion_job_id=ingestion_job_id,
        source_id=source_id,
        source_record_key=source_record_key,
        document_id=document_id,
        file_id=file_id,
        target_table=target_table,
        target_record_id=target_id,
        operation_type="INSERT",
        trace_payload=trace_payload,
    )
    synced_records.append({"targetTable": target_table, "targetRecordId": target_id, "operationType": "INSERT"})
    return {
        "ingestionJobId": ingestion_job_id,
        "sourceRecordKey": source_record_key,
        "businessDomain": business_domain,
        "targetTable": target_table,
        "businessRecords": synced_records,
    }


def confirm_parse_job(job_id: int, payload: dict) -> dict:
    job = query_one("SELECT * FROM ai_parse_job WHERE id = %s", (job_id,))
    if job is None:
        raise ValueError(f"parse_job 不存在：{job_id}")

    fields = {row["field_key"]: row for row in query_all("SELECT * FROM ai_parse_field_result WHERE parse_job_id = %s", (job_id,))}
    confirmed_fields = payload.get("confirmedFields") or []
    for field in confirmed_fields:
        execute(
            """
            UPDATE ai_parse_field_result
            SET confirmed_value = %s, confirm_status = 'CONFIRMED', confirmed_by = %s, confirmed_at = NOW()
            WHERE parse_job_id = %s AND field_key = %s
            """,
            (field.get("confirmedValue"), payload.get("operatorId") or 10001, job_id, field.get("fieldKey")),
        )

    def field_value(key: str, default: str = "") -> str:
        override = next((item.get("confirmedValue") for item in confirmed_fields if item.get("fieldKey") == key), None)
        if override is not None:
            return override
        row = fields.get(key)
        return (row or {}).get("normalized_value") or (row or {}).get("field_value") or default

    document_id = next_id("document_record", 930100)
    document_code = f"DOC-202607-{document_id}"
    document_name = field_value("document_name", f"解析资料_{document_id}")
    document_type = field_value("document_type", "通用资料")
    module = field_value("esg_module", infer_module(document_type))
    period = field_value("period", "2026-07")
    responsible_unit = field_value("responsible_unit", "项目管理部")
    default_valid_start, default_valid_end = infer_valid_period(period, document_type)
    valid_start_date = field_value("valid_start_date", default_valid_start)
    valid_end_date = field_value("valid_end_date", default_valid_end)

    execute(
        """
        INSERT INTO document_record
        (id, document_code, document_name, document_type, module_code, period_value, version_no, source_name,
         relation_count, validity_status, document_status, confirm_status, file_id, parse_job_id,
         responsible_unit, valid_start_date, valid_end_date, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'V1', 'ESG智能入库', 0, '有效', 'ACTIVE', 'CONFIRMED',
                %s, %s, %s, %s, %s, NOW())
        """,
        (
            document_id,
            document_code,
            document_name,
            document_type,
            module,
            period,
            job["file_id"],
            job_id,
            responsible_unit,
            valid_start_date,
            valid_end_date,
        ),
    )
    execute(
        """
        INSERT INTO document_version
        (id, document_id, file_id, version_no, version_desc, change_type, uploaded_by, uploaded_at, is_current)
        VALUES (%s, %s, %s, 'V1', '智能入库确认生成首版资料', 'CREATE', %s, NOW(), 1)
        """,
        (next_id("document_version", 940100), document_id, job["file_id"], payload.get("operatorId") or 10001),
    )
    execute("UPDATE ai_parse_job SET job_status = 'ARCHIVED' WHERE id = %s", (job_id,))
    execute("UPDATE file_asset SET parse_status = 'ARCHIVED' WHERE id = %s", (job["file_id"],))

    accepted_ids = payload.get("acceptedCandidateIds") or []
    linked_tasks: list[dict] = []
    for candidate_id in accepted_ids:
        candidate = query_one("SELECT * FROM task_match_candidate WHERE id = %s", (candidate_id,))
        if candidate is None:
            continue
        relation_id = next_id("document_task_relation", 950100)
        execute(
            """
            INSERT INTO document_task_relation
            (id, document_id, task_id, relation_type, relation_status, match_score, linked_by, linked_at, source)
            VALUES (%s, %s, %s, 'REQUIREMENT', 'LINKED', %s, %s, NOW(), 'AI_MATCH')
            """,
            (relation_id, document_id, candidate["task_id"], candidate["match_score"], payload.get("operatorId") or 10001),
        )
        execute("UPDATE task_match_candidate SET candidate_status = 'ACCEPTED', document_id = %s, confirmed_by = %s, confirmed_at = NOW() WHERE id = %s", (document_id, payload.get("operatorId") or 10001, candidate_id))
        linked = mark_task_requirement_linked(candidate["task_id"], document_name, candidate["task_name"], document_type=document_type)
        append_task_timeline(
            candidate["task_id"],
            f"智能入库关联资料：{document_name}" + (f"（匹配要求：{linked['requirementName']}）" if linked.get("requirementName") else ""),
        )
        linked_tasks.append(
            {
                "taskId": candidate["task_id"],
                "taskName": candidate["task_name"],
                "requirementId": linked["requirementId"],
                "requirementName": linked["requirementName"],
                "progress": linked["progress"],
            }
        )

    execute(
        """
        INSERT INTO manual_confirmation_log
        (id, target_type, target_id, action_type, before_json, after_json, comment, operator_id, operator_name, operated_at)
        VALUES (%s, 'PARSE_JOB', %s, 'CONFIRM_ARCHIVE', NULL, JSON_OBJECT('documentId', %s), %s, %s, %s, NOW())
        """,
        (next_id("manual_confirmation_log", 960100), job_id, document_id, payload.get("comment"), payload.get("operatorId") or 10001, payload.get("operatorName") or "项目管理员"),
    )
    ingestion_result = _sync_confirmed_document_to_business_table(
        job_id=job_id,
        file_id=job["file_id"],
        document_id=document_id,
        document_name=document_name,
        document_type=document_type,
        module=module,
        period=period,
        field_value=field_value,
        operator_id=payload.get("operatorId") or 10001,
        operator_name=payload.get("operatorName") or "项目管理员",
    )
    linked_count = len(accepted_ids)
    if linked_count:
        execute("UPDATE document_record SET relation_count = %s WHERE id = %s", (linked_count, document_id))

    return {
        "documentId": document_id,
        "documentCode": document_code,
        "documentStatus": "ACTIVE",
        "linkedTaskCount": linked_count,
        "linkedTasks": linked_tasks,
        **ingestion_result,
    }


def get_document_detail(document_id: int) -> dict | None:
    row = query_one(
        """
        SELECT d.*, f.original_name, f.file_ext, f.mime_type, f.file_size, f.sha256_hash, f.upload_source, f.upload_time
        FROM document_record d
        LEFT JOIN file_asset f ON f.id = d.file_id
        WHERE d.id = %s
        """,
        (document_id,),
    )
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "documentCode": row["document_code"],
        "documentName": row["document_name"],
        "documentType": row["document_type"],
        "module": row["module_code"],
        "period": row["period_value"],
        "version": row["version_no"],
        "source": row["source_name"],
        "relationCount": row["relation_count"],
        "validityStatus": row["validity_status"],
        "documentStatus": row["document_status"],
        "confirmStatus": row["confirm_status"],
        "responsibleUnit": row["responsible_unit"],
        "validStartDate": value_for_json(row["valid_start_date"]),
        "validEndDate": value_for_json(row["valid_end_date"]),
        "uploadedAt": value_for_json(row["uploaded_at"]),
        "file": {
            "fileId": row["file_id"],
            "originalName": row["original_name"] or row["document_name"],
            "fileExt": row["file_ext"],
            "mimeType": row["mime_type"],
            "fileSize": row["file_size"],
            "fileSizeText": format_size(row["file_size"] or 0),
            "sha256Hash": row["sha256_hash"],
            "uploadSource": row["upload_source"],
            "uploadTime": value_for_json(row["upload_time"]),
        },
        "tags": infer_document_tags(row),
        "isUnique": True,
    }


def infer_document_tags(row: dict) -> list[str]:
    tags = [row["document_type"], row["module_code"]]
    if row.get("source_name"):
        tags.append(row["source_name"])
    if row.get("period_value"):
        tags.append(row["period_value"])
    return [str(tag) for tag in tags if tag]


def get_document_versions(document_id: int) -> dict:
    rows = query_all(
        """
        SELECT v.*, u.display_name AS uploaded_by_name
        FROM document_version v
        LEFT JOIN user_account u ON u.id = v.uploaded_by
        WHERE v.document_id = %s
        ORDER BY v.uploaded_at DESC, v.id DESC
        """,
        (document_id,),
    )
    if not rows:
        doc = query_one("SELECT * FROM document_record WHERE id = %s", (document_id,))
        if doc is None:
            return {"items": []}
        return {
            "items": [
                {
                    "id": f"v-{doc['id']}",
                    "documentId": str(doc["id"]),
                    "versionNo": doc["version_no"],
                    "versionDesc": "当前资料版本",
                    "changeType": "CURRENT",
                    "uploadedBy": doc.get("created_by"),
                    "uploadedByName": "系统",
                    "uploadedAt": value_for_json(doc["uploaded_at"]),
                    "isCurrent": True,
                }
            ]
        }
    return {
        "items": [
            {
                "id": row["id"],
                "documentId": str(row["document_id"]),
                "fileId": row["file_id"],
                "versionNo": row["version_no"],
                "versionDesc": row["version_desc"],
                "changeType": row["change_type"],
                "uploadedBy": row["uploaded_by"],
                "uploadedByName": row["uploaded_by_name"] or "系统",
                "uploadedAt": value_for_json(row["uploaded_at"]),
                "isCurrent": bool(row["is_current"]),
            }
            for row in rows
        ]
    }


def get_document_relations(document_id: int) -> dict:
    rows = query_all(
        """
        SELECT r.*, t.name AS task_name, t.module_code, t.module_name, t.cycle, t.status AS task_status
        FROM document_task_relation r
        LEFT JOIN upload_task t ON t.id = r.task_id
        WHERE r.document_id = %s
        ORDER BY r.linked_at DESC, r.id DESC
        """,
        (document_id,),
    )
    return {
        "items": [
            {
                "id": row["id"],
                "documentId": str(row["document_id"]),
                "taskId": row["task_id"],
                "taskName": row["task_name"] or row["task_id"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "cycle": row["cycle"],
                "status": row["task_status"] or row["relation_status"],
                "relationType": row["relation_type"],
                "relationStatus": row["relation_status"],
                "matchScore": value_for_json(row["match_score"]),
                "source": row["source"],
                "referenceCount": 1,
                "lastReference": value_for_json(row["linked_at"]),
            }
            for row in rows
        ]
    }


def json_value(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


def get_gis_layers(
    project_id: str = "LUOYI-ESG",
    section_id: str | None = None,
    current_time: str | None = None,
    visible_layer_ids: list[str] | None = None,
) -> dict:
    params: list[Any] = [project_id]
    where = ["project_id = %s", "enabled = 1"]
    if visible_layer_ids:
        placeholders = ", ".join(["%s"] * len(visible_layer_ids))
        where.append(f"id IN ({placeholders})")
        params.extend(visible_layer_ids)
    rows = query_all(
        f"""
        SELECT id, name, category, geometry_type, enabled, object_type, source_type,
               source_url, style_json, fields_json, feature_count, display_order
        FROM gis_layer
        WHERE {" AND ".join(where)}
        ORDER BY display_order, id
        """,
        tuple(params),
    )
    return {
        "code": 0,
        "data": [
            {
                "id": row["id"],
                "name": row["name"],
                "geometryType": row["geometry_type"],
                "enabled": bool(row["enabled"]),
                "objectType": row["object_type"],
                "featureCount": int(row["feature_count"] or 0),
                "fields": json_value(row["fields_json"], []),
                "source": {"type": "api", "url": row["source_url"]},
                "style": json_value(row["style_json"], {}),
            }
            for row in rows
        ],
        "meta": {
            "projectId": project_id,
            "sectionId": section_id,
            "currentTime": current_time,
            "total": len(rows),
        },
    }


def get_gis_features(
    project_id: str = "LUOYI-ESG",
    layer_id: str | None = None,
    section_id: str | None = None,
    current_time: str | None = None,
) -> dict:
    params: list[Any] = [project_id]
    where = ["project_id = %s"]
    if layer_id:
        where.append("layer_id = %s")
        params.append(layer_id)
    if section_id:
        where.append("section_id = %s")
        params.append(section_id)

    rows = query_all(
        f"""
        SELECT id, layer_id, object_type, name, geometry_json, properties_json,
               status, risk_level, updated_at
        FROM gis_feature
        WHERE {" AND ".join(where)}
        ORDER BY layer_id, id
        """,
        tuple(params),
    )
    return {
        "code": 0,
        "data": [
            {
                "id": row["id"],
                "layerId": row["layer_id"],
                "objectType": row["object_type"],
                "name": row["name"],
                "geometry": json_value(row["geometry_json"], {}),
                "properties": json_value(row["properties_json"], {}),
                "status": row["status"],
                "riskLevel": row["risk_level"],
                "updatedAt": value_for_json(row["updated_at"]),
            }
            for row in rows
        ],
        "meta": {
            "projectId": project_id,
            "layerId": layer_id,
            "sectionId": section_id,
            "currentTime": current_time,
            "total": len(rows),
        },
    }
