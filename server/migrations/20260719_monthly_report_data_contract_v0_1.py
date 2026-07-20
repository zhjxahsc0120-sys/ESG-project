from __future__ import annotations

"""月报准备与输出数据契约迁移 V0.1。

仅扩展月报任务实例及其资料/校验链，清理既有演示专题中的占位姓名和旧状态。
不创建虚假的月报输出记录，不修改 G04 表，不覆盖非演示任务。
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql_db import mysql_connect  # noqa: E402


CYCLE_ID = 810001
DEMO_SOURCE_TAG = "V0.2_TEST"
DATA_NATURE = "demo"
PLACEHOLDER_NAMES = ("张三", "李四", "王五", "赵六", "钱七", "孙八")

ROLE_BY_TASK = {
    "MR-E-001": ("安全环保部", "环保资料专员"),
    "MR-E-002": ("安全环保部", "环保资料专员"),
    "MR-E-003": ("安全环保部", "环保资料专员"),
    "MR-E-004": ("安全环保部", "环保资料专员"),
    "MR-E-005": ("水保监测单位", "水保资料专员"),
    "MR-E-007": ("工程管理部", "环保资料专员"),
    "MR-E-008": ("技术管理部", "部门审核负责人"),
    "MR-E-010": ("工程计量部门", "ESG月报管理员"),
    "MR-S-001": ("安全环保部", "安全资料专员"),
    "MR-S-002": ("安全环保部", "安全资料专员"),
    "MR-S-003": ("安全环保部", "安全资料专员"),
    "MR-S-005": ("劳务管理部门", "劳务管理专员"),
    "MR-S-006": ("综合管理部门", "劳务管理专员"),
    "MR-G-001": ("工程管理部", "合规资料专员"),
    "MR-G-003": ("许可责任部门", "合规资料专员"),
    "MR-G-004": ("许可责任部门", "部门审核负责人"),
    "MR-G-005": ("工程管理部", "合规资料专员"),
    "MR-G-006": ("问题责任单位", "合规资料专员"),
    "MR-G-007": ("缺口责任单位", "合规资料专员"),
    "MR-G-011": ("档案管理部门", "ESG月报管理员"),
    "MR-X-002": ("施工单位", "ESG月报管理员"),
    "MR-X-004": ("监理单位", "监理资料专员"),
}

PENDING_DETAIL = {
    "MR-G-007": (
        "当期合规资料补齐材料尚未提交。",
        "提交资料或建立可追溯的资料关联后重新校验。",
        "SUBMIT_MATERIAL",
    ),
    "MR-G-011": (
        "资料目录台账及档案检查记录待责任确认。",
        "由责任角色确认目录范围、归档状态和当期适用性。",
        "CONFIRM_RESPONSIBILITY",
    ),
    "MR-E-010": (
        "月度工程计量资料的期间、签章或完整性校验未通过。",
        "补正当期计量资料并重新发起完整性校验。",
        "CORRECT_MATERIAL",
    ),
    "MR-G-004": (
        "许可证及许可变更文件的有效性资料待补正。",
        "补齐有效期、变更链或确认依据后重新校验。",
        "CORRECT_MATERIAL",
    ),
}


def columns(cur, table: str) -> set[str]:
    cur.execute(f"SHOW COLUMNS FROM `{table}`")
    return {row["Field"] for row in cur.fetchall()}


def add_column(cur, table: str, name: str, ddl: str) -> None:
    if name not in columns(cur, table):
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{name}` {ddl}")


def ensure_schema(cur) -> None:
    additions = {
        "responsible_department": "VARCHAR(255) NULL COMMENT '责任部门/单位标准字段'",
        "responsible_role": "VARCHAR(100) NULL COMMENT '无人员主数据时使用的责任角色'",
        "responsible_user_id": "BIGINT NULL COMMENT '正式责任用户ID'",
        "responsible_user_name": "VARCHAR(100) NULL COMMENT '正式责任用户姓名'",
        "data_nature": "VARCHAR(30) NULL COMMENT '数据性质：formal/demo'",
        "is_demo": "TINYINT(1) NOT NULL DEFAULT 0 COMMENT '演示记录标志'",
    }
    for name, ddl in additions.items():
        add_column(cur, "monthly_report_task_instance", name, ddl)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_task_material_link (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          link_code VARCHAR(100) NOT NULL,
          task_instance_id BIGINT NOT NULL,
          required_material_code VARCHAR(100) NOT NULL,
          required_material_name VARCHAR(255) NOT NULL,
          document_id BIGINT NULL,
          source_task_id VARCHAR(64) NULL,
          relation_status VARCHAR(30) NOT NULL,
          data_nature VARCHAR(30) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_monthly_material_link_code(link_code),
          INDEX idx_monthly_material_task(task_instance_id),
          INDEX idx_monthly_material_document(document_id),
          CONSTRAINT fk_monthly_material_task FOREIGN KEY (task_instance_id)
            REFERENCES monthly_report_task_instance(id)
        ) ENGINE=InnoDB COMMENT='月报任务所需资料及资料关联'
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_task_validation (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          validation_code VARCHAR(100) NOT NULL,
          task_instance_id BIGINT NOT NULL,
          validation_result VARCHAR(30) NOT NULL,
          issue_description VARCHAR(500) NULL,
          correction_requirement VARCHAR(500) NULL,
          next_action_type VARCHAR(50) NOT NULL,
          validated_at DATETIME NULL,
          data_nature VARCHAR(30) NOT NULL,
          is_demo TINYINT(1) NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY uk_monthly_validation_code(validation_code),
          UNIQUE KEY uk_monthly_validation_task(task_instance_id),
          CONSTRAINT fk_monthly_validation_task FOREIGN KEY (task_instance_id)
            REFERENCES monthly_report_task_instance(id)
        ) ENGINE=InnoDB COMMENT='月报任务完整性校验与补正记录'
        """
    )


def update_demo_tasks(cur) -> None:
    for task_code, (department, role) in ROLE_BY_TASK.items():
        cur.execute(
            """
            UPDATE monthly_report_task_instance
            SET responsible_department=%s, responsible_role=%s,
                responsible_user_id=NULL, responsible_user_name=NULL,
                data_nature=%s, is_demo=1,
                group_code=CASE WHEN group_code='X' THEN 'G' ELSE group_code END
            WHERE report_cycle_id=%s AND source_tag=%s AND task_code=%s
            """,
            (department, role, DATA_NATURE, CYCLE_ID, DEMO_SOURCE_TAG, task_code),
        )

    # 旧专题演示表保留作历史兼容，但不再含占位姓名或第二套状态词。
    placeholders = ",".join(["%s"] * len(PLACEHOLDER_NAMES))
    cur.execute(
        f"UPDATE monthly_report_chapter SET responsible_person=NULL WHERE cycle_id=%s AND responsible_person IN ({placeholders})",
        (CYCLE_ID, *PLACEHOLDER_NAMES),
    )
    cur.execute(
        """
        UPDATE monthly_report_chapter
        SET status=CASE status
          WHEN '已完成' THEN '校验通过'
          WHEN '编制中' THEN '待提交'
          WHEN '待补充' THEN '待补正'
          ELSE status END
        WHERE cycle_id=%s
        """,
        (CYCLE_ID,),
    )
    cur.execute(
        "UPDATE monthly_report_gap SET status='待补正' WHERE cycle_id=%s AND status IN ('待补齐','待补件')",
        (CYCLE_ID,),
    )
    cur.execute(
        "UPDATE monthly_report_cycle SET expected_complete_date=NULL, current_stage='资料归集' WHERE id=%s",
        (CYCLE_ID,),
    )

    # 旧 E/S/G 百分比改为同一 22 项任务事实的分组计算结果，不再使用 85/78/83。
    cur.execute(
        """
        UPDATE monthly_report_group_progress p
        JOIN (
          SELECT group_code,
                 ROUND(SUM(monthly_status='校验通过') * 100 / COUNT(*), 0) completion_rate
          FROM monthly_report_task_instance
          WHERE report_cycle_id=%s AND include_in_denominator=1
          GROUP BY group_code
        ) x ON x.group_code=p.group_code
        SET p.completion_rate=x.completion_rate
        WHERE p.cycle_id=%s
        """,
        (CYCLE_ID, CYCLE_ID),
    )
    stages = (
        ("collect", "资料归集", "active", 1),
        ("validate", "完整性校验", "active", 2),
        ("confirm", "责任确认", "pending", 3),
        ("generate", "月报生成", "pending", 4),
        ("finalize", "审核定稿", "pending", 5),
    )
    for chain_key, label, status, order in stages:
        cur.execute(
            """
            UPDATE monthly_report_status_chain
            SET chain_key=%s, label=%s, status=%s, display_order=%s
            WHERE cycle_id=%s AND display_order=%s
            """,
            (chain_key, label, status, order, CYCLE_ID, order),
        )


def seed_task_chains(cur) -> None:
    cur.execute(
        """
        SELECT id, task_code, task_name, upload_task_id, monthly_status, validation_passed_at
        FROM monthly_report_task_instance
        WHERE report_cycle_id=%s AND source_tag=%s
        ORDER BY id
        """,
        (CYCLE_ID, DEMO_SOURCE_TAG),
    )
    tasks = list(cur.fetchall())
    if len(tasks) != 22:
        raise RuntimeError(f"演示月报任务应为22项，实际为{len(tasks)}项")

    for task in tasks:
        code = task["task_code"]
        cur.execute(
            """
            INSERT INTO monthly_report_task_material_link
              (link_code, task_instance_id, required_material_code, required_material_name,
               document_id, source_task_id, relation_status, data_nature, is_demo)
            VALUES (%s,%s,%s,%s,NULL,%s,'UNLINKED',%s,1)
            ON DUPLICATE KEY UPDATE
              task_instance_id=VALUES(task_instance_id),
              required_material_name=VALUES(required_material_name),
              source_task_id=VALUES(source_task_id), document_id=NULL,
              relation_status='UNLINKED', data_nature=VALUES(data_nature), is_demo=1
            """,
            (f"DEMO-MONTHLY-MATERIAL-{code}", task["id"], f"{code}-MAT-001",
             task["task_name"], task.get("upload_task_id"), DATA_NATURE),
        )

        status = task["monthly_status"]
        if code in PENDING_DETAIL:
            issue, requirement, action = PENDING_DETAIL[code]
            result = status
            validated_at = None
        else:
            issue = requirement = None
            action = "VIEW_RESULT"
            result = "校验通过"
            validated_at = task.get("validation_passed_at")
        cur.execute(
            """
            INSERT INTO monthly_report_task_validation
              (validation_code, task_instance_id, validation_result, issue_description,
               correction_requirement, next_action_type, validated_at, data_nature, is_demo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)
            ON DUPLICATE KEY UPDATE
              task_instance_id=VALUES(task_instance_id), validation_result=VALUES(validation_result),
              issue_description=VALUES(issue_description), correction_requirement=VALUES(correction_requirement),
              next_action_type=VALUES(next_action_type), validated_at=VALUES(validated_at),
              data_nature=VALUES(data_nature), is_demo=1
            """,
            (f"DEMO-MONTHLY-VALIDATION-{code}", task["id"], result, issue,
             requirement, action, validated_at, DATA_NATURE),
        )


def verify(cur) -> dict:
    cur.execute(
        """
        SELECT COUNT(*) total,
               SUM(monthly_status='校验通过') passed,
               SUM(monthly_status='待提交') pending_submit,
               SUM(monthly_status='待确认') pending_confirm,
               SUM(monthly_status='待补正') pending_correction,
               SUM(task_mechanism='MONTHLY_FIXED') fixed_count,
               SUM(task_mechanism='CONDITIONAL') conditional_count,
               SUM(task_mechanism='PERIODIC_REFERENCE') reference_count,
               MIN(deadline) deadline_start, MAX(deadline) deadline_end,
               SUM(responsible_user_id IS NOT NULL OR responsible_user_name IS NOT NULL) named_users
        FROM monthly_report_task_instance
        WHERE report_cycle_id=%s AND source_tag=%s AND include_in_denominator=1
        """,
        (CYCLE_ID, DEMO_SOURCE_TAG),
    )
    summary = cur.fetchone()
    expected = (22, 18, 1, 1, 2, 16, 4, 2, "2026-08-02", "2026-08-05", 0)
    actual = (
        int(summary["total"]), int(summary["passed"]), int(summary["pending_submit"]),
        int(summary["pending_confirm"]), int(summary["pending_correction"]),
        int(summary["fixed_count"]), int(summary["conditional_count"]),
        int(summary["reference_count"]), str(summary["deadline_start"]),
        str(summary["deadline_end"]), int(summary["named_users"]),
    )
    if actual != expected:
        raise RuntimeError(f"月报冻结口径校验失败：{actual}")
    cur.execute("SELECT COUNT(*) n FROM monthly_report_task_material_link WHERE is_demo=1")
    links = int(cur.fetchone()["n"])
    cur.execute("SELECT COUNT(*) n FROM monthly_report_task_validation WHERE is_demo=1")
    validations = int(cur.fetchone()["n"])
    cur.execute(
        "SELECT COUNT(*) n FROM monthly_report_chapter WHERE cycle_id=%s AND responsible_person IN ('张三','李四','王五','赵六','钱七','孙八')",
        (CYCLE_ID,),
    )
    placeholders = int(cur.fetchone()["n"])
    if (links, validations, placeholders) != (22, 22, 0):
        raise RuntimeError(f"月报资料/校验链或占位姓名清理失败：{links, validations, placeholders}")
    return {"summary": actual, "materialLinks": links, "validations": validations}


def main() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            ensure_schema(cur)
            update_demo_tasks(cur)
            seed_task_chains(cur)
            result = verify(cur)
    print(f"[PASS] 月报数据契约迁移完成（幂等）：{result}")


if __name__ == "__main__":
    main()
