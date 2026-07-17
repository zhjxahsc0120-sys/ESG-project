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
                return int(round(float(item.get("value") or 0)))
    raise AssertionError(f"kpi missing: {key}")


def summary_value(detail: dict, label: str) -> int:
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return int(round(float(item.get("value") or 0)))
    raise AssertionError(f"summary label missing: {label}")


def main() -> int:
    reset_acceptance_baseline()

    try:
        before_kpis = get_json("/api/dashboard/kpis")
        before_e04 = kpi_value(before_kpis, "E04")
        before_detail = get_json("/api/dashboard/kpi/E04")
        before_total = summary_value(before_detail, "累计碳排放")
        assert_true(before_e04 == 12856 and before_total == 12856, f"E04 baseline should be 12856, got card={before_e04}, detail={before_total}")

        token = uuid.uuid4().hex.encode("ascii")
        content = b"%PDF-1.4\ncarbon-ingestion-dashboard-refresh-" + token + b"\n%%EOF\n"
        uploaded = post_multipart_upload("碳排放活动数据表_2026-07_首页联动验收.pdf", content)
        parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
        job_id = parse_job["jobId"]

        confirmed = post_json(
            f"/api/workspace/parse-jobs/{job_id}/confirm",
            {
                "confirmedFields": [
                    {"fieldKey": "document_type", "confirmedValue": "碳排放活动数据表"},
                    {"fieldKey": "period", "confirmedValue": "2026-07"},
                    {"fieldKey": "carbon_emission", "confirmedValue": "1360"},
                ],
                "acceptedCandidateIds": [],
                "operatorId": 10001,
                "operatorName": "项目管理员",
                "comment": "碳排首页指标动态刷新验收",
            },
        )
        assert_true(confirmed.get("targetTable") == "carbon_emission_activity", "confirmed record should sync to carbon_emission_activity")

        expected = before_e04 + 1360
        after_kpis = get_json("/api/dashboard/kpis")
        after_e04 = kpi_value(after_kpis, "E04")
        after_detail = get_json("/api/dashboard/kpi/E04")
        after_total = summary_value(after_detail, "累计碳排放")
        carbon_topic = get_json("/api/dashboard/topics/carbon")
        topic_total = summary_value(carbon_topic, "施工阶段累计碳足迹")

        assert_true(after_e04 == expected, f"E04 card should increase by 1360, before={before_e04}, after={after_e04}")
        assert_true(after_total == expected, f"E04 detail should increase by 1360, before={before_total}, after={after_total}")
        assert_true(topic_total == expected, f"carbon topic total should increase by 1360, after={topic_total}")

        print("✅ 碳排资料入库驱动首页与专题动态刷新验收通过：E04/碳专题从 12856 增至 14216。")
        return 0
    finally:
        reset_acceptance_baseline()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 碳排资料入库驱动首页与专题动态刷新验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

