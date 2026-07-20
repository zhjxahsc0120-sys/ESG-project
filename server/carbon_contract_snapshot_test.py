from __future__ import annotations

import json
from pathlib import Path

from carbon_benefit_overview import get_carbon_benefit_overview


SNAPSHOT = Path(__file__).resolve().parent / "data" / "carbon_benefit_overview.snapshot.json"


def main() -> int:
    mysql_payload = get_carbon_benefit_overview()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert mysql_payload is not None
    for key in ("monthlyEmissions", "emissionSources", "segmentBreakdown", "materialSegmentBreakdown"):
        assert snapshot[key] == mysql_payload[key]
    assert snapshot["carbonCostValue"] == mysql_payload["carbonCostValue"] == 203.1
    assert snapshot["topicData"]["measuresCosts"] == mysql_payload["topicData"]["measuresCosts"]
    assert snapshot["monthlyEmissions"][-1]["cumulativeEmission"] == 12856.0
    print("[PASS] 碳排JSON契约快照与MySQL聚合结构及数值一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
