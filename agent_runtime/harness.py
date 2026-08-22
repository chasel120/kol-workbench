from __future__ import annotations

import os
import urllib.error
import urllib.request
from typing import Any

from . import importers
from .storage import audit, connect, create_session, dumps, enqueue_sync, event, finish_session, new_id, now_iso, row_to_dict, rows_to_dicts


def score_lead(row: dict[str, Any]) -> tuple[float, str]:
    score = 20.0
    if row.get("email"):
        score += 20
    if row.get("homepage_url"):
        score += 8
    if row.get("followers", 0) >= 100000:
        score += 14
    elif row.get("followers", 0) >= 30000:
        score += 8
    if row.get("avg_views", 0) >= 30000:
        score += 14
    elif row.get("avg_views", 0) >= 10000:
        score += 7
    if row.get("sales_28d", 0) >= 3000:
        score += 14
    elif row.get("sales_28d", 0) >= 500:
        score += 8
    if row.get("engagement_rate", 0) >= 1:
        score += 8
    elif row.get("engagement_rate", 0) >= 0.4:
        score += 4
    score = max(0, min(100, score))
    if score >= 78:
        priority = "high"
    elif score >= 58:
        priority = "medium"
    else:
        priority = "low"
    return score, priority


def lead_tags(row: dict[str, Any], priority: str) -> list[str]:
    tags: list[str] = [priority]
    if row.get("email"):
        tags.append("has_email")
    if row.get("country"):
        tags.append(str(row["country"]).strip())
    category = row.get("category") or row.get("commerce_niche")
    if category:
        tags.append(str(category).strip()[:24])
    if row.get("sales_28d", 0) >= 3000:
        tags.append("sales_active")
    return list(dict.fromkeys([tag for tag in tags if tag]))


def import_dataset(filename: str, content: str = "", content_base64: str = "") -> dict[str, Any]:
    rows, mapping = importers.parse_upload(filename, content, content_base64)
    dataset_id = new_id("ds")
    ts = now_iso()
    email_count = len([row for row in rows if row.get("email")])
    with connect() as conn:
        session_id = create_session(conn, f"导入数据集：{filename}", "lead_import")
        event(conn, session_id, "context.loaded", "开始解析上传文件", {"filename": filename})
        conn.execute(
            "INSERT INTO datasets (id, filename, source, row_count, email_count, field_map, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (dataset_id, filename, "upload", len(rows), email_count, dumps(mapping), ts),
        )
        for row in rows:
            score, priority = score_lead(row)
            kol_id = new_id("kol")
            tags = lead_tags(row, priority)
            conn.execute(
                """
                INSERT INTO kol_leads (
                  id, dataset_id, platform, handle, email, whatsapp, other_contacts, homepage_url, fastmoss_url,
                  country, language, category, commerce_niche, followers, avg_views, engagement_rate, sales_28d,
                  score, priority, tags, status, raw_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kol_id,
                    dataset_id,
                    row.get("platform", "TikTok"),
                    row.get("handle", ""),
                    row.get("email", ""),
                    row.get("whatsapp", ""),
                    row.get("other_contacts", ""),
                    row.get("homepage_url", ""),
                    row.get("fastmoss_url", ""),
                    row.get("country", ""),
                    "",
                    row.get("category", ""),
                    row.get("commerce_niche", ""),
                    row.get("followers", 0),
                    row.get("avg_views", 0),
                    row.get("engagement_rate", 0),
                    row.get("sales_28d", 0),
                    score,
                    priority,
                    dumps(tags),
                    "scored",
                    dumps(row.get("raw", {})),
                    ts,
                    ts,
                ),
            )
            enqueue_sync(conn, "kol_leads", kol_id, {"id": kol_id, "dataset_id": dataset_id, **{k: row.get(k, "") for k in ("platform", "handle", "email", "homepage_url", "country", "category", "commerce_niche")}, "score": score, "priority": priority, "tags": tags})
        audit(conn, "dataset.imported", "dataset", dataset_id, f"导入 {len(rows)} 条 KOL，邮箱 {email_count} 个")
        event(conn, session_id, "task.completed", "数据导入完成", {"rows": len(rows), "emails": email_count})
        finish_session(conn, session_id, f"导入 {len(rows)} 条 KOL，提取邮箱 {email_count} 个")
    return get_dataset(dataset_id) or {}


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        return row_to_dict(conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone())


def list_datasets() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM datasets ORDER BY created_at DESC").fetchall())


def list_kols(query: str = "", priority: str = "", status: str = "", tag: str = "", limit: int = 200) -> list[dict[str, Any]]:
    sql = "SELECT * FROM kol_leads WHERE 1=1"
    params: list[Any] = []
    if query:
        sql += " AND (handle LIKE ? OR email LIKE ? OR homepage_url LIKE ? OR category LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term, term])
    if priority:
        sql += " AND priority = ?"
        params.append(priority)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if tag:
        sql += " AND tags LIKE ?"
        params.append(f"%{tag}%")
    sql += " ORDER BY score DESC, updated_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, params).fetchall())


def render_template_text(text: str, kol: dict[str, Any], brief: str = "") -> str:
    values = {
        "kol_name": kol.get("handle") or "there",
        "name": kol.get("handle") or "there",
        "email": kol.get("email") or "",
        "platform": kol.get("platform") or "TikTok",
        "country": kol.get("country") or "your market",
        "niche": kol.get("commerce_niche") or kol.get("category") or "your content niche",
        "category": kol.get("category") or kol.get("commerce_niche") or "your content niche",
        "homepage": kol.get("homepage_url") or "",
        "brief": brief.strip(),
    }
    rendered = text
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def email_copy(kol: dict[str, Any], brief: str = "", language: str = "en", template: dict[str, Any] | None = None) -> tuple[str, str]:
    if template:
        subject = render_template_text(template.get("subject", ""), kol, brief)
        body = render_template_text(template.get("body", ""), kol, brief)
        return subject, body
    handle = kol.get("handle") or "there"
    niche = kol.get("commerce_niche") or kol.get("category") or "your content niche"
    country = kol.get("country") or "your market"
    if language == "zh":
        subject = f"{handle}，想和你聊一个合作机会"
        body = (
            f"Hi {handle}，\n\n"
            f"我们关注到你的 TikTok 内容，受众和 {country} 市场的 {niche} 方向比较匹配。"
            "我们正在准备一个达人合作活动，希望先把产品信息和样品计划发给你看看。\n\n"
            "如果你感兴趣，我们可以再根据你的内容风格沟通合作形式。\n\n"
            "祝好，\nBD Team"
        )
    else:
        subject = f"Collaboration idea for {handle}"
        body = (
            f"Hi {handle},\n\n"
            f"I came across your TikTok content and noticed your audience fits {niche} in {country}. "
            "We are preparing a creator campaign for practical products and would like to share the details with you.\n\n"
            "Would you be open to reviewing the product information and sample plan? "
            "If it looks relevant, we can discuss the cooperation format after your review.\n\n"
            "Best,\nBD Team"
        )
    if brief.strip():
        body += f"\n\nReviewer note: {brief.strip()[:400]}"
    return subject, body


def generate_drafts(limit: int = 20, brief: str = "", from_account: str = "", kol_ids: list[str] | None = None, language: str = "en", template_id: str = "") -> list[dict[str, Any]]:
    with connect() as conn:
        session_id = create_session(conn, "生成 Gmail 触达草稿", "outreach_generation")
        template = get_template_by_id(conn, template_id) if template_id else None
        event(conn, session_id, "context.loaded", "读取可触达 KOL", {"limit": limit, "selected": len(kol_ids or []), "language": language})
        if kol_ids:
            placeholders = ",".join("?" for _ in kol_ids)
            rows = conn.execute(
                f"SELECT * FROM kol_leads WHERE email IS NOT NULL AND email != '' AND id IN ({placeholders}) ORDER BY score DESC, updated_at DESC",
                kol_ids,
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM kol_leads
                WHERE email IS NOT NULL AND email != '' AND status IN ('scored', 'draft_ready', 'recycled')
                ORDER BY score DESC, updated_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 100)),),
            ).fetchall()
        drafts: list[dict[str, Any]] = []
        for row in rows:
            kol = row_to_dict(row) or {}
            subject, body = email_copy(kol, brief, language, template)
            risk_labels = ["manual_review_required"]
            if any(word in body.lower() for word in ["price", "commission", "free sample", "guarantee"]):
                risk_labels.append("commercial_terms")
            draft_id = new_id("draft")
            ts = now_iso()
            conn.execute(
                """
                INSERT INTO outreach_drafts (id, kol_id, type, status, to_email, from_account, subject, body, risk_labels, external_sent, created_at, updated_at)
                VALUES (?, ?, 'first_touch', 'pending_review', ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (draft_id, kol["id"], kol.get("email", ""), from_account, subject, body, dumps(risk_labels), ts, ts),
            )
            conn.execute("UPDATE kol_leads SET status = 'drafted', updated_at = ? WHERE id = ?", (ts, kol["id"]))
            enqueue_sync(conn, "outreach_records", draft_id, {"id": draft_id, "kol_id": kol["id"], "to_email": kol.get("email", ""), "status": "pending_review", "subject_summary": subject, "risk_labels": risk_labels})
            event(conn, session_id, "draft.generated", f"已生成 {kol.get('handle') or kol.get('email')} 的草稿", {"draft_id": draft_id, "language": language})
            drafts.append(get_draft_by_id(conn, draft_id) or {})
        audit(conn, "drafts.generated", "outreach_draft", "", f"生成 {len(drafts)} 条草稿")
        finish_session(conn, session_id, f"生成 {len(drafts)} 条待审核 Gmail 草稿")
        return drafts


def get_draft_by_id(conn: Any, draft_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT d.*, k.handle, k.homepage_url, k.priority, k.score
        FROM outreach_drafts d
        JOIN kol_leads k ON k.id = d.kol_id
        WHERE d.id = ?
        """,
        (draft_id,),
    ).fetchone()
    return row_to_dict(row)


def list_drafts(status: str = "", limit: int = 200) -> list[dict[str, Any]]:
    sql = """
      SELECT d.*, k.handle, k.homepage_url, k.priority, k.score
      FROM outreach_drafts d
      JOIN kol_leads k ON k.id = d.kol_id
      WHERE 1=1
    """
    params: list[Any] = []
    if status:
        sql += " AND d.status = ?"
        params.append(status)
    sql += " ORDER BY d.created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, params).fetchall())


def get_template_by_id(conn: Any, template_id: str) -> dict[str, Any] | None:
    if not template_id:
        return None
    return row_to_dict(conn.execute("SELECT * FROM reply_templates WHERE id = ?", (template_id,)).fetchone())


def list_templates() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM reply_templates ORDER BY updated_at DESC").fetchall())


def save_template(name: str, subject: str, body: str, language: str = "en", scenario: str = "first_touch", tags: list[str] | None = None, template_id: str = "") -> dict[str, Any]:
    if not name.strip() or not subject.strip() or not body.strip():
        raise ValueError("模板名称、主题和正文不能为空")
    ts = now_iso()
    with connect() as conn:
        if template_id:
            conn.execute(
                "UPDATE reply_templates SET name = ?, language = ?, scenario = ?, subject = ?, body = ?, tags = ?, updated_at = ? WHERE id = ?",
                (name.strip(), language, scenario, subject, body, dumps(tags or []), ts, template_id),
            )
            audit(conn, "template.updated", "reply_template", template_id, f"更新模板：{name}")
            return row_to_dict(conn.execute("SELECT * FROM reply_templates WHERE id = ?", (template_id,)).fetchone()) or {}
        new_template_id = new_id("tpl")
        conn.execute(
            "INSERT INTO reply_templates (id, name, language, scenario, subject, body, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (new_template_id, name.strip(), language, scenario, subject, body, dumps(tags or []), ts, ts),
        )
        audit(conn, "template.created", "reply_template", new_template_id, f"新增模板：{name}")
        return row_to_dict(conn.execute("SELECT * FROM reply_templates WHERE id = ?", (new_template_id,)).fetchone()) or {}


def generate_template_ai(language: str = "en", scenario: str = "first_touch", brief: str = "") -> dict[str, Any]:
    if language == "zh":
        subject = "{{kol_name}}，想和你聊一个合作机会"
        body = (
            "Hi {{kol_name}}，\n\n"
            "我们关注到你的 {{platform}} 内容，觉得你在 {{country}} 市场的 {{niche}} 方向和我们的产品比较匹配。"
            "{{brief}}\n\n"
            "如果你愿意了解，我可以先发你产品资料和样品计划，你看是否适合你的内容风格。\n\n"
            "祝好，\nBD Team"
        )
        name = "AI 生成中文触达模板"
    else:
        subject = "Collaboration idea for {{kol_name}}"
        body = (
            "Hi {{kol_name}},\n\n"
            "I came across your {{platform}} content and noticed your audience fits {{niche}} in {{country}}. "
            "{{brief}}\n\n"
            "Would you be open to reviewing the product details and sample plan? If it feels relevant, we can discuss the cooperation format after your review.\n\n"
            "Best,\nBD Team"
        )
        name = "AI generated first-touch template"
    return {"name": name, "language": language, "scenario": scenario, "subject": subject, "body": body, "tags": ["ai_generated", scenario, language]}


def approve_draft(draft_id: str, from_account: str = "") -> dict[str, Any]:
    with connect() as conn:
        draft = get_draft_by_id(conn, draft_id)
        if not draft:
            raise ValueError("草稿不存在")
        ts = now_iso()
        conn.execute(
            "UPDATE outreach_drafts SET status = 'sent_recorded', from_account = COALESCE(NULLIF(?, ''), from_account), sent_at = ?, updated_at = ? WHERE id = ?",
            (from_account, ts, ts, draft_id),
        )
        conn.execute("UPDATE kol_leads SET status = 'sent', updated_at = ? WHERE id = ?", (ts, draft["kol_id"]))
        audit(conn, "draft.sent_recorded", "outreach_draft", draft_id, "人工确认发送，当前版本仅记录发送动作", {"external_sent": False})
        enqueue_sync(conn, "outreach_records", draft_id, {"id": draft_id, "kol_id": draft["kol_id"], "status": "sent_recorded", "sent_at": ts, "subject_summary": draft["subject"]})
        return get_draft_by_id(conn, draft_id) or {}


def save_reply(kol_id: str, reply_text: str, account_email: str = "", intent: str = "needs_review") -> dict[str, Any]:
    with connect() as conn:
        kol = row_to_dict(conn.execute("SELECT * FROM kol_leads WHERE id = ?", (kol_id,)).fetchone())
        if not kol:
            raise ValueError("KOL 不存在")
        ts = now_iso()
        reply_id = new_id("reply")
        next_action = "generate_followup"
        conn.execute(
            "INSERT INTO replies (id, kol_id, account_email, reply_text, intent, next_action, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (reply_id, kol_id, account_email, reply_text, intent, next_action, ts),
        )
        conn.execute("UPDATE kol_leads SET status = 'replied', updated_at = ? WHERE id = ?", (ts, kol_id))
        subject = f"Re: Collaboration details for {kol.get('handle') or 'you'}"
        body = (
            f"Hi {kol.get('handle') or 'there'},\n\n"
            "Thanks for your reply. I reviewed your note and can share the next details for product fit, sample plan, and cooperation format.\n\n"
            "Please let me know which part you would like to confirm first.\n\n"
            "Best,\nBD Team\n\n"
            f"Reviewer note: {reply_text[:400]}"
        )
        draft_id = new_id("draft")
        conn.execute(
            """
            INSERT INTO outreach_drafts (id, kol_id, type, status, to_email, from_account, subject, body, risk_labels, external_sent, created_at, updated_at)
            VALUES (?, ?, 'follow_up', 'pending_review', ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (draft_id, kol_id, kol.get("email", ""), account_email, subject, body, dumps(["manual_review_required", "follow_up"]), ts, ts),
        )
        audit(conn, "reply.saved", "reply", reply_id, "保存回复并生成二次跟进草稿")
        enqueue_sync(conn, "reply_summaries", reply_id, {"id": reply_id, "kol_id": kol_id, "intent": intent, "next_action": next_action, "created_at": ts})
        return {"reply": row_to_dict(conn.execute("SELECT * FROM replies WHERE id = ?", (reply_id,)).fetchone()), "followupDraft": get_draft_by_id(conn, draft_id)}


def list_replies(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(
            conn.execute(
                """
                SELECT r.*, k.handle, k.email, k.homepage_url
                FROM replies r
                LEFT JOIN kol_leads k ON k.id = r.kol_id
                ORDER BY r.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        )


def summary() -> dict[str, Any]:
    with connect() as conn:
        values = {
            "datasets": conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],
            "kols": conn.execute("SELECT COUNT(*) FROM kol_leads").fetchone()[0],
            "emails": conn.execute("SELECT COUNT(*) FROM kol_leads WHERE email IS NOT NULL AND email != ''").fetchone()[0],
            "draftsPending": conn.execute("SELECT COUNT(*) FROM outreach_drafts WHERE status = 'pending_review'").fetchone()[0],
            "sentRecorded": conn.execute("SELECT COUNT(*) FROM outreach_drafts WHERE status = 'sent_recorded'").fetchone()[0],
            "replies": conn.execute("SELECT COUNT(*) FROM replies").fetchone()[0],
            "syncPending": conn.execute("SELECT COUNT(*) FROM sync_queue WHERE status = 'pending'").fetchone()[0],
        }
        return values


def supabase_status() -> dict[str, Any]:
    return {
        "configured": bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
        "url": os.environ.get("SUPABASE_URL", ""),
        "note": "Supabase 仅同步 KOL 等业务摘要；Agent 会话、模型上下文、原始邮件和密钥保持本地。",
    }


def sync_supabase(limit: int = 50) -> dict[str, Any]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        return {"ok": False, "synced": 0, "error": "未配置 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY，已保持本地-only。"}
    synced = 0
    errors: list[str] = []
    with connect() as conn:
        rows = conn.execute("SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?", (limit,)).fetchall()
        for row in rows:
            item = row_to_dict(row) or {}
            table = item["entity_type"]
            payload = item["payload_json"]
            if table not in {"kol_leads", "outreach_records", "reply_summaries"}:
                continue
            request = urllib.request.Request(
                f"{url}/rest/v1/{table}",
                data=dumps(payload).encode("utf-8"),
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates",
                },
                method="POST",
            )
            try:
                urllib.request.urlopen(request, timeout=20).read()
                conn.execute("UPDATE sync_queue SET status = 'synced', updated_at = ? WHERE id = ?", (now_iso(), item["id"]))
                synced += 1
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                conn.execute(
                    "UPDATE sync_queue SET retry_count = retry_count + 1, last_error = ?, updated_at = ? WHERE id = ?",
                    (f"HTTP {exc.code}: {detail}", now_iso(), item["id"]),
                )
                errors.append(f"{item['id']}: HTTP {exc.code}")
            except Exception as exc:
                conn.execute(
                    "UPDATE sync_queue SET retry_count = retry_count + 1, last_error = ?, updated_at = ? WHERE id = ?",
                    (str(exc), now_iso(), item["id"]),
                )
                errors.append(f"{item['id']}: {exc}")
    return {"ok": not errors, "synced": synced, "errors": errors}
