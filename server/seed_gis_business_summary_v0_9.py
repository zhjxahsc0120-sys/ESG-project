from __future__ import annotations

import json
from typing import Any

from mysql_db import mysql_connect


PROJECT_ID = "LUOYI-ESG"


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def create_tables() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS gis_feature_business_summary (
          feature_id VARCHAR(96) PRIMARY KEY,
          project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
          object_type VARCHAR(64) NOT NULL,
          status_code VARCHAR(32) NULL,
          status_label VARCHAR(32) NULL,
          dashboard_title VARCHAR(120) NULL,
          dashboard_summary_json JSON NOT NULL,
          dashboard_note TEXT NULL,
          preview_detail_json JSON NULL,
          target_module VARCHAR(64) NULL,
          target_route VARCHAR(255) NULL,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_gis_business_project (project_id),
          CONSTRAINT fk_gis_business_feature
            FOREIGN KEY (feature_id) REFERENCES gis_feature(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS gis_feature_business_relation (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
          feature_id VARCHAR(96) NOT NULL,
          relation_type VARCHAR(64) NOT NULL,
          relation_code VARCHAR(64) NULL,
          relation_name VARCHAR(160) NOT NULL,
          relation_status VARCHAR(32) NULL,
          risk_level INT NULL,
          source_table VARCHAR(80) NULL,
          source_id VARCHAR(64) NULL,
          summary TEXT NULL,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_gis_relation_feature (feature_id),
          INDEX idx_gis_relation_type (relation_type),
          CONSTRAINT fk_gis_relation_feature
            FOREIGN KEY (feature_id) REFERENCES gis_feature(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


SUMMARY_ROWS = [
    {
        "feature_id": "section-1-1",
        "object_type": "road-section",
        "status_code": "normal",
        "status_label": "正常",
        "dashboard_title": "施工标段概览",
        "summary": [
            {"label": "建设进度", "value": "72%"},
            {"label": "环保问题", "value": "1项"},
            {"label": "风险点", "value": "1处"},
            {"label": "计划完工", "value": "2027年06月"},
        ],
        "note": "当前标段处于主体施工阶段，环保问题和风险点均纳入台账跟踪。",
        "detail": [
            {"label": "施工单位", "value": "广西路桥工程集团第一项目部"},
            {"label": "监理单位", "value": "广西交通工程监理咨询公司"},
            {"label": "资料说明", "value": "标段业务摘要由施工进度、环保闭环、安全风险等台账汇总形成。"},
        ],
        "target_module": "dashboard-gis",
    },
    {
        "feature_id": "section-2-1",
        "object_type": "road-section",
        "status_code": "normal",
        "status_label": "正常",
        "dashboard_title": "施工标段概览",
        "summary": [
            {"label": "建设进度", "value": "58%"},
            {"label": "环保问题", "value": "3项"},
            {"label": "风险点", "value": "1处"},
            {"label": "计划完工", "value": "2027年10月"},
        ],
        "note": "当前标段处于主体施工阶段，环保问题和风险点均纳入台账跟踪。",
        "detail": [
            {"label": "施工单位", "value": "广西路建工程集团第二项目部"},
            {"label": "监理单位", "value": "北京华通公路桥梁监理公司"},
            {"label": "资料说明", "value": "标段业务摘要由施工进度、环保闭环、安全风险等台账汇总形成。"},
        ],
        "target_module": "dashboard-gis",
    },
    {
        "feature_id": "section-3-1",
        "object_type": "road-section",
        "status_code": "attention",
        "status_label": "关注",
        "dashboard_title": "施工标段概览",
        "summary": [
            {"label": "建设进度", "value": "46%"},
            {"label": "环保问题", "value": "2项"},
            {"label": "风险点", "value": "2处"},
            {"label": "计划完工", "value": "2028年03月"},
        ],
        "note": "当前标段存在需持续关注的风险点，建议结合风险预警与督办模块查看。",
        "detail": [
            {"label": "施工单位", "value": "中交第四公路工程局项目部"},
            {"label": "监理单位", "value": "广西桂通工程管理集团"},
            {"label": "资料说明", "value": "标段业务摘要由施工进度、环保闭环、安全风险等台账汇总形成。"},
        ],
        "target_module": "dashboard-gis",
    },
    {
        "feature_id": "water-1-1",
        "object_type": "water-source",
        "status_code": "normal",
        "status_label": "正常管控",
        "dashboard_title": "环保区域概览",
        "summary": [
            {"label": "当前状态", "value": "正常管控"},
            {"label": "最近巡查", "value": "2026-07-11"},
            {"label": "责任单位", "value": "安全环保部"},
        ],
        "note": "该区域已纳入环保敏感点管控，后续与巡查记录、问题闭环数据联动。",
        "detail": [
            {"label": "保护对象", "value": "沿线村镇集中式饮用水水源"},
            {"label": "保护级别", "value": "二级保护区"},
        ],
        "target_module": "environment",
    },
    {
        "feature_id": "water-2-1",
        "object_type": "water-source",
        "status_code": "normal",
        "status_label": "正常管控",
        "dashboard_title": "环保区域概览",
        "summary": [
            {"label": "当前状态", "value": "正常管控"},
            {"label": "最近巡查", "value": "2026-07-10"},
            {"label": "责任单位", "value": "安全环保部"},
        ],
        "note": "该区域已纳入环保敏感点管控，后续与巡查记录、问题闭环数据联动。",
        "detail": [
            {"label": "保护对象", "value": "沿线水源保护区"},
            {"label": "保护级别", "value": "二级保护区"},
        ],
        "target_module": "environment",
    },
    {
        "feature_id": "eco-1-1",
        "object_type": "ecological-zone",
        "status_code": "normal",
        "status_label": "正常管控",
        "dashboard_title": "环保区域概览",
        "summary": [
            {"label": "当前状态", "value": "正常管控"},
            {"label": "最近巡查", "value": "2026-07-09"},
            {"label": "责任单位", "value": "安全环保部"},
        ],
        "note": "生态保护区按敏感区域管理，施工扰动和恢复情况纳入环保闭环台账。",
        "detail": [
            {"label": "敏感类型", "value": "生态保护区"},
            {"label": "管控要求", "value": "边界防护、扰动控制、恢复复绿"},
        ],
        "target_module": "environment",
    },
    {
        "feature_id": "waste-1-1",
        "object_type": "spoil-site",
        "status_code": "attention",
        "status_label": "关注",
        "dashboard_title": "弃渣点概览",
        "summary": [
            {"label": "当前状态", "value": "重点巡查"},
            {"label": "最近巡查", "value": "2026-07-12"},
            {"label": "责任单位", "value": "工程管理部"},
        ],
        "note": "弃渣点已纳入环保敏感点和水保巡查清单，异常情况进入问题闭环。",
        "detail": [
            {"label": "管控事项", "value": "边坡防护、排水、复绿"},
            {"label": "关联资料", "value": "弃渣场巡查记录"},
        ],
        "target_module": "environment",
    },
    {
        "feature_id": "waste-2-1",
        "object_type": "spoil-site",
        "status_code": "normal",
        "status_label": "正常管控",
        "dashboard_title": "弃渣点概览",
        "summary": [
            {"label": "当前状态", "value": "正常管控"},
            {"label": "最近巡查", "value": "2026-07-08"},
            {"label": "责任单位", "value": "工程管理部"},
        ],
        "note": "弃渣点已纳入环保敏感点和水保巡查清单，异常情况进入问题闭环。",
        "detail": [
            {"label": "管控事项", "value": "边坡防护、排水、复绿"},
            {"label": "关联资料", "value": "弃渣场巡查记录"},
        ],
        "target_module": "environment",
    },
    {
        "feature_id": "slope-1-1",
        "object_type": "slope-monitor",
        "status_code": "normal",
        "status_label": "正常",
        "dashboard_title": "风险监测概览",
        "summary": [
            {"label": "设备状态", "value": "在线"},
            {"label": "预警状态", "value": "正常"},
            {"label": "数据更新", "value": "2026-07-13 10:00"},
        ],
        "note": "当前监测点持续纳入风险预警范围，异常变化将同步进入风险督办链路。",
        "detail": [
            {"label": "监测类型", "value": "边坡位移"},
            {"label": "责任单位", "value": "安全环保部"},
        ],
        "target_module": "risk",
    },
    {
        "feature_id": "slope-2-1",
        "object_type": "slope-monitor",
        "status_code": "attention",
        "status_label": "关注",
        "dashboard_title": "风险监测概览",
        "summary": [
            {"label": "设备状态", "value": "在线"},
            {"label": "预警状态", "value": "关注"},
            {"label": "数据更新", "value": "2026-07-13 09:30"},
        ],
        "note": "当前监测点存在持续关注信号，建议结合风险预警与督办模块查看。",
        "detail": [
            {"label": "监测类型", "value": "边坡位移"},
            {"label": "责任单位", "value": "安全环保部"},
        ],
        "target_module": "risk",
    },
]


RELATIONS = [
    ("section-1-1", "environment_problem", "E02-001", "K12+400 便道扬尘整改", "整改中", 2, "env_issue_record", "E02-001", "与1标段施工便道扬尘控制相关"),
    ("section-2-1", "environment_problem", "E02-003", "弃渣场截排水整改", "待复查", 2, "env_issue_record", "E02-003", "与2标段弃渣点巡查问题相关"),
    ("section-2-1", "safety_risk", "S02-002", "高边坡施工较大风险点", "持续管控", 3, "safety_risk_point", "S02-002", "与2标段边坡监测点相关"),
    ("section-3-1", "safety_risk", "S02-006", "边坡监测关注点", "持续管控", 3, "safety_risk_point", "S02-006", "与3标段边坡监测点相关"),
    ("water-1-1", "inspection_record", "IR-202607-001", "水源保护区巡查记录", "正常", 1, "inspection_record", "IR-202607-001", "水源保护区巡查无异常"),
    ("eco-1-1", "environment_problem", "E02-005", "生态保护区临边防护完善", "待销项", 2, "env_issue_record", "E02-005", "生态保护区边界防护整改"),
    ("waste-1-1", "inspection_record", "IR-202607-003", "弃渣场巡查记录", "关注", 2, "inspection_record", "IR-202607-003", "弃渣点截排水需持续巡查"),
    ("slope-2-1", "safety_risk", "S02-006", "边坡监测关注点", "持续管控", 3, "safety_risk_point", "S02-006", "监测点存在关注信号"),
]


def seed_summary() -> None:
    for item in SUMMARY_ROWS:
        execute(
            """
            INSERT INTO gis_feature_business_summary
              (feature_id, project_id, object_type, status_code, status_label,
               dashboard_title, dashboard_summary_json, dashboard_note,
               preview_detail_json, target_module, target_route)
            VALUES (%s, %s, %s, %s, %s, %s, CAST(%s AS JSON), %s, CAST(%s AS JSON), %s, %s)
            ON DUPLICATE KEY UPDATE
              object_type = VALUES(object_type),
              status_code = VALUES(status_code),
              status_label = VALUES(status_label),
              dashboard_title = VALUES(dashboard_title),
              dashboard_summary_json = VALUES(dashboard_summary_json),
              dashboard_note = VALUES(dashboard_note),
              preview_detail_json = VALUES(preview_detail_json),
              target_module = VALUES(target_module),
              target_route = VALUES(target_route),
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                item["feature_id"],
                PROJECT_ID,
                item["object_type"],
                item["status_code"],
                item["status_label"],
                item["dashboard_title"],
                dumps(item["summary"]),
                item["note"],
                dumps(item["detail"]),
                item["target_module"],
                item.get("target_route"),
            ),
        )


def seed_relations() -> None:
    execute("DELETE FROM gis_feature_business_relation WHERE project_id = %s", (PROJECT_ID,))
    for row in RELATIONS:
        execute(
            """
            INSERT INTO gis_feature_business_relation
              (project_id, feature_id, relation_type, relation_code, relation_name,
               relation_status, risk_level, source_table, source_id, summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (PROJECT_ID, *row),
        )


def main() -> None:
    create_tables()
    seed_summary()
    seed_relations()
    print(f"GIS business summary seed complete: {len(SUMMARY_ROWS)} summaries, {len(RELATIONS)} relations")


if __name__ == "__main__":
    main()
