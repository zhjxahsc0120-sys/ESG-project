from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from monthly_report_overview import get_monthly_report_overview
from mysql_db import mysql_connect


MIGRATION = Path(__file__).resolve().parent / "migrations" / "20260719_monthly_validated_material_evidence_v0_1.py"
PENDING = {"MR-G-007": "待提交", "MR-G-011": "待确认", "MR-E-010": "待补正", "MR-G-004": "待补正"}
PLACEHOLDERS = {"张三", "李四", "王五", "赵六", "钱七", "孙八"}


def query_one(sql: str) -> dict:
    with mysql_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()


def load_migration():
    spec = importlib.util.spec_from_file_location("monthly_material_evidence_migration", MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load evidence migration")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def counts() -> dict:
    return {
        "documents": int(query_one("SELECT COUNT(*) n FROM document_record WHERE document_code LIKE 'DEMO-MONTHLY-MATERIAL-MR-%'")["n"]),
        "linked": int(query_one("SELECT COUNT(*) n FROM monthly_report_task_material_link WHERE document_id IS NOT NULL AND relation_status='LINKED' AND is_demo=1")["n"]),
        "links": int(query_one("SELECT COUNT(*) n FROM monthly_report_task_material_link WHERE is_demo=1")["n"]),
        "validations": int(query_one("SELECT COUNT(*) n FROM monthly_report_task_validation WHERE is_demo=1")["n"]),
        "audit": int(query_one("SELECT COUNT(*) n FROM audit_log WHERE id=790020")["n"]),
        "g04": int(query_one("SELECT COUNT(*) n FROM compliance_material_gap")["n"]),
    }


def main() -> int:
    migration = load_migration()
    before = counts()
    migration.main()
    once = counts()
    migration.main()
    twice = counts()
    assert once == twice
    assert before["g04"] == once["g04"]
    assert once == {"documents": 18, "linked": 18, "links": 22, "validations": 22, "audit": 1, "g04": before["g04"]}

    overview = get_monthly_report_overview("2026-07")
    assert overview is not None
    assert overview["summary"] == {
        "collectedCount": 18, "totalCount": 22, "pendingSubmitCount": 1,
        "pendingConfirmCount": 1, "pendingCorrectionCount": 2,
        "pendingTotal": 4, "notApplicableCount": 0,
    }
    passed = [task for task in overview["taskInstances"] if task["status"] == "校验通过"]
    pending = [task for task in overview["taskInstances"] if task["status"] != "校验通过"]
    assert len(passed) == 18 and len(pending) == 4
    for task in passed:
        assert task["requiredMaterialCount"] == 1
        assert task["linkedMaterialCount"] == 1
        assert len(task["linkedMaterials"]) == 1
        material = task["linkedMaterials"][0]
        assert material["id"] and material["documentCode"] and material["documentName"]
        assert material["relationStatus"] == "LINKED" and material["dataNature"] == "demo"
        assert material["documentName"] not in PLACEHOLDERS
        assert task["validationId"] and task["validationResult"] == "校验通过"
        assert task["lastValidationAt"] == "2026-08-05 12:00:00"
        assert task["materialChain"]["status"] == "LINKED"
        assert task["materialChain"]["linkedDocumentIds"] == [material["id"]]
    for task in pending:
        assert PENDING[task["taskCode"]] == task["status"] == task["validationResult"]
        assert task["requiredMaterialCount"] == 1 and task["linkedMaterialCount"] == 0
        assert task["linkedMaterials"] == [] and task["lastValidationAt"] is None
        assert task["materialChain"]["status"] == "UNLINKED"

    print("[PASS] 月报18项通过任务资料证据链一致，4项待处理及冻结统计保持不变。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 月报资料证据一致性测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
