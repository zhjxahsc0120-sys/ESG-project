from __future__ import annotations

import json
import sys
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8765"
VALID_STATUSES = {"待提交", "待确认", "待补正", "校验通过", "不适用"}
PLACEHOLDER_NAMES = {"张三", "李四", "王五", "赵六", "钱七", "孙八"}


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    overview = get_json("/api/monthly/report-overview?reportMonth=2026-07")
    assert_true(overview["sourceMode"] == "mysql", "overview must use MySQL")
    assert_true(overview["isMock"] is False, "overview must not be mock")
    assert_true(overview["dataNature"] == "demo", "demo dataset must be labelled")
    assert_true(overview["readinessRate"] == 82, "readiness rate mismatch")
    assert_true(overview["summary"] == {
        "collectedCount": 18,
        "totalCount": 22,
        "pendingSubmitCount": 1,
        "pendingConfirmCount": 1,
        "pendingCorrectionCount": 2,
        "pendingTotal": 4,
        "notApplicableCount": 0,
    }, "summary mismatch")
    assert_true(len(overview["taskInstances"]) == 22, "task count mismatch")
    assert_true(len(overview["pendingTasks"]) == 4, "pending task count mismatch")
    passed_tasks = [item for item in overview["taskInstances"] if item["status"] == "校验通过"]
    pending_tasks = [item for item in overview["taskInstances"] if item["status"] != "校验通过"]
    assert_true(len(passed_tasks) == 18, "passed task count mismatch")
    assert_true(all(
        item["requiredMaterialCount"] == 1
        and item["linkedMaterialCount"] == 1
        and len(item["linkedMaterials"]) == 1
        and item["linkedMaterials"][0]["id"]
        and item["linkedMaterials"][0]["documentName"]
        and item["validationResult"] == "校验通过"
        and item["lastValidationAt"]
        and item["materialChain"]["status"] == "LINKED"
        for item in passed_tasks
    ), "passed task material/validation chain mismatch")
    assert_true(all(
        item["linkedMaterialCount"] == 0
        and item["linkedMaterials"] == []
        and item["materialChain"]["status"] == "UNLINKED"
        for item in pending_tasks
    ), "pending task data must remain unchanged")
    assert_true(
        {item["taskType"]: item["count"] for item in overview["taskTypeCounts"]}
        == {"MONTHLY_FIXED": 16, "CONDITIONAL": 4, "PERIODIC_REFERENCE": 2},
        "task type counts mismatch",
    )
    assert_true(
        {item["status"]: item["count"] for item in overview["statusCounts"]}
        == {"待提交": 1, "待确认": 1, "待补正": 2, "校验通过": 18, "不适用": 0},
        "status counts mismatch",
    )
    assert_true(
        {item["status"] for item in overview["taskInstances"]} <= VALID_STATUSES,
        "legacy status leaked from the API",
    )
    assert_true(
        not any(item.get("responsibleUserName") in PLACEHOLDER_NAMES for item in overview["taskInstances"]),
        "placeholder person name leaked from the API",
    )
    assert_true(
        all(item.get("responsibleRole") and item.get("responsibleUserId") is None
            and item.get("responsibleUserName") is None for item in overview["taskInstances"]),
        "responsibility fallback contract mismatch",
    )
    assert_true(overview["deadlineRange"] == {"start": "2026-08-02", "end": "2026-08-05"}, "deadline range mismatch")

    alias = get_json("/api/monthly/readiness?reportMonth=2026-07")
    assert_true(alias["summary"] == overview["summary"], "readiness alias mismatch")

    topic = get_json("/api/dashboard/topics/monthly-report")
    assert_true(topic["sourceMode"] == "mysql" and topic["isMock"] is False, "homepage topic source mismatch")
    assert_true(topic["completeness"] == "82%", "homepage topic readiness mismatch")
    assert_true(len(topic["topicData"]["chapters"]["list"]) == 22, "homepage topic must expose 22 tasks")
    assert_true(len(topic["detailData"]) == 4, "homepage topic must expose 4 pending tasks")
    assert_true(
        {item["key"]: item["value"] for item in topic["topicData"]["progress"]["groups"]}
        == {"E": 88, "S": 100, "G": 67},
        "homepage E/S/G progress must be derived from task facts",
    )

    print("[PASS] 月报新版MySQL聚合、兼容接口与首页专题回归通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 月报新版接口验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
