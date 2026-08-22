from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import harness
from .storage import DB_PATH, init_db


ROOT = Path(__file__).resolve().parents[1]
DESKTOP_SHELL = ROOT / "desktop_shell" / "index.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "KOLWorkbench/0.1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(fmt % args)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        if not path.exists():
            self.send_json({"error": "not found"}, 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        init_db()
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = parsed.path
        if path in {"/", "/index.html"}:
            self.send_file(DESKTOP_SHELL)
            return
        if path == "/api/summary":
            self.send_json({"ok": True, "summary": harness.summary(), "dbPath": str(DB_PATH)})
            return
        if path == "/api/datasets":
            self.send_json({"ok": True, "datasets": harness.list_datasets()})
            return
        if path == "/api/kols":
            self.send_json(
                {
                    "ok": True,
                    "kols": harness.list_kols(
                        query=query.get("query", [""])[0],
                        priority=query.get("priority", [""])[0],
                        status=query.get("status", [""])[0],
                        tag=query.get("tag", [""])[0],
                    ),
                }
            )
            return
        if path == "/api/kols/ids":
            self.send_json(
                {
                    "ok": True,
                    "ids": harness.list_kol_ids(
                        query=query.get("query", [""])[0],
                        priority=query.get("priority", [""])[0],
                        status=query.get("status", [""])[0],
                        tag=query.get("tag", [""])[0],
                        only_reachable=query.get("onlyReachable", ["1"])[0] != "0",
                    ),
                }
            )
            return
        if path == "/api/drafts":
            self.send_json({"ok": True, "drafts": harness.list_drafts(status=query.get("status", [""])[0])})
            return
        if path == "/api/templates":
            self.send_json({"ok": True, "templates": harness.list_templates()})
            return
        if path == "/api/replies":
            self.send_json({"ok": True, "replies": harness.list_replies()})
            return
        if path == "/api/supabase/status":
            self.send_json({"ok": True, "supabase": harness.supabase_status()})
            return
        if path == "/api/settings":
            self.send_json({"ok": True, "settings": harness.app_settings()})
            return
        if path == "/api/gmail-accounts":
            self.send_json({"ok": True, "accounts": harness.list_gmail_accounts()})
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        init_db()
        try:
            body = self.body_json()
            path = urlparse(self.path).path
            if path == "/api/datasets":
                dataset = harness.import_dataset(body.get("filename", "upload.csv"), body.get("content", ""), body.get("contentBase64", ""))
                self.send_json({"ok": True, "dataset": dataset})
                return
            if path == "/api/drafts/generate":
                drafts = harness.generate_drafts(
                    int(body.get("limit", 20) or 20),
                    body.get("brief", ""),
                    body.get("fromAccount", ""),
                    body.get("kolIds") or [],
                    body.get("language", "en"),
                    body.get("templateId", ""),
                )
                self.send_json({"ok": True, "drafts": drafts, "message": f"已生成 {len(drafts)} 条草稿，进入 Gmail 草稿队列。"})
                return
            if path == "/api/drafts/approve":
                draft = harness.approve_draft(body.get("draftId", ""), body.get("fromAccount", ""))
                self.send_json({"ok": True, "draft": draft})
                return
            if path == "/api/drafts/archive":
                draft = harness.archive_draft(body.get("draftId", ""))
                self.send_json({"ok": True, "draft": draft})
                return
            if path == "/api/drafts/restore":
                draft = harness.restore_draft(body.get("draftId", ""))
                self.send_json({"ok": True, "draft": draft})
                return
            if path == "/api/drafts/delete":
                self.send_json(harness.delete_draft(body.get("draftId", "")))
                return
            if path == "/api/gmail/archive-batch":
                self.send_json(harness.archive_mail_items(body.get("items") or []))
                return
            if path == "/api/gmail/delete-batch":
                self.send_json(harness.delete_mail_items(body.get("items") or []))
                return
            if path == "/api/replies":
                result = harness.save_reply(body.get("kolId", ""), body.get("replyText", ""), body.get("accountEmail", ""), body.get("intent", "needs_review"), body.get("language", "en"))
                self.send_json({"ok": True, **result})
                return
            if path == "/api/templates":
                template = harness.save_template(
                    body.get("name", ""),
                    body.get("subject", ""),
                    body.get("body", ""),
                    body.get("language", "en"),
                    body.get("scenario", "first_touch"),
                    body.get("tags") or [],
                    body.get("id", ""),
                )
                self.send_json({"ok": True, "template": template})
                return
            if path == "/api/templates/ai":
                template = harness.generate_template_ai(body.get("language", "en"), body.get("scenario", "first_touch"), body.get("brief", ""))
                self.send_json({"ok": True, "template": template})
                return
            if path == "/api/templates/delete":
                self.send_json(harness.delete_template(body.get("templateId", "")))
                return
            if path == "/api/templates/default":
                template = harness.set_default_template(body.get("templateId", ""))
                self.send_json({"ok": True, "template": template})
                return
            if path == "/api/models/list":
                self.send_json(
                    harness.list_supported_models(
                        body.get("provider", "openai"),
                        body.get("baseUrl", ""),
                        body.get("apiKey", ""),
                    )
                )
                return
            if path == "/api/settings/model":
                self.send_json(
                    {
                        "ok": True,
                        "model": harness.save_model_config(
                            body.get("provider", "openai"),
                            body.get("baseUrl", ""),
                            body.get("modelName", ""),
                            body.get("apiKey", ""),
                            bool(body.get("clearApiKey", False)),
                        ),
                    }
                )
                return
            if path == "/api/settings/user":
                self.send_json({"ok": True, "user": harness.save_current_user(body.get("displayName", ""), body.get("email", ""), body.get("role", "BD"))})
                return
            if path == "/api/gmail-accounts":
                self.send_json(
                    {
                        "ok": True,
                        "account": harness.save_gmail_account(
                            body.get("email", ""),
                            body.get("browserName", ""),
                            body.get("browserProfile", ""),
                            body.get("notes", ""),
                        ),
                    }
                )
                return
            if path == "/api/gmail-accounts/delete":
                self.send_json(harness.delete_gmail_account(body.get("accountId", "")))
                return
            if path == "/api/supabase/sync":
                self.send_json(harness.sync_supabase())
                return
            self.send_json({"error": "not found"}, 404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)


def main() -> None:
    init_db()
    host = "127.0.0.1"
    port = int(os.environ.get("KOL_WORKBENCH_PORT", "8766"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"KOL Agent 工作台已启动: http://{host}:{port}")
    print(f"本地 Agent 运行态数据库: {DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
