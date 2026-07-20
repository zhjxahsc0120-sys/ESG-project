from __future__ import annotations

import json
import sys
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str, params: dict | None = None) -> dict:
    query = f"?{urlencode(params or {})}" if params else ""
    try:
        with urlopen(f"{BASE_URL}{path}{query}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise AssertionError(f"接口不可访问：{path}{query}；请先启动 server/start_backend.ps1。原始错误：{exc}") from exc


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：期望 {expected!r}，实际 {actual!r}")


def assert_true(value: object, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    payload = get_json("/api/esg/gis/features", {"projectId": "LUOYI-ESG", "layerId": "section-2"})
    assert_equal(payload.get("code"), 0, "GIS 要素接口 code")
    features = payload.get("data") or []
    assert_equal(len(features), 1, "section-2 要素数量")

    feature = features[0]
    assert_equal(feature.get("statusLabel"), "正常", "section-2 状态中文标签")
    summary = feature.get("businessSummary") or {}
    assert_equal(summary.get("title"), "施工标段概览", "section-2 摘要标题")
    assert_equal(summary.get("statusLabel"), "正常", "section-2 摘要状态")
    assert_true(summary.get("dashboardRows"), "section-2 应返回领导层摘要行")
    relation_summary = feature.get("relationSummary") or {}
    assert_equal(relation_summary.get("total"), 2, "section-2 关联事项数量")
    assert_equal(relation_summary.get("highRiskCount"), 1, "section-2 高风险关联数量")

    detail_payload = get_json("/api/esg/gis/features/section-2-1", {"projectId": "LUOYI-ESG"})
    assert_equal(detail_payload.get("code"), 0, "GIS 要素详情接口 code")
    detail = detail_payload.get("data") or {}
    assert_equal(detail.get("id"), "section-2-1", "详情 featureId")
    assert_true(detail.get("businessSummary"), "详情应返回 businessSummary")
    assert_equal((detail.get("relationSummary") or {}).get("total"), 2, "详情关联事项数量")
    assert_true(len(detail.get("relations") or []) >= 2, "section-2 应至少有关联环保/风险事项")

    relations_payload = get_json("/api/esg/gis/features/section-2-1/relations", {"projectId": "LUOYI-ESG"})
    assert_equal(relations_payload.get("code"), 0, "GIS 关联事项接口 code")
    relations_data = relations_payload.get("data") or {}
    assert_equal((relations_data.get("summary") or {}).get("total"), 2, "关联事项接口 total")
    relation_types = {item.get("type") for item in relations_data.get("items") or []}
    assert_true({"environment_problem", "safety_risk"}.issubset(relation_types), "section-2 应有关联环保问题和安全风险")

    links_payload = get_json("/api/esg/gis/features/section-2-1/business-links", {"projectId": "LUOYI-ESG"})
    assert_equal(links_payload.get("code"), 0, "GIS 关联业务轻联动接口 code")
    links_data = links_payload.get("data") or {}
    permissions = links_data.get("permissions") or {}
    assert_equal(permissions.get("canView"), True, "领导层可查看关联业务")
    assert_equal(permissions.get("canSupervise"), False, "地图侧不提供督办")
    assert_equal(permissions.get("canHandle"), False, "地图侧不提供办理")
    link_items = links_data.get("items") or []
    assert_equal(len(link_items), 2, "关联业务轻联动 items")
    target_kpis = {item.get("targetKpiCode") for item in link_items}
    assert_true({"E02", "S02"}.issubset(target_kpis), "关联业务应映射 E02/S02")
    for item in link_items:
        assert_equal(item.get("actionEnabled"), False, "关联业务动作为预留")
        if item.get("targetKpiCode") == "E02":
            assert_equal(item.get("sourceTable"), "env_issue_record", "E02 关联业务 sourceTable 应与 KPI 明细来源表一致")
        if item.get("targetKpiCode") == "S02":
            assert_equal(item.get("sourceTable"), "safety_risk_point", "S02 关联业务 sourceTable 应与 KPI 明细来源表一致")

    e02_detail = get_json("/api/dashboard/kpi/E02")
    s02_detail = get_json("/api/dashboard/kpi/S02")
    kpi_source_ids = {
        "E02": {item.get("sourceId") for item in e02_detail.get("detailData") or []},
        "S02": {item.get("sourceId") for item in s02_detail.get("detailData") or []},
    }
    for item in link_items:
        target_kpi = item.get("targetKpiCode")
        source_id = item.get("sourceId")
        if target_kpi in {"E02", "S02"}:
            assert_true(source_id in kpi_source_ids[target_kpi], f"GIS business link {source_id} should match {target_kpi} detailData sourceId")

    risk_payload = get_json("/api/esg/gis/features/slope-2-1", {"projectId": "LUOYI-ESG"})
    risk_detail = risk_payload.get("data") or {}
    assert_equal(risk_detail.get("statusLabel"), "关注", "slope-2 状态中文标签")
    assert_true(risk_detail.get("relations"), "slope-2 应有关联风险事项")

    print("✅ GIS 业务摘要接口测试通过：列表摘要、详情摘要、关联事项接口、轻联动接口与中文状态均正常。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"❌ GIS 业务摘要接口测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
