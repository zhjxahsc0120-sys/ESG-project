from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402


def existing_columns() -> set[str]:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW COLUMNS FROM env_monitoring_record")
            return {row["Field"] for row in cur.fetchall()}


def ensure_value_columns() -> None:
    columns = existing_columns()
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            if "initial_detected_value" not in columns:
                cur.execute(
                    "ALTER TABLE env_monitoring_record "
                    "ADD COLUMN initial_detected_value VARCHAR(50) NULL COMMENT '初检值' "
                    "AFTER detected_value"
                )
            if "recheck_detected_value" not in columns:
                cur.execute(
                    "ALTER TABLE env_monitoring_record "
                    "ADD COLUMN recheck_detected_value VARCHAR(50) NULL COMMENT '复测值' "
                    "AFTER initial_detected_value"
                )


def migrate_confirmed_demo_values() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE env_monitoring_record
                SET initial_detected_value = NULL,
                    recheck_detected_value = '68.2 dB(A)',
                    detected_value = NULL,
                    exceed_multiple = NULL
                WHERE id = 410001
                  AND monitor_type = '噪声'
                """
            )
            cur.execute(
                """
                UPDATE indicator_result
                SET label = '环境监测超标项次',
                    full_name = '环境监测超标项次',
                    unit = '项次'
                WHERE indicator_code = 'E01'
                """
            )
            cur.execute(
                """
                UPDATE env_monitoring_record
                SET initial_detected_value = COALESCE(initial_detected_value, detected_value),
                    recheck_detected_value = NULL
                WHERE id IN (410002, 410003)
                """
            )


def main() -> int:
    ensure_value_columns()
    migrate_confirmed_demo_values()
    print("[PASS] E01 初检值/复测值字段已迁移，68.2 dB(A) 已归入复测值。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
