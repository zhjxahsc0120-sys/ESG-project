from __future__ import annotations

import json
import sys
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def summary_value(items: list[dict], label: str):
    return next(item["value"] for item in items if item.get("label") == label)


def main() -> int:
    topic = get_json("/api/carbon/benefit-overview")
    assert topic["sourceMode"] == "mysql" and topic["isMock"] is False
    assert "carbon_emission_segment_detail" in topic["dataSource"]
    assert summary_value(topic["summary"], "施工阶段累计碳足迹") == 12856
    assert summary_value(topic["summary"], "低碳措施节约成本") == 203.1
    assert topic["carbonCostLabel"] == "低碳措施节约成本"
    assert topic["carbonCostValue"] == 203.1 and topic["carbonCostUnit"] == "万元"

    monthly = topic["monthlyEmissions"]
    assert [row["month"] for row in monthly] == ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
    assert len({row["monthlyEmission"] for row in monthly}) == 6
    assert round(sum(row["monthlyEmission"] for row in monthly), 2) == 12856.0
    assert monthly[-1]["cumulativeEmission"] == 12856.0
    assert all(row["emissionUnit"] == "tCO₂e" for row in monthly)

    sources = topic["emissionSources"]
    assert [row["sourceCode"] for row in sources] == ["diesel", "electricity", "material", "transport"]
    assert round(sum(row["totalEmission"] for row in sources), 2) == 12856.0
    assert all(len(row["segments"]) == 3 for row in sources)
    assert all(len({segment["emissionAmount"] for segment in row["segments"]}) == 3 for row in sources)
    assert len(topic["segmentBreakdown"]) == 4

    material_segments = topic["materialSegmentBreakdown"]
    assert [row["segmentCode"] for row in material_segments] == ["SEG-01", "SEG-02", "SEG-03"]
    assert all([item["materialCode"] for item in row["materials"]] == ["cement", "steel", "asphalt"] for row in material_segments)
    assert round(sum(row["totalEmission"] for row in material_segments), 2) == 2485.73

    benefit = topic["topicData"]["benefit"]
    assert benefit["actualTotal"] == 12856.0
    assert benefit["accountedReduction"] == 1445.0
    assert benefit["measureEstimatedReduction"] == 950.0
    assert round(sum(row["accountedReduction"] for row in benefit["accountingRows"]), 2) == 1445.0

    cost = topic["topicData"]["measuresCosts"]["costSummary"]
    assert cost["investmentCost"] == 318.6
    assert cost["operatingCostSaving"] == 84.75
    assert cost["materialTransportDisposalSaving"] == 118.35
    assert cost["netCostImpact"] == 115.5
    assert cost["totalCostSaving"] == 203.1
    assert cost["totalCostSaving"] == round(cost["operatingCostSaving"] + cost["materialTransportDisposalSaving"], 2)
    assert cost["netCostImpact"] == round(cost["investmentCost"] - cost["operatingCostSaving"] - cost["materialTransportDisposalSaving"], 2)
    assert topic["dataNotice"] == "当前数据用于功能验证，不作为正式核算或财务确认依据。"

    print("[PASS] 碳排专题标段、材料、月度、减排与成本聚合接口通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 碳排专题接口测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
