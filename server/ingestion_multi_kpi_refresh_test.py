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
    content = b"%PDF-1.4\nmulti-kpi-refresh-" + token + b"\n%%EOF\n"
    uploaded = post_multipart_upload(filename, content)
    parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    return post_json(
        f"/api/workspace/parse-jobs/{parse_job['jobId']}/confirm",
        {
            "confirmedFields": confirmed_fields,
            "acceptedCandidateIds": [],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "多指标动态刷新验收",
        },
    )


def main() -> int:
    reset_acceptance_baseline()

    try:
        before_e02 = kpi_value("E02")
        before_s02 = kpi_value("S02")
        before_g03 = kpi_value("G03")
        assert_true(before_e02 == 5, f"E02 baseline should be 5, got {before_e02}")
        assert_true(before_s02 == 6, f"S02 baseline should be 6, got {before_s02}")
        assert_true(before_g03 == 6, f"G03 baseline should be 6, got {before_g03}")

        e02_confirmed = upload_parse_confirm(
            "环保问题整改资料_2026-07_首页联动验收.pdf",
            [
                {"fieldKey": "document_type", "confirmedValue": "环保问题整改资料"},
                {"fieldKey": "issue_name", "confirmedValue": "施工便道扬尘覆盖不到位"},
                {"fieldKey": "issue_status", "confirmedValue": "整改中"},
            ],
        )
        assert_true(e02_confirmed.get("targetTable") == "env_issue_record", "E02 should sync to env_issue_record")
        after_e02_card = kpi_value("E02")
        after_e02_detail = summary_value(get_json("/api/dashboard/kpi/E02"), "当前未闭环")
        assert_true(after_e02_card == before_e02 + 1, f"E02 card should increase by 1, got {after_e02_card}")
        assert_true(after_e02_detail == before_e02 + 1, f"E02 detail should increase by 1, got {after_e02_detail}")

        s02_confirmed = upload_parse_confirm(
            "高风险作业审批资料_2026-07_首页联动验收.pdf",
            [
                {"fieldKey": "document_type", "confirmedValue": "高风险作业审批资料"},
                {"fieldKey": "risk_level", "confirmedValue": "较大"},
                {"fieldKey": "work_location", "confirmedValue": "K36+200 高边坡"},
            ],
        )
        assert_true(s02_confirmed.get("targetTable") == "safety_risk_point", "S02 should sync to safety_risk_point")
        after_s02_card = kpi_value("S02")
        s02_detail = get_json("/api/dashboard/kpi/S02")
        after_s02_detail = summary_value(s02_detail, "较大风险点") + summary_value(s02_detail, "重大风险点")
        assert_true(after_s02_card == before_s02 + 1, f"S02 card should increase by 1, got {after_s02_card}")
        assert_true(after_s02_detail == before_s02 + 1, f"S02 detail should increase by 1, got {after_s02_detail}")

        g03_confirmed = upload_parse_confirm(
            "NCR整改关闭资料_2026-07_首页联动验收.pdf",
            [
                {"fieldKey": "document_type", "confirmedValue": "NCR整改关闭资料"},
                {"fieldKey": "rectification_item", "confirmedValue": "钢筋加工区整改资料待复查"},
                {"fieldKey": "rectification_status", "confirmedValue": "待复查"},
            ],
        )
        assert_true(g03_confirmed.get("targetTable") == "rectification_record", "G03 should sync to rectification_record")
        after_g03_card = kpi_value("G03")
        after_g03_detail = summary_value(get_json("/api/dashboard/kpi/G03"), "未关闭事项")
        assert_true(after_g03_card == before_g03 + 1, f"G03 card should increase by 1, got {after_g03_card}")
        assert_true(after_g03_detail == before_g03 + 1, f"G03 detail should increase by 1, got {after_g03_detail}")

        print("✅ E02/S02/G03 资料入库驱动首页指标动态刷新验收通过。")
        return 0
    finally:
        reset_acceptance_baseline()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ E02/S02/G03 资料入库驱动首页指标动态刷新验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
