from __future__ import annotations

"""E04 演示核算数据迁移 V0.1。

本迁移只更新既有 720001~720006 E04 演示月度记录，并使用固定主键
幂等补充演示排放因子和材料分项。所有因子均明确标记为 demo / 待业务核验，
不代表正式工程核算依据。
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mysql_db import mysql_connect  # noqa: E402


getcontext().prec = 32

DEMO_VERSION = "DEMO-EF-2026-v0.1"
DEMO_SOURCE = "系统演示测试数据，非正式核算依据"
DEMO_NATURE = "demo"
VERIFICATION_STATUS = "待业务核验"
DEMO_NOTE = "E04界面和数据链测试使用，不代表正式工程核算结果"
E04_ACTIVITY_IDS = tuple(range(720001, 720007))
PERIODS = ("2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07")


@dataclass(frozen=True)
class FactorSeed:
    id: int
    code: str
    name: str
    value: Decimal
    unit: str


FACTORS = (
    FactorSeed(740001, "DEMO_DIESEL", "施工用油演示排放因子", Decimal("2.68"), "kgCO₂e/L"),
    FactorSeed(740002, "DEMO_ELECTRICITY", "施工用电演示排放因子", Decimal("0.57"), "kgCO₂e/kWh"),
    FactorSeed(740003, "DEMO_CEMENT", "水泥演示排放因子", Decimal("0.800"), "tCO₂e/t"),
    FactorSeed(740004, "DEMO_STEEL", "钢材演示排放因子", Decimal("0.750"), "tCO₂e/t"),
    FactorSeed(740005, "DEMO_ASPHALT", "沥青演示排放因子", Decimal("0.680"), "tCO₂e/t"),
    FactorSeed(740006, "DEMO_TRANSPORT", "施工运输演示排放因子", Decimal("0.000885"), "tCO₂e/(t·km)"),
)

MATERIALS = (
    ("水泥", Decimal("2000"), Decimal("1600"), 740003),
    ("钢材", Decimal("1000"), Decimal("750"), 740004),
    ("沥青", Decimal("200"), Decimal("136"), 740005),
)


def column_names(cur, table: str) -> set[str]:
    cur.execute(f"SHOW COLUMNS FROM `{table}`")
    return {row["Field"] for row in cur.fetchall()}


def add_column(cur, table: str, column: str, ddl: str, changes: list[str]) -> None:
    if column in column_names(cur, table):
        return
    cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}")
    changes.append(f"{table}.{column}")


def ensure_schema(cur) -> list[str]:
    changes: list[str] = []
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS carbon_emission_factor (
          id BIGINT PRIMARY KEY,
          factor_code VARCHAR(60) NOT NULL UNIQUE,
          factor_name VARCHAR(160) NOT NULL,
          factor_value DECIMAL(24,12) NOT NULL,
          factor_unit VARCHAR(80) NOT NULL,
          factor_version VARCHAR(80) NOT NULL,
          factor_source VARCHAR(255) NOT NULL,
          data_nature VARCHAR(30) NOT NULL,
          verification_status VARCHAR(40) NOT NULL,
          evidence_document_id BIGINT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          INDEX idx_carbon_factor_nature(data_nature)
        ) ENGINE=InnoDB COMMENT='碳排放因子元数据（含演示测试因子）'
        """
    )

    activity_columns = {
        "diesel_unit": "VARCHAR(30) NULL COMMENT '施工用油活动单位'",
        "electricity_unit": "VARCHAR(30) NULL COMMENT '施工用电活动单位'",
        "transport_usage": "DECIMAL(24,8) NULL COMMENT '施工运输活动量'",
        "transport_unit": "VARCHAR(30) NULL COMMENT '施工运输活动单位'",
        "diesel_factor_id": "BIGINT NULL COMMENT '施工用油排放因子ID'",
        "electricity_factor_id": "BIGINT NULL COMMENT '施工用电排放因子ID'",
        "transport_factor_id": "BIGINT NULL COMMENT '施工运输排放因子ID'",
        "data_nature": "VARCHAR(30) NULL COMMENT '数据性质'",
        "verification_status": "VARCHAR(40) NULL COMMENT '核验状态'",
        "demo_note": "VARCHAR(255) NULL COMMENT '演示数据说明'",
        "updated_at": "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",
    }
    for column, ddl in activity_columns.items():
        add_column(cur, "carbon_emission_activity", column, ddl, changes)

    material_columns = {
        "carbon_activity_id": "BIGINT NULL COMMENT '关联月度碳排活动记录ID'",
        "emission_factor_id": "BIGINT NULL COMMENT '排放因子ID'",
        "carbon_emission": "DECIMAL(18,6) NULL COMMENT '材料分项排放量，tCO₂e'",
        "data_nature": "VARCHAR(30) NULL COMMENT '数据性质'",
        "verification_status": "VARCHAR(40) NULL COMMENT '核验状态'",
        "demo_note": "VARCHAR(255) NULL COMMENT '演示数据说明'",
        "updated_at": "DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",
    }
    for column, ddl in material_columns.items():
        add_column(cur, "carbon_material_usage", column, ddl, changes)

    # 保留足够的小数精度，避免月度反算后累计值受四位小数限制。
    cur.execute("ALTER TABLE carbon_emission_activity MODIFY diesel_usage DECIMAL(24,8) NULL")
    cur.execute("ALTER TABLE carbon_emission_activity MODIFY electricity_usage DECIMAL(24,8) NULL")
    cur.execute("ALTER TABLE carbon_emission_activity MODIFY material_usage DECIMAL(24,8) NULL")
    cur.execute("ALTER TABLE carbon_material_usage MODIFY material_usage DECIMAL(24,8) NULL")
    return changes


def load_demo_activity_rows(cur) -> list[dict]:
    placeholders = ",".join(["%s"] * len(E04_ACTIVITY_IDS))
    cur.execute(
        f"""
        SELECT id, period_value, carbon_emission,
               diesel_emission, electricity_emission, material_emission, other_emission
        FROM carbon_emission_activity
        WHERE id IN ({placeholders})
        ORDER BY period_value, id
        """,
        E04_ACTIVITY_IDS,
    )
    rows = cur.fetchall()
    if len(rows) != 6 or tuple(row["period_value"] for row in rows) != PERIODS:
        raise RuntimeError("E04演示月度记录范围不匹配，迁移已停止")

    expected = {
        "carbon_emission": Decimal("12856"),
        "diesel_emission": Decimal("5628"),
        "electricity_emission": Decimal("3857"),
        "material_emission": Decimal("2486"),
        "other_emission": Decimal("885"),
    }
    for field, target in expected.items():
        actual = sum(Decimal(str(row[field] or 0)) for row in rows)
        if actual != target:
            raise RuntimeError(f"迁移前{field}合计应为{target}，实际为{actual}，迁移已停止")
    return rows


def distribute_by_emission(rows: list[dict], emission_field: str, factor: Decimal, target: Decimal, kg_factor: bool) -> list[Decimal]:
    scale = Decimal("1000") if kg_factor else Decimal("1")
    values: list[Decimal] = []
    for row in rows[:-1]:
        values.append((Decimal(str(row[emission_field])) * scale / factor).quantize(Decimal("0.00000001"), ROUND_HALF_UP))
    values.append(target - sum(values))
    return values


def material_allocations(rows: list[dict]) -> dict[str, list[tuple[Decimal, Decimal]]]:
    total_material_emission = Decimal("2486")
    allocations: dict[str, list[tuple[Decimal, Decimal]]] = {}
    for name, target_usage, target_emission, factor_id in MATERIALS:
        factor = next(item.value for item in FACTORS if item.id == factor_id)
        emissions: list[Decimal] = []
        for row in rows[:-1]:
            monthly = Decimal(str(row["material_emission"]))
            emissions.append((monthly * target_emission / total_material_emission).quantize(Decimal("0.000001"), ROUND_HALF_UP))
        emissions.append(target_emission - sum(emissions))

        usages: list[Decimal] = []
        for emission in emissions[:-1]:
            usages.append((emission / factor).quantize(Decimal("0.00000001"), ROUND_HALF_UP))
        usages.append(target_usage - sum(usages))
        allocations[name] = list(zip(usages, emissions))
    return allocations


def upsert_factors(cur) -> tuple[int, int]:
    inserted = updated = 0
    for item in FACTORS:
        cur.execute("SELECT id FROM carbon_emission_factor WHERE id=%s", (item.id,))
        exists = cur.fetchone() is not None
        cur.execute(
            """
            INSERT INTO carbon_emission_factor
              (id, factor_code, factor_name, factor_value, factor_unit, factor_version,
               factor_source, data_nature, verification_status, evidence_document_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)
            ON DUPLICATE KEY UPDATE
              factor_code=VALUES(factor_code), factor_name=VALUES(factor_name),
              factor_value=VALUES(factor_value), factor_unit=VALUES(factor_unit),
              factor_version=VALUES(factor_version), factor_source=VALUES(factor_source),
              data_nature=VALUES(data_nature), verification_status=VALUES(verification_status),
              evidence_document_id=NULL
            """,
            (item.id, item.code, item.name, item.value, item.unit, DEMO_VERSION,
             DEMO_SOURCE, DEMO_NATURE, VERIFICATION_STATUS),
        )
        inserted += int(not exists)
        updated += int(exists and cur.rowcount > 0)
    return inserted, updated


def update_activity_rows(cur, rows: list[dict], material_data: dict[str, list[tuple[Decimal, Decimal]]]) -> int:
    diesel_values = distribute_by_emission(rows, "diesel_emission", Decimal("2.68"), Decimal("2100000"), True)
    electricity_values = distribute_by_emission(rows, "electricity_emission", Decimal("0.57"), Decimal("6766666.67"), True)
    transport_values = distribute_by_emission(rows, "other_emission", Decimal("0.000885"), Decimal("1000000"), False)
    updated = 0
    for index, row in enumerate(rows):
        material_usage = sum(material_data[name][index][0] for name, *_ in MATERIALS)
        cur.execute(
            """
            UPDATE carbon_emission_activity
            SET diesel_usage=%s, diesel_unit='L', diesel_factor_id=740001,
                electricity_usage=%s, electricity_unit='kWh', electricity_factor_id=740002,
                material_usage=%s,
                transport_usage=%s, transport_unit='t·km', transport_factor_id=740006,
                data_nature=%s, verification_status=%s, demo_note=%s
            WHERE id=%s
            """,
            (diesel_values[index], electricity_values[index], material_usage,
             transport_values[index], DEMO_NATURE, VERIFICATION_STATUS, DEMO_NOTE, row["id"]),
        )
        updated += int(cur.rowcount > 0)
    return updated


def upsert_material_rows(cur, rows: list[dict], allocations: dict[str, list[tuple[Decimal, Decimal]]]) -> tuple[int, int]:
    inserted = updated = 0
    material_meta = {name: factor_id for name, _usage, _emission, factor_id in MATERIALS}
    record_id = 720501
    for month_index, activity in enumerate(rows):
        for name, *_ in MATERIALS:
            usage, emission = allocations[name][month_index]
            cur.execute("SELECT id FROM carbon_material_usage WHERE id=%s", (record_id,))
            exists = cur.fetchone() is not None
            cur.execute(
                """
                INSERT INTO carbon_material_usage
                  (id, document_id, period_value, material_name, material_usage, material_unit,
                   carbon_activity_id, emission_factor_id, carbon_emission,
                   data_nature, verification_status, demo_note)
                VALUES (%s,NULL,%s,%s,%s,'t',%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  document_id=NULL, period_value=VALUES(period_value), material_name=VALUES(material_name),
                  material_usage=VALUES(material_usage), material_unit='t',
                  carbon_activity_id=VALUES(carbon_activity_id), emission_factor_id=VALUES(emission_factor_id),
                  carbon_emission=VALUES(carbon_emission), data_nature=VALUES(data_nature),
                  verification_status=VALUES(verification_status), demo_note=VALUES(demo_note)
                """,
                (record_id, activity["period_value"], name, usage, activity["id"],
                 material_meta[name], emission, DEMO_NATURE, VERIFICATION_STATUS, DEMO_NOTE),
            )
            inserted += int(not exists)
            updated += int(exists and cur.rowcount > 0)
            record_id += 1
    return inserted, updated


def verify(cur) -> dict[str, Decimal | int]:
    cur.execute(
        """
        SELECT COUNT(*) AS row_count,
               SUM(diesel_usage) AS diesel_usage,
               SUM(electricity_usage) AS electricity_usage,
               SUM(transport_usage) AS transport_usage,
               SUM(diesel_emission) AS diesel_emission,
               SUM(electricity_emission) AS electricity_emission,
               SUM(material_emission) AS material_emission,
               SUM(other_emission) AS transport_emission,
               SUM(carbon_emission) AS total_emission
        FROM carbon_emission_activity
        WHERE id BETWEEN 720001 AND 720006
        """
    )
    result = cur.fetchone()
    cur.execute(
        """
        SELECT COUNT(*) AS row_count, SUM(material_usage) AS material_usage,
               SUM(carbon_emission) AS material_emission
        FROM carbon_material_usage
        WHERE id BETWEEN 720501 AND 720518 AND data_nature='demo'
        """
    )
    material = cur.fetchone()
    result.update({
        "material_row_count": material["row_count"],
        "material_usage": material["material_usage"],
        "material_detail_emission": material["material_emission"],
    })
    return result


def main() -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            schema_changes = ensure_schema(cur)
            rows = load_demo_activity_rows(cur)
            allocations = material_allocations(rows)
            factor_inserted, factor_updated = upsert_factors(cur)
            activity_updated = update_activity_rows(cur, rows, allocations)
            material_inserted, material_updated = upsert_material_rows(cur, rows, allocations)
            result = verify(cur)

    print(
        "[PASS] E04演示核算迁移完成："
        f"新增字段{len(schema_changes)}个，因子新增{factor_inserted}条/更新{factor_updated}条，"
        f"月度活动更新{activity_updated}条，材料新增{material_inserted}条/更新{material_updated}条。"
    )
    print(
        "[VERIFY] "
        f"活动记录{result['row_count']}条；用油活动量{result['diesel_usage']} L；"
        f"用电活动量{result['electricity_usage']} kWh；运输活动量{result['transport_usage']} t·km；"
        f"材料分项{result['material_row_count']}条/{result['material_usage']} t；"
        f"材料排放{result['material_detail_emission']} tCO₂e；总排放{result['total_emission']} tCO₂e。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
