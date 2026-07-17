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


def kpi_value(kpis: dict, key: str) -> int:
    for group in kpis.get("groups", []):
        for item in group.get("items", []):
            if item.get("key") == key:
                return int(item.get("value") or 0)
    raise AssertionError(f"kpi missing: {key}")


def summary_value(detail: dict, label: str) -> int:
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return int(item.get("value") or 0)
    raise AssertionError(f"summary label missing: {label}")


def main() -> int:
    reset_acceptance_baseline()

    try:
        before_kpis = get_json("/api/dashboard/kpis")
        before_e03 = kpi_value(before_kpis, "E03")
        before_detail = get_json("/api/dashboard/kpi/E03")
        before_open = summary_value(before_detail, "当前未闭环")
        assert_true(before_e03 == 7 and before_open == 7, f"E03 baseline should be 7, got card={before_e03}, detail={before_open}")

        token = uuid.uuid4().hex.encode("ascii")
        content = b"%PDF-1.4\ningestion-dashboard-refresh-" + token + b"\n%%EOF\n"
        uploaded = post_multipart_upload("水保监测月报_2026-07_首页联动验收.pdf", content)
        parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
        job_id = parse_job["jobId"]

        confirmed = post_json(
            f"/api/workspace/parse-jobs/{job_id}/confirm",
            {
                "confirmedFields": [
                    {"fieldKey": "document_type", "confirmedValue": "水保监测月报"},
                    {"fieldKey": "period", "confirmedValue": "2026-07"},
                ],
                "acceptedCandidateIds": [],
                "operatorId": 10001,
                "operatorName": "项目管理员",
                "comment": "首页指标动态刷新验收",
            },
        )
        assert_true(confirmed.get("targetTable") == "water_protection_issue", "confirmed record should sync to water_protection_issue")

        after_kpis = get_json("/api/dashboard/kpis")
        after_e03 = kpi_value(after_kpis, "E03")
        after_detail = get_json("/api/dashboard/kpi/E03")
        after_open = summary_value(after_detail, "当前未闭环")

        assert_true(after_e03 == before_e03 + 1, f"E03 card should increase by 1, before={before_e03}, after={after_e03}")
        assert_true(after_open == before_open + 1, f"E03 detail should increase by 1, before={before_open}, after={after_open}")

        print("✅ 智能入库驱动首页指标动态刷新验收通过：水保资料确认入库后 E03 从 7 增至 8。")
        return 0
    finally:
        reset_acceptance_baseline()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 智能入库驱动首页指标动态刷新验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

