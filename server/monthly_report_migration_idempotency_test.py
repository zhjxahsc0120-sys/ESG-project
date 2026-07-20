from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from mysql_db import mysql_connect


MIGRATION = Path(__file__).resolve().parent / "migrations" / "20260719_monthly_report_data_contract_v0_1.py"
EVIDENCE_MIGRATION = Path(__file__).resolve().parent / "migrations" / "20260719_monthly_validated_material_evidence_v0_1.py"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def query_one(sql: str) -> dict:
    with mysql_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()


def load_migration(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load monthly report migration")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot() -> dict:
    return {
        "tasks": query_one("SELECT COUNT(*) AS n FROM monthly_report_task_instance WHERE source_tag = 'V0.2_TEST'")["n"],
        "links": query_one("SELECT COUNT(*) AS n FROM monthly_report_task_material_link WHERE is_demo = 1")["n"],
        "validations": query_one("SELECT COUNT(*) AS n FROM monthly_report_task_validation WHERE is_demo = 1")["n"],
        "documents": query_one("SELECT COUNT(*) AS n FROM document_record WHERE document_code LIKE 'DEMO-MONTHLY-MATERIAL-MR-%'")["n"],
        "linked": query_one("SELECT COUNT(*) AS n FROM monthly_report_task_material_link WHERE is_demo=1 AND relation_status='LINKED' AND document_id IS NOT NULL")["n"],
        "placeholders": query_one(
            "SELECT COUNT(*) AS n FROM monthly_report_chapter "
            "WHERE responsible_person IN ('张三','李四','王五','赵六','钱七','孙八')"
        )["n"],
        "g04": query_one("SELECT COUNT(*) AS n FROM compliance_material_gap")["n"],
    }


def main() -> int:
    module = load_migration(MIGRATION, "monthly_report_contract_migration")
    evidence_module = load_migration(EVIDENCE_MIGRATION, "monthly_report_evidence_migration")
    before = snapshot()
    module.main()
    evidence_module.main()
    once = snapshot()
    module.main()
    evidence_module.main()
    twice = snapshot()
    assert_true(once == twice, f"migration is not idempotent: {once} != {twice}")
    assert_true(once["tasks"] == 22 and once["links"] == 22 and once["validations"] == 22, "seed counts mismatch")
    assert_true(once["documents"] == 18 and once["linked"] == 18, "validated material evidence counts mismatch")
    assert_true(once["placeholders"] == 0, "placeholder names remain")
    assert_true(before["g04"] == once["g04"] == twice["g04"], "migration changed G04 rows")
    print(f"[PASS] 月报迁移连续执行两次幂等，G04行数保持{twice['g04']}。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 月报迁移幂等测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
