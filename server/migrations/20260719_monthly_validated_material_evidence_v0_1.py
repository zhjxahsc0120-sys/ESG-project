from __future__ import annotations

"""为18项已校验通过的月报演示任务补齐可追溯资料实例和资料链。"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql_db import mysql_connect  # noqa: E402


CYCLE_ID = 810001
SOURCE_TAG = "V0.2_TEST"
NOTICE = "功能验证资料，不作为正式月报、正式审核、正式签章或归档依据"

DOCUMENTS = {
    "MR-E-001": (830001, "2026年7月环境监测原始记录及监测报告", "E"),
    "MR-E-002": (830002, "2026年7月环境监测超标复测及处置记录", "E"),
    "MR-E-003": (830003, "2026年7月环保巡查及环保设施运行台账", "E"),
    "MR-E-004": (830004, "2026年7月环保问题整改闭环资料汇总", "E"),
    "MR-E-005": (830005, "2026年7月水土保持监测月报", "E"),
    "MR-E-007": (830006, "2026年7月施工能源及主要材料消耗统计表", "E"),
    "MR-E-008": (830007, "2026年7月碳排放因子依据及确认记录", "E"),
    "MR-S-001": (830008, "2026年7月安全事故台账及连续安全生产确认表", "S"),
    "MR-S-002": (830009, "2026年7月较大及以上安全风险管控月末快照", "S"),
    "MR-S-003": (830010, "2026年7月安全检查记录汇总表", "S"),
    "MR-S-005": (830011, "2026年7月劳务纠纷处理情况统计表", "S"),
    "MR-S-006": (830012, "2026年7月群众诉求处理情况统计表", "S"),
    "MR-G-001": (830013, "2026年7月报批报建事项进度台账", "G"),
    "MR-G-003": (830014, "2026年7月许可状态及临期续办台账", "G"),
    "MR-G-005": (830015, "2026年7月检查及NCR整改事项台账", "G"),
    "MR-G-006": (830016, "2026年7月NCR及检查整改关闭资料汇总", "G"),
    "MR-X-002": (830017, "2026年7月施工月报功能验证资料包", "G"),
    "MR-X-004": (830018, "2026年7月监理月报功能验证资料包", "G"),
}


def ensure_no_conflicts(cur) -> None:
    ids = tuple(item[0] for item in DOCUMENTS.values())
    codes = tuple(f"DEMO-MONTHLY-MATERIAL-{task_code}" for task_code in DOCUMENTS)
    cur.execute(
        f"SELECT id, document_code FROM document_record WHERE id IN ({','.join(['%s'] * len(ids))})",
        ids,
    )
    expected_by_id = {document_id: f"DEMO-MONTHLY-MATERIAL-{code}" for code, (document_id, _name, _group) in DOCUMENTS.items()}
    for row in cur.fetchall():
        if row["document_code"] != expected_by_id[int(row["id"])]:
            raise RuntimeError(f"资料ID与非本迁移记录冲突：{row}")
    cur.execute(
        f"SELECT id, document_code FROM document_record WHERE document_code IN ({','.join(['%s'] * len(codes))})",
        codes,
    )
    expected_by_code = {f"DEMO-MONTHLY-MATERIAL-{code}": document_id for code, (document_id, _name, _group) in DOCUMENTS.items()}
    for row in cur.fetchall():
        if int(row["id"]) != expected_by_code[row["document_code"]]:
            raise RuntimeError(f"资料编码与非本迁移记录冲突：{row}")


def upsert_documents_and_links(cur) -> None:
    for task_code, (document_id, document_name, module_code) in DOCUMENTS.items():
        document_code = f"DEMO-MONTHLY-MATERIAL-{task_code}"
        cur.execute(
            """
            INSERT INTO document_record
              (id, document_code, document_name, document_type, module_code, period_value,
               version_no, source_name, relation_count, validity_status, document_status,
               confirm_status, file_id, parse_job_id, responsible_unit, uploaded_at)
            SELECT %s,%s,%s,'月报任务功能验证资料',%s,'2026-07','V1',%s,1,
                   '有效','ACTIVE','CONFIRMED',NULL,NULL,t.responsible_department,'2026-08-05 10:00:00'
            FROM monthly_report_task_instance t
            WHERE t.report_cycle_id=%s AND t.source_tag=%s AND t.task_code=%s
              AND t.monthly_status='校验通过' AND t.is_demo=1
            ON DUPLICATE KEY UPDATE
              document_name=VALUES(document_name), document_type=VALUES(document_type),
              module_code=VALUES(module_code), period_value=VALUES(period_value),
              source_name=VALUES(source_name), relation_count=1,
              validity_status='有效', document_status='ACTIVE', confirm_status='CONFIRMED',
              file_id=NULL, parse_job_id=NULL, responsible_unit=VALUES(responsible_unit),
              uploaded_at=VALUES(uploaded_at)
            """,
            (document_id, document_code, document_name, module_code, NOTICE, CYCLE_ID, SOURCE_TAG, task_code),
        )
        cur.execute(
            """
            UPDATE monthly_report_task_material_link l
            JOIN monthly_report_task_instance t ON t.id=l.task_instance_id
            SET l.document_id=%s, l.relation_status='LINKED', l.data_nature='demo', l.is_demo=1
            WHERE t.report_cycle_id=%s AND t.source_tag=%s AND t.task_code=%s
              AND t.monthly_status='校验通过' AND t.is_demo=1
              AND l.link_code=%s
            """,
            (document_id, CYCLE_ID, SOURCE_TAG, task_code, f"DEMO-MONTHLY-MATERIAL-{task_code}"),
        )


def write_trace(cur) -> None:
    cur.execute(
        """
        INSERT INTO audit_log
          (id,module_name,entity_type,entity_id,action,action_desc,operator_name)
        VALUES
          (790020,'MONTHLY_REPORT','demo_material_evidence','20260719-monthly-validated-material-v0.1',
           'UPSERT','为18项校验通过任务补齐稳定演示资料实例及任务—资料—校验链；4项待处理未修改',
           'Codex migration')
        ON DUPLICATE KEY UPDATE action_desc=VALUES(action_desc),operator_name=VALUES(operator_name)
        """
    )


def verify(cur) -> dict:
    cur.execute(
        """
        SELECT COUNT(*) total,
               SUM(t.monthly_status='校验通过') passed,
               SUM(t.monthly_status='待提交') pending_submit,
               SUM(t.monthly_status='待确认') pending_confirm,
               SUM(t.monthly_status='待补正') pending_correction,
               SUM(t.monthly_status='校验通过' AND l.document_id IS NOT NULL
                   AND l.relation_status='LINKED' AND d.id IS NOT NULL
                   AND v.validation_result='校验通过' AND v.validated_at IS NOT NULL) consistent_passed,
               SUM(t.monthly_status<>'校验通过' AND l.document_id IS NOT NULL) pending_with_docs
        FROM monthly_report_task_instance t
        LEFT JOIN monthly_report_task_material_link l ON l.task_instance_id=t.id
        LEFT JOIN document_record d ON d.id=l.document_id
        LEFT JOIN monthly_report_task_validation v ON v.task_instance_id=t.id
        WHERE t.report_cycle_id=%s AND t.source_tag=%s AND t.include_in_denominator=1
        """,
        (CYCLE_ID, SOURCE_TAG),
    )
    row = cur.fetchone()
    actual = tuple(int(row[key] or 0) for key in (
        "total", "passed", "pending_submit", "pending_confirm", "pending_correction",
        "consistent_passed", "pending_with_docs",
    ))
    expected = (22, 18, 1, 1, 2, 18, 0)
    if actual != expected:
        raise RuntimeError(f"月报资料一致性校验失败：{actual}")
    cur.execute("SELECT COUNT(*) n FROM document_record WHERE document_code LIKE 'DEMO-MONTHLY-MATERIAL-MR-%%'")
    document_count = int(cur.fetchone()["n"])
    if document_count != 18:
        raise RuntimeError(f"月报演示资料实例数量异常：{document_count}")
    return {"statusSummary": actual[:5], "consistentPassed": actual[5], "pendingWithDocs": actual[6], "documents": document_count}


def main() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            ensure_no_conflicts(cur)
            upsert_documents_and_links(cur)
            write_trace(cur)
            result = verify(cur)
    print(f"[PASS] 月报校验通过资料证据迁移完成（幂等）：{result}")


if __name__ == "__main__":
    main()
