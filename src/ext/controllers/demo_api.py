import asyncio
import base64
import logging
import os
import shutil
from dataclasses import asdict
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


def _require_api_key(api_key: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            provided = request.headers.get("X-API-Key", "")
            if not provided or provided != api_key:
                return jsonify({"error": "invalid or missing X-API-Key"}), 401
            return f(*args, **kwargs)
        return wrapper
    return decorator


def create_demo_app(
    api_key: str,
    demo_sqlite_path: str,
    db_connector,
    inspection_repo_factory,
    history_repo_factory,
    queue_repo_factory,
    project_repo_factory,
    review_repo_factory,
    image_gateway,
    process_service_factory,
    system_version: str,
    loop: asyncio.AbstractEventLoop,
) -> Flask:
    app = Flask(__name__)
    auth = _require_api_key(api_key)

    _state = {
        "conn": None,
        "inspection_repo": None,
        "history_repo": None,
        "queue_repo": None,
        "project_repo": None,
        "review_repo": None,
        "process_svc": None,
    }

    def _run(coro):
        return loop.run_until_complete(coro)

    async def _connect():
        if _state["conn"] is not None:
            try:
                await _state["conn"].close()
            except Exception:
                pass
            for k in _state:
                _state[k] = None
        if not os.path.exists(demo_sqlite_path):
            return
        conn = await db_connector(demo_sqlite_path)
        _state["conn"] = conn
        _state["inspection_repo"] = inspection_repo_factory(conn)
        _state["history_repo"] = history_repo_factory(conn)
        _state["queue_repo"] = queue_repo_factory(conn)
        _state["project_repo"] = project_repo_factory(conn)
        _state["review_repo"] = review_repo_factory(conn)
        _state["process_svc"] = process_service_factory(
            queue_repo=_state["queue_repo"],
            project_repo=_state["project_repo"],
            history_repo=_state["history_repo"],
            inspection_repo=_state["inspection_repo"],
            review_repo=_state["review_repo"],
            telegram=image_gateway,
        )

    _run(_connect())

    @app.route("/demo/db", methods=["PUT"])
    @auth
    def upload_db():
        body = request.get_json(force=True)
        if not body or "db_base64" not in body:
            return jsonify({"error": "body must be JSON with a 'db_base64' field"}), 400
        try:
            data = base64.b64decode(body["db_base64"])
        except Exception:
            return jsonify({"error": "db_base64 is not valid base64"}), 400
        tmp_path = demo_sqlite_path + ".upload"
        with open(tmp_path, "wb") as f:
            f.write(data)
        shutil.move(tmp_path, demo_sqlite_path)
        _run(_connect())
        return jsonify({"status": "ok"})

    @app.route("/demo/messages", methods=["POST"])
    @auth
    def post_messages():
        if _state["history_repo"] is None:
            return jsonify({"error": "no demo database uploaded yet"}), 404
        body = request.get_json(force=True)
        project_id = body.get("project_id")
        if not project_id:
            return jsonify({"error": "project_id required"}), 400
        messages = body.get("messages", [])
        if not messages:
            return jsonify({"error": "messages array required"}), 400

        from app.domain.entities import ChatMessage, QueueItem, QueueStatus, UserRole
        saved = 0
        queued = 0
        for m in messages:
            file_id = m.get("file_id", "")
            image_b64 = m.get("image_base64", "")

            if file_id and image_b64:
                image_gateway.put(file_id, base64.b64decode(image_b64))

            msg = ChatMessage(
                chat_id=m["chat_id"],
                message_id=m["message_id"],
                telegram_user_id=m.get("telegram_user_id", "demo-user"),
                display_name=m.get("display_name", "Demo User"),
                role=UserRole(m.get("role", "TECNICO")),
                text=m.get("text", ""),
                timestamp=datetime.fromisoformat(m["timestamp"]),
                file_id=file_id,
                cluster_id=m.get("cluster_id", ""),
                is_included_in_history=m.get("is_included_in_history", True),
                rejected_reason=m.get("rejected_reason", ""),
            )
            _run(_state["history_repo"].save(project_id, msg))
            saved += 1

            if file_id and image_b64:
                queue_item = QueueItem(
                    project_id=project_id,
                    file_id=file_id,
                    chat_id=msg.chat_id,
                    system_version=system_version,
                    message_id=msg.message_id,
                    cluster_id=msg.cluster_id,
                    status=QueueStatus.PENDING,
                    attempts=0,
                    received_at=msg.timestamp,
                    last_error="",
                    worker_id="",
                    processed_at="",
                )
                _run(_state["queue_repo"].save(queue_item))
                queued += 1
        return jsonify({"status": "ok", "saved": saved, "queued": queued})

    @app.route("/demo/process", methods=["POST"])
    @auth
    def process_queue():
        if _state["process_svc"] is None:
            return jsonify({"error": "no demo database uploaded yet"}), 404
        from app.domain.entities import ProjectStatus
        projects = _run(_state["project_repo"].list_by_status(ProjectStatus.ACTIVE))
        processed = 0
        failed = 0
        for project in projects:
            while True:
                item = _run(_state["queue_repo"].get_oldest_pending(project.project_id, 0))
                if item is None:
                    break
                ok = _run(_state["process_svc"].execute(
                    item.chat_id, item.message_id, item.system_version
                ))
                if ok:
                    processed += 1
                else:
                    failed += 1
                    break
        return jsonify({"status": "ok", "processed": processed, "failed": failed})

    @app.route("/demo/inspections/<project_id>", methods=["GET"])
    @auth
    def get_inspections(project_id: str):
        if _state["inspection_repo"] is None:
            return jsonify({"error": "no demo database uploaded yet"}), 404
        records = _run(_state["inspection_repo"].get_all_for_project(project_id))
        out = []
        for r in records:
            d = asdict(r)
            d["created_at"] = r.created_at.isoformat()
            d["inspection_status"] = r.inspection_status.value
            out.append(d)
        return jsonify({"project_id": project_id, "inspections": out})

    @app.route("/demo/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    return app
