from __future__ import annotations

import app


def main() -> int:
    payload = app.load_carbon_overview_snapshot()
    assert payload is not None
    assert payload["sourceMode"] == "server-json"
    assert payload["isMock"] is False
    assert payload["monthlyEmissions"][-1]["cumulativeEmission"] == 12856.0
    assert len(payload["segmentBreakdown"]) == 4
    assert len(payload["materialSegmentBreakdown"]) == 3
    assert payload["carbonCostValue"] == 203.1
    print("[PASS] 碳排服务端JSON契约快照回退通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
