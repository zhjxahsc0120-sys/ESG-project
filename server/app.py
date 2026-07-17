from __future__ import annotations

import json
import hashlib
import sqlite3
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import mysql_api
from mysql_db import mysql_enabled, mysql_ping

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "luoyi_esg_dev.db"
DASHBOARD_PAYLOAD_PATH = BASE_DIR / "dashboard_payload.json"
UPLOAD_DIR = BASE_DIR / "storage" / "uploads" / "202607"
HOST = "127.0.0.1"
PORT = 8765


GROUP_META = {
    "E": {"key": "E", "title": "环境环保组", "theme": "green", "status": "总体可控"},
    "S": {"key": "S", "title": "社会责任组", "theme": "blue", "status": "总体可控"},
    "G": {"key": "G", "title": "治理合规组", "theme": "purple", "status": "总体可控"},
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def try_mysql(func, *args):
    if not mysql_enabled():
        return None
    try:
        return func(*args)
    except Exception as exc:
        print(f"[api] MySQL fallback to SQLite: {exc}")
        return None


def load_dashboard_payload() -> dict:
    if not DASHBOARD_PAYLOAD_PATH.exists():
        return {}
    return json.loads(DASHBOARD_PAYLOAD_PATH.read_text(encoding="utf-8"))


def json_response(handler: BaseHTTPRequestHandler, payload: object, status: int = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def not_found(handler: BaseHTTPRequestHandler) -> None:
    json_response(handler, {"ok": False, "message": "接口不存在"}, HTTPStatus.NOT_FOUND)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    body = handler.rfile.read(length).decode("utf-8")
    return json.loads(body) if body else {}


def parse_disposition_params(value: str) -> dict[str, str]:
    params: dict[str, str] = {}
    for part in value.split(";"):
        if "=" not in part:
            continue
        key, raw = part.split("=", 1)
        clean_key = key.strip().lower()
        clean_value = raw.strip().strip('"')
        if clean_key.endswith("*") and "''" in clean_value:
            clean_value = unquote(clean_value.split("''", 1)[1])
            clean_key = clean_key[:-1]
        params[clean_key] = clean_value
    return params


def sanitize_filename(filename: str) -> str:
    safe = "".join(ch for ch in filename if ch not in '<>:"/\\|?*\r\n\t').strip()
    return safe or "未命名资料"


def parse_multipart_upload(handler: BaseHTTPRequestHandler) -> dict:
    content_type = handler.headers.get("Content-Type") or ""
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        raise ValueError("未接收到上传文件")
    if length > 220 * 1024 * 1024:
        raise ValueError("单个文件不能超过 200MB")

    boundary_token = ""
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary_token = part.split("=", 1)[1].strip().strip('"')
            break
    if not boundary_token:
        raise ValueError("multipart 请求缺少 boundary")

    body = handler.rfile.read(length)
    boundary = ("--" + boundary_token).encode("utf-8")
    fields: dict[str, str] = {}
    uploaded_file: dict | None = None

    for raw_part in body.split(boundary):
        part = raw_part
        if part.startswith(b"\r\n"):
            part = part[2:]
        if not part or part in (b"--", b"--\r\n"):
            continue
        if part.endswith(b"--\r\n"):
            part = part[:-4]
        elif part.endswith(b"--"):
            part = part[:-2].rstrip(b"\r\n")
        header_blob, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        try:
            header_text = header_blob.decode("utf-8")
        except UnicodeDecodeError:
            header_text = header_blob.decode("latin-1", errors="ignore")
        headers = header_text.split("\r\n")
        disposition = next((line for line in headers if line.lower().startswith("content-disposition:")), "")
        disposition_params = parse_disposition_params(disposition.split(":", 1)[1] if ":" in disposition else "")
        name = disposition_params.get("name", "")
        filename = disposition_params.get("filename")
        if filename:
            content_type_line = next((line for line in headers if line.lower().startswith("content-type:")), "")
            mime_type = content_type_line.split(":", 1)[1].strip() if ":" in content_type_line else "application/octet-stream"
            original_name = sanitize_filename(filename)
            file_bytes = content[:-2] if content.endswith(b"\r\n") else content
            sha256_hash = hashlib.sha256(file_bytes).hexdigest()
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            stored_name = f"{uuid.uuid4().hex}_{original_name}"
            stored_path = UPLOAD_DIR / stored_name
            stored_path.write_bytes(file_bytes)
            uploaded_file = {
                "originalName": original_name,
                "fileName": original_name,
                "fileSize": len(file_bytes),
                "mimeType": mime_type,
                "storagePath": str(stored_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "sha256Hash": sha256_hash,
            }
        elif name:
            field_bytes = content[:-2] if content.endswith(b"\r\n") else content
            fields[name] = field_bytes.decode("utf-8", errors="ignore").strip()

    if uploaded_file is None:
        raise ValueError("multipart 请求中未找到文件字段")

    uploaded_file.update(fields)
    return uploaded_file


def read_upload_payload(handler: BaseHTTPRequestHandler) -> dict:
    content_type = handler.headers.get("Content-Type") or ""
    if content_type.lower().startswith("multipart/form-data"):
        return parse_multipart_upload(handler)
    return read_json_body(handler)


def bad_request(handler: BaseHTTPRequestHandler, message: str) -> None:
    json_response(handler, {"ok": False, "message": message}, HTTPStatus.BAD_REQUEST)


def get_dashboard_kpis() -> dict:
    mysql_payload = try_mysql(mysql_api.get_dashboard_kpis)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT indicator_code, group_code, label, full_name, value, unit, display_order
            FROM indicator_result
            ORDER BY group_code, display_order
            """
        ).fetchall()

    groups: dict[str, dict] = {key: {**meta, "items": []} for key, meta in GROUP_META.items()}
    for row in rows:
        item = {
            "key": row["indicator_code"],
            "label": row["label"],
            "fullName": row["full_name"],
            "value": int(row["value"]) if float(row["value"]).is_integer() else row["value"],
            "unit": row["unit"],
        }
        groups[row["group_code"]]["items"].append(item)

    return {"groups": [groups["E"], groups["S"], groups["G"]]}


def get_dashboard_kpi_detail(kpi_code: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_dashboard_kpi_detail, kpi_code)
    if mysql_payload:
        return mysql_payload

    payload = load_dashboard_payload()
    detail = (payload.get("kpiDetails") or {}).get(kpi_code)
    if not detail:
        return None
    detail["isMock"] = False
    return detail


def get_dashboard_topic(topic_key: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_dashboard_topic, topic_key)
    if mysql_payload:
        return mysql_payload

    payload = load_dashboard_payload()
    if topic_key == "carbon":
        detail = payload.get("carbonTopicDetail")
        if not detail:
            return None
        detail["isMock"] = False
        detail["topicData"] = payload.get("carbonTabData") or {}
        return detail
    if topic_key in {"monthly", "monthly-report"}:
        detail = payload.get("monthlyTopicDetail")
        if not detail:
            return None
        detail["isMock"] = False
        detail["topicData"] = payload.get("monthlyTabData") or {}
        return detail
    return None


def get_dashboard_panels() -> dict:
    mysql_payload = try_mysql(mysql_api.get_dashboard_panels)
    if mysql_payload:
        return mysql_payload

    payload = load_dashboard_payload()
    return {
        "compliance": {
            "metrics": payload.get("complianceMetrics") or [],
            "effectiveness": payload.get("effectivenessItems") or [],
            "safeguards": payload.get("safeguardItems") or [],
        },
        "carbon": {
            "metrics": payload.get("carbonMetrics") or [],
            "sources": payload.get("carbonSources") or [],
            "reductions": payload.get("reductionMeasures") or [],
        },
        "monthly": payload.get("monthlyReport") or {},
        "timeline": payload.get("timelineSteps") or [],
        "gis": {
            "routePoints": payload.get("routePoints") or [],
            "routeSegments": payload.get("routeSegments") or [],
            "sensitiveAreas": payload.get("sensitiveAreas") or [],
        },
    }


def get_snapshot(snapshot_type: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT snapshot_type, snapshot_date, payload_json, published_at
            FROM indicator_snapshot
            WHERE snapshot_type = ?
            ORDER BY snapshot_date DESC, published_at DESC
            LIMIT 1
            """,
            (snapshot_type,),
        ).fetchone()
    if row is None:
        return None
    return {
        "snapshotType": row["snapshot_type"],
        "snapshotDate": row["snapshot_date"],
        "publishedAt": row["published_at"],
        "payload": json.loads(row["payload_json"]),
    }


def get_s01_detail() -> dict:
    mysql_payload = try_mysql(mysql_api.get_s01_detail)
    if mysql_payload is not None:
        return mysql_payload

    snapshot = get_snapshot("MODAL_S01")
    if snapshot is not None:
        return snapshot["payload"]

    with connect() as conn:
        safety = conn.execute("SELECT * FROM safety_production WHERE project_id = 900001").fetchone()
        stages = conn.execute("SELECT id, name, status, detail FROM construction_stage ORDER BY sequence_no").fetchall()
    if safety is None:
        return {}

    return {
        "projectStartDate": safety["project_start_date"],
        "currentDate": safety["current_date"],
        "currentStage": safety["current_stage"],
        "currentStageDetail": safety["current_stage_detail"],
        "countingStatus": safety["counting_status"],
        "updateTime": safety["update_time"],
        "constructionStages": [row_to_dict(row) for row in stages],
    }


def get_workspace_summary() -> dict:
    mysql_payload = try_mysql(mysql_api.get_workspace_summary)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        row = conn.execute("SELECT * FROM workspace_summary WHERE id = 1").fetchone()
    return {
        "currentTodo": row["current_todo"],
        "pendingUpload": row["pending_upload"],
        "pendingCorrection": row["pending_correction"],
        "pendingSubmit": row["pending_submit"],
        "underReview": row["under_review"],
        "dueSoon": row["due_soon"],
        "completed": row["completed"],
    }


def get_tasks(query: dict[str, list[str]]) -> dict:
    module = (query.get("module") or [""])[0]
    status = (query.get("status") or [""])[0]
    keyword = (query.get("keyword") or [""])[0]
    cycle = (query.get("cycle") or [""])[0]
    cycle_type = (query.get("cycleType") or query.get("cycle_type") or [""])[0]
    deadline_start = (query.get("deadlineStart") or query.get("deadline_start") or [""])[0]
    deadline_end = (query.get("deadlineEnd") or query.get("deadline_end") or [""])[0]
    assignee = (query.get("assignee") or [""])[0]

    mysql_payload = try_mysql(mysql_api.get_tasks, module, status, keyword, cycle, cycle_type, deadline_start, deadline_end, assignee)
    if mysql_payload is not None:
        return mysql_payload

    sql = "SELECT * FROM upload_task WHERE 1=1"
    params: list[str] = []
    if module:
        sql += " AND module_code = ?"
        params.append(module)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if keyword:
        sql += " AND name LIKE ?"
        params.append(f"%{keyword}%")
    sql += " ORDER BY deadline ASC"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "name": row["name"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "cycle": row["cycle"],
                "cycleType": row["cycle_type"],
                "deadline": row["deadline"],
                "deadlineDisplay": row["deadline"],
                "progressCurrent": row["progress_current"],
                "progressTotal": row["progress_total"],
                "status": row["status"],
                "nextStep": row["next_step"],
                "assignee": row["assignee"],
                "assigneeDept": row["assignee_dept"],
                "priorityCode": row["priority_code"],
            }
        )
    return {"total": len(items), "items": items}


def get_task_detail(task_id: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_task_detail, task_id)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        task = conn.execute("SELECT * FROM upload_task WHERE id = ?", (task_id,)).fetchone()
        if task is None:
            return None
        requirement_rows = conn.execute(
            """
            SELECT * FROM task_document_requirement
            WHERE task_id IN (?, '*')
            ORDER BY CASE WHEN task_id = ? THEN 0 ELSE 1 END, sequence_no
            """,
            (task_id, task_id),
        ).fetchall()
        candidate_rows = conn.execute(
            """
            SELECT * FROM task_candidate_document
            WHERE task_id IN (?, '*')
            ORDER BY CASE WHEN task_id = ? THEN 0 ELSE 1 END, sequence_no
            """,
            (task_id, task_id),
        ).fetchall()
        timeline_rows = conn.execute(
            """
            SELECT * FROM task_review_timeline
            WHERE task_id IN (?, '*')
            ORDER BY CASE WHEN task_id = ? THEN 0 ELSE 1 END, sequence_no
            """,
            (task_id, task_id),
        ).fetchall()
        review_columns = [row["name"] for row in conn.execute("PRAGMA table_info(review_record)").fetchall()]
        if "task_id" in review_columns:
            review_rows = conn.execute(
                "SELECT * FROM review_record WHERE task_id = ? ORDER BY submit_time DESC",
                (task_id,),
            ).fetchall()
        else:
            review_rows = []

    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "format": row["format_rule"],
            "status": row["status"],
            "templateAvailable": bool(row["template_available"]),
        }
        for row in requirement_rows
    ]
    completed = sum(1 for row in documents if row["status"] in ("已关联", "审核通过"))
    missing = sum(1 for row in documents if row["status"] == "缺失")
    abnormal = sum(1 for row in documents if row["status"] == "格式异常")

    return {
        "task": {
            "id": task["id"],
            "name": task["name"],
            "module": task["module_code"],
            "moduleName": task["module_name"],
            "cycle": task["cycle"],
            "cycleType": task["cycle_type"],
            "deadline": task["deadline"],
            "deadlineDisplay": task["deadline"],
            "progressCurrent": task["progress_current"],
            "progressTotal": task["progress_total"],
            "status": task["status"],
            "nextStep": task["next_step"],
            "assignee": task["assignee"],
            "assigneeDept": task["assignee_dept"],
            "priorityCode": task["priority_code"],
        },
        "tabs": ["资料要求", "已关联资料", "校验问题", "审核记录"],
        "documents": documents,
        "validation": {
            "completed": completed,
            "missing": missing,
            "abnormal": abnormal,
            "canSubmit": missing == 0 and abnormal == 0,
        },
        "candidateDocuments": [
            {
                "id": row["id"],
                "name": row["name"],
                "cycle": row["cycle"],
                "unit": row["unit_name"],
                "linkCount": row["link_count"],
                "matchRate": row["match_rate"],
            }
            for row in candidate_rows
        ],
        "linkedDocuments": [
            {
                "relationId": row["id"],
                "documentId": row["id"],
                "documentName": row["name"],
                "documentType": row["format_rule"],
                "period": task["cycle"],
                "version": "V1",
                "validityStatus": "有效",
                "source": "SQLite fallback",
                "relationType": "REQUIREMENT",
                "relationStatus": "LINKED",
                "matchScore": 90,
                "linkedAt": "",
                "uploadedAt": "",
            }
            for row in requirement_rows
            if row["status"] in ("已关联", "审核通过")
        ],
        "validationIssues": [
            {
                "id": row["id"],
                "documentRequirementId": row["id"],
                "documentName": row["name"],
                "issueType": row["status"],
                "severity": "warning" if row["status"] == "格式异常" else "error",
                "message": f"{row['name']}当前状态为{row['status']}",
                "canSubmit": False,
            }
            for row in requirement_rows
            if row["status"] in ("缺失", "格式异常")
        ],
        "aiRecommendation": {
            "fileName": "弃渣场巡查记录_2026-07.pdf",
            "matchRate": 96,
            "text": "该资料已用于其他流程，无需重复上传",
        },
        "aiTip": "还缺少“审核确认单”，建议下载模板后补充签章。",
        "reviewTimeline": [
            {
                "time": row["event_time"],
                "action": row["action_text"],
            }
            for row in timeline_rows
        ],
        "reviewRecords": [
            {
                "id": row["id"],
                "taskId": row["task_id"] if "task_id" in row.keys() else task_id,
                "taskName": row["task_name"],
                "submitTime": row["submit_time"],
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in review_rows
        ],
    }


def get_document_summary() -> dict:
    mysql_payload = try_mysql(mysql_api.get_document_summary)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        row = conn.execute("SELECT * FROM document_summary WHERE id = 1").fetchone()
    return {
        "documentTotal": row["document_total"],
        "monthNew": row["month_new"],
        "pendingArchive": row["pending_archive"],
        "expiringSoon": row["expiring_soon"],
    }


def get_documents() -> dict:
    mysql_payload = try_mysql(mysql_api.get_documents)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute("SELECT * FROM document_record ORDER BY uploaded_at DESC").fetchall()
    return {
        "total": 368,
        "items": [
            {
                "id": row["id"],
                "documentName": row["document_name"],
                "documentType": row["document_type"],
                "module": row["module_code"],
                "period": row["period_value"],
                "version": row["version_no"],
                "source": row["source_name"],
                "relationCount": row["relation_count"],
                "validityStatus": row["validity_status"],
                "uploadedAt": row["uploaded_at"],
            }
            for row in rows
        ],
    }


def get_document_detail_fallback(document_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM document_record WHERE id = ?", (document_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "documentCode": row["id"],
        "documentName": row["document_name"],
        "documentType": row["document_type"],
        "module": row["module_code"],
        "period": row["period_value"],
        "version": row["version_no"],
        "source": row["source_name"],
        "relationCount": row["relation_count"],
        "validityStatus": row["validity_status"],
        "documentStatus": "ACTIVE",
        "confirmStatus": "CONFIRMED",
        "responsibleUnit": row["source_name"],
        "validStartDate": None,
        "validEndDate": None,
        "uploadedAt": row["uploaded_at"],
        "file": {
            "fileId": None,
            "originalName": row["document_name"],
            "fileExt": row["document_name"].split(".")[-1] if "." in row["document_name"] else None,
            "mimeType": None,
            "fileSize": None,
            "fileSizeText": "-",
            "sha256Hash": None,
            "uploadSource": row["source_name"],
            "uploadTime": row["uploaded_at"],
        },
        "tags": [row["document_type"], row["module_code"], row["period_value"]],
        "isUnique": True,
    }


def get_document_versions_fallback(document_id: str) -> dict:
    detail = get_document_detail_fallback(document_id)
    if detail is None:
        return {"items": []}
    return {
        "items": [
            {
                "id": f"{document_id}-v1",
                "documentId": document_id,
                "versionNo": detail["version"],
                "versionDesc": "SQLite fallback 当前版本",
                "changeType": "CURRENT",
                "uploadedByName": "系统",
                "uploadedAt": detail["uploadedAt"],
                "isCurrent": True,
            }
        ]
    }


def get_document_relations_fallback(document_id: str) -> dict:
    return {"items": []}


def get_reviews() -> dict:
    mysql_payload = try_mysql(mysql_api.get_reviews)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute("SELECT * FROM review_record ORDER BY submit_time DESC").fetchall()
    task_map = {"r1": "t2", "r2": "t3", "r3": "t5", "r4": "t1"}
    return {
        "statusCards": [
            {"label": "待审核", "value": 3, "unit": "项", "color": "#2f9cff"},
            {"label": "已通过", "value": 21, "unit": "项", "color": "#69e36f"},
            {"label": "已退回", "value": 3, "unit": "项", "color": "#ff4f5e"},
            {"label": "补正逾期", "value": 1, "unit": "项", "color": "#ffb347"},
        ],
        "items": [
            {
                "id": row["id"],
                "taskId": row["task_id"] if "task_id" in row.keys() else task_map.get(row["id"], ""),
                "taskName": row["task_name"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "submitTime": row["submit_time"],
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in rows
        ],
    }


def get_review_detail(review_id: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_review_detail, review_id)
    if mysql_payload is not None:
        return mysql_payload
    with connect() as conn:
        row = conn.execute("SELECT * FROM review_record WHERE id = ?", (review_id,)).fetchone()
    if row is None:
        return None
    task_map = {"r1": "t2", "r2": "t3", "r3": "t5", "r4": "t1"}
    return {
        "id": row["id"],
        "taskId": row["task_id"] if "task_id" in row.keys() else task_map.get(row["id"], ""),
        "taskName": row["task_name"],
        "module": row["module_code"],
        "moduleName": row["module_name"],
        "submitTime": row["submit_time"],
        "status": row["status"],
        "reviewer": row["reviewer"],
        "commentSummary": row["comment_summary"],
        "nextStep": row["next_step"],
        "correctionDeadline": None,
        "requirementCount": 0,
    }


def get_review_timeline(review_id: str) -> dict:
    return try_mysql(mysql_api.get_review_timeline, review_id) or {"items": []}


def get_review_requirements(review_id: str) -> dict:
    return try_mysql(mysql_api.get_review_requirements, review_id) or {"items": []}


def get_ai_parse_queue() -> dict:
    mysql_payload = try_mysql(mysql_api.get_ai_parse_queue)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute("SELECT * FROM ai_parse_item ORDER BY id").fetchall()
    return {
        "items": [
            {
                "id": row["id"],
                "fileName": row["file_name"],
                "size": row["file_size"],
                "progress": row["progress"],
                "status": row["status"],
            }
            for row in rows
        ]
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        print(f"[api] {self.address_string()} - {format % args}")

    def do_OPTIONS(self) -> None:
        json_response(self, {"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path == "/health":
            mysql_status = None
            if mysql_enabled():
                try:
                    mysql_status = mysql_ping()
                except Exception as exc:
                    mysql_status = {"ok": False, "engine": "mysql", "message": str(exc)}
            json_response(
                self,
                {
                    "ok": True,
                    "service": "luoyi-esg-api",
                    "mode": "mysql-first" if mysql_enabled() else "sqlite",
                    "sqlite": str(DB_PATH),
                    "mysql": mysql_status,
                },
            )
            return

        if not DB_PATH.exists():
            json_response(self, {"ok": False, "message": "数据库不存在，请先执行 python server/init_db.py"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return

        if path == "/api/esg/gis/layers":
            project_id = (query.get("projectId") or ["LUOYI-ESG"])[0]
            section_id = (query.get("sectionId") or [None])[0]
            current_time = (query.get("currentTime") or [None])[0]
            visible_layer_ids_raw = (query.get("visibleLayerIds") or [None])[0]
            visible_layer_ids = [item for item in (visible_layer_ids_raw or "").split(",") if item] or None
            payload = try_mysql(mysql_api.get_gis_layers, project_id, section_id, current_time, visible_layer_ids)
            if payload is None:
                json_response(self, {"code": 500, "message": "GIS MySQL 数据暂不可用", "data": []}, HTTPStatus.OK)
            else:
                json_response(self, payload)
            return

        if path == "/api/esg/gis/features":
            project_id = (query.get("projectId") or ["LUOYI-ESG"])[0]
            section_id = (query.get("sectionId") or [None])[0]
            current_time = (query.get("currentTime") or [None])[0]
            layer_id = (query.get("layerId") or [None])[0]
            payload = try_mysql(mysql_api.get_gis_features, project_id, layer_id, section_id, current_time)
            if payload is None:
                json_response(self, {"code": 500, "message": "GIS MySQL 数据暂不可用", "data": []}, HTTPStatus.OK)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/esg/gis/features/"):
            project_id = (query.get("projectId") or ["LUOYI-ESG"])[0]
            feature_path = path.removeprefix("/api/esg/gis/features/")
            if feature_path.endswith("/business-links"):
                feature_id = unquote(feature_path.removesuffix("/business-links").rstrip("/"))
                payload = try_mysql(mysql_api.get_gis_feature_business_links, feature_id, project_id)
                if payload is None:
                    json_response(self, {"code": 500, "message": "GIS feature business links MySQL 数据暂不可用", "data": None}, HTTPStatus.OK)
                else:
                    json_response(self, payload)
                return

            if feature_path.endswith("/relations"):
                feature_id = unquote(feature_path.removesuffix("/relations").rstrip("/"))
                payload = try_mysql(mysql_api.get_gis_feature_relations, feature_id, project_id)
                if payload is None:
                    json_response(self, {"code": 500, "message": "GIS feature relations MySQL 数据暂不可用", "data": None}, HTTPStatus.OK)
                else:
                    json_response(self, payload)
                return

            feature_id = unquote(feature_path)
            payload = try_mysql(mysql_api.get_gis_feature_detail, feature_id, project_id)
            if payload is None:
                json_response(self, {"code": 500, "message": "GIS feature detail MySQL 数据暂不可用", "data": None}, HTTPStatus.OK)
            else:
                json_response(self, payload)
            return

        if path == "/api/dashboard/kpis":
            json_response(self, get_dashboard_kpis())
            return

        if path == "/api/dashboard/panels":
            json_response(self, get_dashboard_panels())
            return

        if path.startswith("/api/dashboard/topics/"):
            topic_key = path.removeprefix("/api/dashboard/topics/")
            topic = get_dashboard_topic(topic_key)
            if topic is None:
                not_found(self)
            else:
                json_response(self, topic)
            return

        if path == "/api/dashboard/snapshot":
            snapshot_type = (query.get("type") or ["LEADER_HOME"])[0]
            snapshot = get_snapshot(snapshot_type)
            json_response(self, snapshot if snapshot is not None else {})
            return

        if path == "/api/dashboard/kpi/S01":
            json_response(self, get_s01_detail())
            return

        if path.startswith("/api/dashboard/kpi/"):
            kpi_code = path.removeprefix("/api/dashboard/kpi/")
            detail = get_dashboard_kpi_detail(kpi_code)
            if detail is None:
                not_found(self)
            else:
                json_response(self, detail)
            return

        if path == "/api/workspace/summary":
            json_response(self, get_workspace_summary())
            return

        if path == "/api/workspace/tasks":
            json_response(self, get_tasks(query))
            return

        if path.startswith("/api/workspace/tasks/") and path.endswith("/detail"):
            task_id = path.removeprefix("/api/workspace/tasks/").removesuffix("/detail")
            detail = get_task_detail(task_id)
            if detail is None:
                not_found(self)
            else:
                json_response(self, detail)
            return

        if path == "/api/workspace/documents/summary":
            json_response(self, get_document_summary())
            return

        if path == "/api/workspace/documents":
            json_response(self, get_documents())
            return

        if path.startswith("/api/workspace/documents/"):
            parts = path.split("/")
            try:
                document_id_raw = parts[4]
            except IndexError:
                bad_request(self, "资料 ID 无效")
                return
            document_id_for_mysql = int(document_id_raw) if document_id_raw.isdigit() else None
            if len(parts) == 5:
                detail = try_mysql(mysql_api.get_document_detail, document_id_for_mysql) if document_id_for_mysql is not None else None
                if detail is None:
                    detail = get_document_detail_fallback(document_id_raw)
                if detail is None:
                    not_found(self)
                else:
                    json_response(self, detail)
                return
            if len(parts) == 6 and parts[5] == "versions":
                payload = try_mysql(mysql_api.get_document_versions, document_id_for_mysql) if document_id_for_mysql is not None else None
                json_response(self, payload if payload is not None else get_document_versions_fallback(document_id_raw))
                return
            if len(parts) == 6 and parts[5] == "relations":
                payload = try_mysql(mysql_api.get_document_relations, document_id_for_mysql) if document_id_for_mysql is not None else None
                json_response(self, payload if payload is not None else get_document_relations_fallback(document_id_raw))
                return

        if path == "/api/workspace/reviews":
            json_response(self, get_reviews())
            return

        if path.startswith("/api/workspace/reviews/"):
            parts = path.split("/")
            try:
                review_id = parts[4]
            except IndexError:
                bad_request(self, "审核记录 ID 无效")
                return
            if len(parts) == 5:
                detail = get_review_detail(review_id)
                if detail is None:
                    not_found(self)
                else:
                    json_response(self, detail)
                return
            if len(parts) == 6 and parts[5] == "timeline":
                json_response(self, get_review_timeline(review_id))
                return
            if len(parts) == 6 and parts[5] == "requirements":
                json_response(self, get_review_requirements(review_id))
                return

        if path == "/api/workspace/ai/parse-queue":
            json_response(self, get_ai_parse_queue())
            return

        if path.startswith("/api/workspace/parse-jobs/"):
            parts = path.split("/")
            try:
                job_id = int(parts[4])
            except (IndexError, ValueError):
                bad_request(self, "解析任务 ID 无效")
                return
            if len(parts) == 5:
                payload = try_mysql(mysql_api.get_parse_job, job_id)
                json_response(self, payload if payload is not None else {})
                return
            if len(parts) == 6 and parts[5] == "fields":
                payload = try_mysql(mysql_api.get_parse_fields, job_id)
                json_response(self, payload if payload is not None else {"items": []})
                return
            if len(parts) == 6 and parts[5] == "match-candidates":
                payload = try_mysql(mysql_api.get_match_candidates, job_id)
                json_response(self, payload if payload is not None else {"items": []})
                return

        not_found(self)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/workspace/files/upload":
            try:
                payload = read_upload_payload(self)
            except (json.JSONDecodeError, ValueError) as exc:
                bad_request(self, str(exc))
                return
            result = try_mysql(mysql_api.create_file_asset, payload)
            if result is None:
                bad_request(self, "MySQL 不可用，暂不能写入智能入库数据")
            else:
                json_response(self, result)
            return

        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            bad_request(self, "请求体不是合法 JSON")
            return

        if path.startswith("/api/workspace/tasks/"):
            parts = path.split("/")
            try:
                task_id = parts[4]
                action = parts[5]
            except IndexError:
                bad_request(self, "任务接口路径无效")
                return
            try:
                if action == "save":
                    result = try_mysql(mysql_api.save_task_draft, task_id, payload)
                elif action == "link-document":
                    result = try_mysql(mysql_api.link_task_document, task_id, payload)
                elif action == "submit":
                    result = try_mysql(mysql_api.submit_task_review, task_id, payload)
                else:
                    result = None
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        if path.startswith("/api/workspace/reviews/"):
            parts = path.split("/")
            try:
                review_id = parts[4]
                action = parts[5]
            except IndexError:
                bad_request(self, "审核接口路径无效")
                return
            if action == "approve":
                result = try_mysql(mysql_api.approve_review, review_id, payload)
            elif action == "return":
                result = try_mysql(mysql_api.return_review, review_id, payload)
            else:
                result = None
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        if path.startswith("/api/workspace/files/") and path.endswith("/parse"):
            try:
                file_id = int(path.removeprefix("/api/workspace/files/").removesuffix("/parse"))
            except ValueError:
                bad_request(self, "文件 ID 无效")
                return
            result = try_mysql(mysql_api.start_parse_job, file_id)
            if result is None:
                bad_request(self, "发起解析失败")
            else:
                json_response(self, result)
            return

        if path.startswith("/api/workspace/parse-jobs/") and path.endswith("/confirm"):
            try:
                job_id = int(path.removeprefix("/api/workspace/parse-jobs/").removesuffix("/confirm"))
            except ValueError:
                bad_request(self, "解析任务 ID 无效")
                return
            result = try_mysql(mysql_api.confirm_parse_job, job_id, payload)
            if result is None:
                bad_request(self, "确认入库失败")
            else:
                json_response(self, result)
            return

        not_found(self)


def main() -> None:
    if not DB_PATH.exists():
        print("数据库不存在，请先执行：python server/init_db.py")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Luoyi ESG API listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
