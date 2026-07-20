from __future__ import annotations

import json
import sys
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def metric_value(items: list[dict], label: str):
    return next(item["value"] for item in items if item.get("label") == label)


def main() -> int:
    panels = get_json("/api/dashboard/panels")
    compliance = panels["compliance"]
    carbon = panels["carbon"]
    monthly = panels["monthly"]

    assert metric_value(compliance["metrics"], "合规点位") == 12
    assert metric_value(compliance["metrics"], "碳排点位") == 6
    assert metric_value(carbon["metrics"], "施工阶段累计碳足迹") == 12856
    assert metric_value(carbon["metrics"], "累计核算减排量") == 1445.0
    assert metric_value(carbon["metrics"], "低碳措施节约成本") == 203.1
    assert carbon["carbonCostLabel"] == "低碳措施节约成本"
    assert carbon["carbonCostValue"] == 203.1
    assert carbon["carbonCostUnit"] == "万元"
    assert len(carbon["sources"]) == 4

    assert monthly["progress"] == 82
    assert monthly["pendingCount"] == 4
    assert monthly["confirmCount"] == 1
    assert monthly["currentStatus"] == "资料归集"
    assert monthly["expectedCompletion"] is None
    assert len(monthly["materials"]) == 4

    print("[PASS] 首页面板MySQL回归通过，低碳措施节约成本指标为203.10万元。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 首页面板回归失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
