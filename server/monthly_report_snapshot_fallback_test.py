from __future__ import annotations

import app


def main() -> int:
    overview = app.load_monthly_overview_snapshot("2026-07")
    assert overview is not None
    assert overview["sourceMode"] == "server-json"
    assert overview["isMock"] is False
    assert overview["dataNature"] == "demo"
    assert overview["readinessRate"] == 82
    assert len(overview["taskInstances"]) == 22
    assert len(overview["pendingTasks"]) == 4
    passed = [task for task in overview["taskInstances"] if task["status"] == "校验通过"]
    assert len(passed) == 18
    assert all(
        task["requiredMaterialCount"] == task["linkedMaterialCount"] == 1
        and len(task["linkedMaterials"]) == 1
        and task["validationResult"] == "校验通过"
        and task["lastValidationAt"]
        and task["materialChain"]["status"] == "LINKED"
        for task in passed
    )
    assert app.load_monthly_overview_snapshot("2026-08") is None

    topic = app.monthly_overview_to_topic(overview)
    assert topic["completeness"] == "82%"
    assert topic["sourceMode"] == "server-json"
    assert len(topic["topicData"]["chapters"]["list"]) == 22
    assert len(topic["detailData"]) == 4
    print("[PASS] 月报服务端JSON契约快照回退通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
