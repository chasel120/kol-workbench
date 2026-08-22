from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "kol_workbench.sqlite3"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}_{uuid.uuid4().hex[:8]}"


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(value: str | None, fallback: Any = None) -> Any:
    if value is None or value == "":
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'upload',
  row_count INTEGER NOT NULL DEFAULT 0,
  email_count INTEGER NOT NULL DEFAULT 0,
  field_map TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kol_leads (
  id TEXT PRIMARY KEY,
  dataset_id TEXT NOT NULL,
  platform TEXT,
  handle TEXT,
  email TEXT,
  whatsapp TEXT,
  other_contacts TEXT,
  homepage_url TEXT,
  fastmoss_url TEXT,
  country TEXT,
  language TEXT,
  category TEXT,
  commerce_niche TEXT,
  followers REAL DEFAULT 0,
  avg_views REAL DEFAULT 0,
  engagement_rate REAL DEFAULT 0,
  sales_28d REAL DEFAULT 0,
  score REAL DEFAULT 0,
  priority TEXT NOT NULL DEFAULT 'low',
  tags TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'imported',
  raw_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kol_dataset ON kol_leads(dataset_id);
CREATE INDEX IF NOT EXISTS idx_kol_email ON kol_leads(email);
CREATE INDEX IF NOT EXISTS idx_kol_status ON kol_leads(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kol_homepage_unique ON kol_leads(dataset_id, homepage_url) WHERE homepage_url IS NOT NULL AND homepage_url != '';

CREATE TABLE IF NOT EXISTS campaigns (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  market TEXT,
  niche TEXT,
  product_brief_ref TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outreach_drafts (
  id TEXT PRIMARY KEY,
  kol_id TEXT NOT NULL,
  type TEXT NOT NULL DEFAULT 'first_touch',
  status TEXT NOT NULL DEFAULT 'pending_review',
  to_email TEXT NOT NULL,
  from_account TEXT,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  risk_labels TEXT NOT NULL DEFAULT '[]',
  external_sent INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  sent_at TEXT,
  archived_at TEXT,
  FOREIGN KEY(kol_id) REFERENCES kol_leads(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_draft_status ON outreach_drafts(status);
CREATE INDEX IF NOT EXISTS idx_draft_kol ON outreach_drafts(kol_id);

CREATE TABLE IF NOT EXISTS replies (
  id TEXT PRIMARY KEY,
  kol_id TEXT,
  account_email TEXT,
  reply_text TEXT NOT NULL,
  intent TEXT NOT NULL DEFAULT 'needs_review',
  next_action TEXT NOT NULL DEFAULT 'generate_followup',
  created_at TEXT NOT NULL,
  archived_at TEXT,
  FOREIGN KEY(kol_id) REFERENCES kol_leads(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reply_templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'en',
  scenario TEXT NOT NULL DEFAULT 'first_touch',
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  tags TEXT NOT NULL DEFAULT '[]',
  is_default INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_tasks (
  id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  risk_labels TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'pending',
  reviewer TEXT,
  created_at TEXT NOT NULL,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  actor TEXT,
  action TEXT NOT NULL,
  target_type TEXT,
  target_id TEXT,
  summary TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS local_agent_sessions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  task_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',
  summary TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS local_task_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES local_agent_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sync_queue (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  operation TEXT NOT NULL DEFAULT 'upsert',
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  retry_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL DEFAULT '',
  sensitive INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gmail_accounts (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  browser_name TEXT NOT NULL DEFAULT '',
  browser_profile TEXT NOT NULL DEFAULT '',
  auth_status TEXT NOT NULL DEFAULT 'not_authorized',
  notes TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS local_user_profiles (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  email TEXT NOT NULL DEFAULT '',
  role TEXT NOT NULL DEFAULT 'BD',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        ensure_column(conn, "kol_leads", "tags", "TEXT NOT NULL DEFAULT '[]'")
        ensure_column(conn, "outreach_drafts", "archived_at", "TEXT")
        ensure_column(conn, "replies", "archived_at", "TEXT")
        ensure_column(conn, "reply_templates", "is_default", "INTEGER NOT NULL DEFAULT 0")
        conn.execute(
            """
            INSERT INTO local_user_profiles (id, display_name, email, role, created_at, updated_at)
            SELECT ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM local_user_profiles)
            """,
            ("local_user_placeholder", "BD Admin", "bd-local@example.com", "BD", now_iso(), now_iso()),
        )
        conn.execute(
            """
            UPDATE reply_templates
            SET is_default = 1
            WHERE id = 'tpl_default_first_touch_en'
              AND NOT EXISTS (
                SELECT 1 FROM reply_templates
                WHERE language = 'en' AND scenario = 'first_touch' AND is_default = 1
              )
            """
        )
        conn.execute(
            """
            INSERT INTO reply_templates (id, name, language, scenario, subject, body, tags, created_at, updated_at)
            SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM reply_templates)
            """,
            (
                "tpl_default_first_touch_en",
                "First touch - friendly EN",
                "en",
                "first_touch",
                "Collaboration idea for {{kol_name}}",
                "Hi {{kol_name}},\n\nI came across your {{platform}} content and noticed your audience fits {{niche}} in {{country}}. We are preparing a creator campaign and would like to share the product details with you.\n\nWould you be open to reviewing the product information and sample plan?\n\nBest,\nBD Team",
                dumps(["first_touch", "english", "safe"]),
                now_iso(),
                now_iso(),
            ),
        )
        conn.execute(
            """
            UPDATE reply_templates
            SET is_default = 1
            WHERE id = 'tpl_default_first_touch_en'
              AND NOT EXISTS (
                SELECT 1 FROM reply_templates
                WHERE language = 'en' AND scenario = 'first_touch' AND is_default = 1
              )
            """
        )
        hydrate_existing_kol_tags(conn)


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def hydrate_existing_kol_tags(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT id, email, country, category, commerce_niche, sales_28d, priority, tags
        FROM kol_leads
        WHERE tags IS NULL OR tags = '' OR tags = '[]'
        """
    ).fetchall()
    for row in rows:
        tags = [row["priority"] or "low"]
        if row["email"]:
            tags.append("has_email")
        if row["country"]:
            tags.append(str(row["country"]).strip())
        category = row["category"] or row["commerce_niche"]
        if category:
            tags.append(str(category).strip()[:24])
        if (row["sales_28d"] or 0) >= 3000:
            tags.append("sales_active")
        conn.execute("UPDATE kol_leads SET tags = ? WHERE id = ?", (dumps(list(dict.fromkeys([tag for tag in tags if tag]))), row["id"]))


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for key in ("field_map", "raw_json", "risk_labels", "metadata_json", "payload_json", "tags"):
        if key in data:
            data[key] = loads(data[key], [] if key in {"risk_labels", "tags"} else {})
    return data


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_dict(row) or {} for row in rows]


def audit(conn: sqlite3.Connection, action: str, target_type: str = "", target_id: str = "", summary: str = "", metadata: Any = None, actor: str = "local") -> None:
    conn.execute(
        """
        INSERT INTO audit_logs (id, actor, action, target_type, target_id, summary, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (new_id("audit"), actor, action, target_type, target_id, summary, dumps(metadata or {}), now_iso()),
    )


def create_session(conn: sqlite3.Connection, title: str, task_type: str) -> str:
    session_id = new_id("session")
    ts = now_iso()
    conn.execute(
        "INSERT INTO local_agent_sessions (id, title, task_type, status, summary, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, title, task_type, "running", "", ts, ts),
    )
    return session_id


def event(conn: sqlite3.Connection, session_id: str, event_type: str, message: str, payload: Any = None) -> None:
    conn.execute(
        "INSERT INTO local_task_events (id, session_id, event_type, message, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (new_id("event"), session_id, event_type, message, dumps(payload or {}), now_iso()),
    )


def finish_session(conn: sqlite3.Connection, session_id: str, summary: str, status: str = "completed") -> None:
    conn.execute(
        "UPDATE local_agent_sessions SET status = ?, summary = ?, updated_at = ? WHERE id = ?",
        (status, summary, now_iso(), session_id),
    )


def enqueue_sync(conn: sqlite3.Connection, entity_type: str, entity_id: str, payload: dict[str, Any], operation: str = "upsert") -> None:
    ts = now_iso()
    conn.execute(
        """
        INSERT INTO sync_queue (id, entity_type, entity_id, operation, payload_json, status, retry_count, last_error, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', 0, '', ?, ?)
        """,
        (new_id("sync"), entity_type, entity_id, operation, dumps(payload), ts, ts),
    )
