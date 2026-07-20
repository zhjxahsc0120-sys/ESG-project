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
    content = b"%PDF-1.4\nsocial-kpi-refresh-" + token + b"\n%%EOF\n"
    uploaded = post_multipart_upload(filename, content)
    parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    return post_json(
        f"/api/workspace/parse-jobs/{parse_job['jobId']}/confirm",
        {
            "confirmedFields": confirmed_fields,
            "acceptedCandidateIds": [],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "S03/S04 动态刷新验收",
        },
    )


def main() -> int:
    reset_acceptance_baseline()

    try:
        before_s03 = kpi_value("S03")
        before_s04 = kpi_value("S04")
        assert_true(before_s03 == 4, f"S03 baseline should be 4, got {before_s03}")
        assert_true(before_s04 == 3, f"S04 baseline should be 3, got {before_s04}")
        assert_true(summary_value(get_json("/api/dashboard/kpi/S03"), "未办结纠纷") == before_s03, "S03 detail baseline mismatch")
        assert_true(summary_value(get_json("/api/dashboard/kpi/S04"), "未办结诉求") == before_s04, "S04 detail baseline mismatch")

        s03_confirmed = upload_parse_confirm(
            "劳务纠纷台账_2026-07_S03联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "劳务纠纷台账_2026年7月新增欠薪纠纷"},
                {"fieldKey": "document_type", "confirmedValue": "劳务纠纷台账"},
                {"fieldKey": "esg_module", "confirmedValue": "S"},
                {"fieldKey": "dispute_name", "confirmedValue": "新增班组欠薪协调事项"},
                {"fieldKey": "dispute_type", "confirmedValue": "工资支付"},
                {"fieldKey": "dispute_status", "confirmedValue": "协调中"},
                {"fieldKey": "involved_people", "confirmedValue": "5"},
                {"fieldKey": "amount_wan", "confirmedValue": "12"},
                {"fieldKey": "occurred_date", "confirmedValue": "2026-07-13"},
                {"fieldKey": "responsible_department", "confirmedValue": "财务管理部"},
            ],
        )
        assert_true(s03_confirmed.get("targetTable") == "labor_dispute_record", "S03 should sync to labor_dispute_record")
        assert_true(kpi_value("S03") == before_s03 + 1, "S03 card should increase by 1")
        s03_detail = get_json("/api/dashboard/kpi/S03")
        assert_true(summary_value(s03_detail, "未办结纠纷") == before_s03 + 1, "S03 detail should increase by 1")
        assert_true(summary_value(s03_detail, "涉及人数") == 23, "S03 involved people should include new dispute")
        assert_true(summary_value(s03_detail, "涉及金额") == 80, "S03 amount should include new dispute")

        s04_confirmed = upload_parse_confirm(
            "群众诉求台账_2026-07_S04联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "群众诉求台账_2026年7月新增投诉"},
                {"fieldKey": "document_type", "confirmedValue": "群众诉求台账"},
                {"fieldKey": "esg_module", "confirmedValue": "S"},
                {"fieldKey": "appeal_content", "confirmedValue": "新增施工便道扬尘投诉"},
                {"fieldKey": "appeal_type", "confirmedValue": "扬尘投诉"},
                {"fieldKey": "appeal_status", "confirmedValue": "办理中"},
                {"fieldKey": "source_channel", "confirmedValue": "12345热线"},
                {"fieldKey": "accepted_date", "confirmedValue": "2026-07-13"},
                {"fieldKey": "location", "confirmedValue": "K20+000 施工便道"},
                {"fieldKey": "deadline", "confirmedValue": "2026-07-20"},
                {"fieldKey": "duration_days", "confirmedValue": "7"},
            ],
        )
        assert_true(s04_confirmed.get("targetTable") == "appeal_record", "S04 should sync to appeal_record")
        assert_true(kpi_value("S04") == before_s04 + 1, "S04 card should increase by 1")
        assert_true(summary_value(get_json("/api/dashboard/kpi/S04"), "未办结诉求") == before_s04 + 1, "S04 detail should increase by 1")

        print("✅ S03/S04 资料入库驱动首页指标动态刷新验收通过。")
        return 0
    finally:
        reset_acceptance_baseline()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ S03/S04 资料入库驱动首页指标动态刷新验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
