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


def upload_parse_confirm(filename: str, confirmed_fields: list[dict]) -> dict:
    token = uuid.uuid4().hex.encode("ascii")
    content = b"%PDF-1.4\ns01-safety-production-business-" + token + b"\n%%EOF\n"
    uploaded = post_multipart_upload(filename, content)
    parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    return post_json(
        f"/api/workspace/parse-jobs/{parse_job['jobId']}/confirm",
        {
            "confirmedFields": confirmed_fields,
            "acceptedCandidateIds": [],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "S01 安全生产周期业务表化验收",
        },
    )


def main() -> int:
    reset_acceptance_baseline()

    try:
        baseline = get_json("/api/dashboard/kpi/S01")
        assert_true(baseline.get("continuousDays") == 368, f"S01 baseline should be 368, got {baseline.get('continuousDays')}")
        assert_true(baseline.get("countingStatus") == "continuous", "S01 baseline should be continuous")
        assert_true(baseline.get("latestInterruptDate") is None, "S01 baseline should not have interrupt date")
        assert_true(len(baseline.get("constructionStages") or []) == 4, "S01 should expose 4 construction stages")
        assert_true(kpi_value("S01") == 368, "S01 dashboard card should be 368 at baseline")

        confirmed = upload_parse_confirm(
            "安全事故台账_2026-07_S01联动验收.pdf",
            [
                {"fieldKey": "document_name", "confirmedValue": "安全事故台账_2026年7月中断记录"},
                {"fieldKey": "document_type", "confirmedValue": "安全事故台账"},
                {"fieldKey": "esg_module", "confirmedValue": "S"},
                {"fieldKey": "incident_date", "confirmedValue": "2026-07-01"},
                {"fieldKey": "incident_name", "confirmedValue": "高处作业一般安全事故"},
                {"fieldKey": "incident_type", "confirmedValue": "安全生产事故"},
                {"fieldKey": "incident_level", "confirmedValue": "一般"},
                {"fieldKey": "interrupt_counting", "confirmedValue": "1"},
                {"fieldKey": "interrupt_reason", "confirmedValue": "触发连续安全生产记录中断条件"},
                {"fieldKey": "responsible_department", "confirmedValue": "安全环保部"},
            ],
        )
        assert_true(confirmed.get("targetTable") == "safety_incident_record", "S01 should sync to safety_incident_record")

        interrupted = get_json("/api/dashboard/kpi/S01")
        assert_true(interrupted.get("continuousDays") == 12, f"S01 should recalculate to 12 after 2026-07-01 incident, got {interrupted.get('continuousDays')}")
        assert_true(interrupted.get("countingStatus") == "interrupted", "S01 should mark interrupted after an interrupt incident")
        assert_true(interrupted.get("latestInterruptDate") == "2026-07-01", "S01 should expose latest interrupt date")
        assert_true("事故后新一轮连续安全生产12天" in interrupted.get("conclusion", ""), "S01 conclusion should explain new cycle after incident")
        assert_true(kpi_value("S01") == 12, "S01 dashboard card should use recalculated continuous days")

        print("✅ S01 安全生产周期业务表化验收通过：事故台账可驱动连续天数重新累计。")
        return 0
    finally:
        reset_acceptance_baseline()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ S01 安全生产周期业务表化验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
