from __future__ import annotations

import json
import sys
import uuid
from urllib.request import Request, urlopen

from multipart_upload_test import post_multipart_upload
from reset_acceptance_baseline import main as reset_acceptance_baseline


BASE_URL = "http://127.0.0.1:8765"


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def kpi_value(key: str) -> int:
    kpis = get_json("/api/dashboard/kpis")
    for group in kpis.get("groups", []):
        for item in group.get("items", []):
            if item.get("key") == key:
                return int(round(float(item.get("value") or 0)))
    raise AssertionError(f"kpi missing: {key}")


def summary_value(detail: dict, label: str) -> int:
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return int(round(float(item.get("value") or 0)))
    raise AssertionError(f"summary label missing: {label}")


def upload_parse_confirm(filename: str, confirmed_fields: list[dict]) -> dict:
    token = uuid.uuid4().hex.encode("ascii")
    content = b"%PDF-1.4\nmore-kpi-refresh-" + token + b"\n%%EOF\n"
    uploaded = post_multipart_upload(filename, content)
    parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    return post_json(
        f"/api/workspace/parse-jobs/{parse_job['jobId']}/confirm",
        {
            "confirmedFields": confirmed_fields,
            "acceptedCandidateIds": [],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "E01/G01/G02/G04 动态刷新验收",
        },
    )


def assert_detail_count(key: str, label: str, expected: int) -> None:
    actual = summary_value(get_json(f"/api/dashboard/kpi/{key}"), label)
    assert_true(actual == expected, f"{key} detail {label} should be {expected}, got {actual}")


def main() -> int:
    reset_acceptance_baseline()

    try:
        before_e01 = kpi_value("E01")
        before_g01 = kpi_value("G01")
        before_g02 = kpi_value("G02")
        before_g04 = kpi_value("G04")

        assert_true(before_e01 == 2, f"E01 baseline should be 2, got {before_e01}")
        assert_true(before_g01 == 5, f"G01 baseline should be 5, got {before_g01}")
        assert_true(before_g02 == 5, f"G02 baseline should be 5, got {before_g02}")
        assert_true(before_g04 == 4, f"G04 baseline should be 4, got {before_g04}")
        assert_detail_count("E01", "本月超标项次", before_e01)
        assert_detail_count("G01", "未完成事项", before_g01)
        g02_detail = get_json("/api/dashboard/kpi/G02")
        assert_true(
            summary_value(g02_detail, "临期许可") + summary_value(g02_detail, "逾期许可") == before_g02,
            "G02 detail baseline should equal card value",
        )
        assert_detail_count("G04", "待补齐资料", before_g04)

        e01_confirmed = upload_parse_confirm(
            "环境监测报告_2026-07_E01联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "环境监测报告_2026年7月扬尘超标记录"},
                {"fieldKey": "document_type", "confirmedValue": "环境监测报告"},
                {"fieldKey": "esg_module", "confirmedValue": "E"},
                {"fieldKey": "monitor_type", "confirmedValue": "扬尘"},
                {"fieldKey": "dust_exceed_count", "confirmedValue": "1"},
                {"fieldKey": "noise_exceed_count", "confirmedValue": "0"},
                {"fieldKey": "monitor_point", "confirmedValue": "K30+000 拌合站监测点"},
            ],
        )
        assert_true(e01_confirmed.get("targetTable") == "env_monitoring_record", "E01 should sync to env_monitoring_record")
        assert_true(kpi_value("E01") == before_e01 + 1, "E01 card should increase by 1")
        assert_detail_count("E01", "本月超标项次", before_e01 + 1)

        g02_confirmed = upload_parse_confirm(
            "临时用地许可资料_2026-07_G02联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "临时用地许可资料_2026年7月临期记录"},
                {"fieldKey": "document_type", "confirmedValue": "临时用地合规资料"},
                {"fieldKey": "esg_module", "confirmedValue": "G"},
                {"fieldKey": "permit_name", "confirmedValue": "临时施工便道占用许可"},
                {"fieldKey": "permit_expire_date", "confirmedValue": "2026-07-25"},
            ],
        )
        assert_true(g02_confirmed.get("targetTable") == "permit_record", "G02 should sync to permit_record")
        assert_true(kpi_value("G02") == before_g02 + 1, "G02 card should increase by 1")
        g02_after_detail = get_json("/api/dashboard/kpi/G02")
        assert_true(
            summary_value(g02_after_detail, "临期许可") + summary_value(g02_after_detail, "逾期许可") == before_g02 + 1,
            "G02 detail should increase by 1",
        )

        g01_confirmed = upload_parse_confirm(
            "报批报建资料_2026-07_G01联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "报批报建资料_2026年7月未完成手续"},
                {"fieldKey": "document_type", "confirmedValue": "报批报建资料"},
                {"fieldKey": "esg_module", "confirmedValue": "G"},
                {"fieldKey": "procedure_name", "confirmedValue": "施工便道临时占用手续"},
                {"fieldKey": "procedure_status", "confirmedValue": "待批复"},
            ],
        )
        assert_true(g01_confirmed.get("targetTable") == "compliance_procedure", "G01 should sync to compliance_procedure")
        assert_true(kpi_value("G01") == before_g01 + 1, "G01 card should increase by 1")
        assert_detail_count("G01", "未完成事项", before_g01 + 1)

        g04_confirmed = upload_parse_confirm(
            "合规资料补齐材料_2026-07_G04联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "合规资料补齐材料_2026年7月"},
                {"fieldKey": "document_type", "confirmedValue": "合规资料补齐材料"},
                {"fieldKey": "esg_module", "confirmedValue": "G"},
                {"fieldKey": "material_name", "confirmedValue": "安全生产费用使用台账"},
            ],
        )
        assert_true(g04_confirmed.get("targetTable") == "compliance_material_gap", "G04 should sync to compliance_material_gap")
        g04_operation = (g04_confirmed.get("businessRecords") or [{}])[0].get("operationType")
        assert_true(g04_operation == "UPDATE", "G04 should update an existing material gap")
        assert_true(kpi_value("G04") == before_g04 - 1, "G04 card should decrease by 1 after material completion")
        assert_detail_count("G04", "待补齐资料", before_g04 - 1)

        print("✅ E01/G02/G01/G04 资料入库驱动首页指标动态刷新验收通过。")
        return 0
    finally:
        reset_acceptance_baseline()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ E01/G02/G01/G04 资料入库驱动首页指标动态刷新验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
