from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import importers
from .secure_store import protect_text, unprotect_text
from .storage import audit, connect, create_session, dumps, enqueue_sync, event, finish_session, new_id, now_iso, row_to_dict, rows_to_dicts

LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Chinese",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
}


def language_name(language: str = "en") -> str:
    code = (language or "en").strip().lower()
    return LANGUAGE_NAMES.get(code, code or "English")


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


def list_kol_ids(query: str = "", priority: str = "", status: str = "", tag: str = "", only_reachable: bool = True, limit: int = 5000) -> list[str]:
    sql = "SELECT id FROM kol_leads WHERE 1=1"
    params: list[Any] = []
    if only_reachable:
        sql += " AND email IS NOT NULL AND email != ''"
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
    params.append(max(1, min(limit, 5000)))
    with connect() as conn:
        return [row["id"] for row in conn.execute(sql, params).fetchall()]


def _num(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return 0.0


def create_manual_kol(data: dict[str, Any]) -> dict[str, Any]:
    handle = str(data.get("handle") or "").strip()
    email = str(data.get("email") or "").strip()
    homepage_url = str(data.get("homepageUrl") or data.get("homepage_url") or "").strip()
    if not handle and not email and not homepage_url:
        raise ValueError("请至少填写 KOL 名称、邮箱或主页链接。")

    row = {
        "platform": str(data.get("platform") or "TikTok").strip() or "TikTok",
        "handle": handle or email or homepage_url,
        "email": email,
        "whatsapp": str(data.get("whatsapp") or "").strip(),
        "other_contacts": str(data.get("otherContacts") or data.get("other_contacts") or "").strip(),
        "homepage_url": homepage_url,
        "fastmoss_url": str(data.get("fastmossUrl") or data.get("fastmoss_url") or "").strip(),
        "country": str(data.get("country") or "").strip(),
        "category": str(data.get("category") or "").strip(),
        "commerce_niche": str(data.get("commerceNiche") or data.get("commerce_niche") or "").strip(),
        "followers": _num(data.get("followers")),
        "avg_views": _num(data.get("avgViews") or data.get("avg_views")),
        "engagement_rate": _num(data.get("engagementRate") or data.get("engagement_rate")),
        "sales_28d": _num(data.get("sales28d") or data.get("sales_28d")),
    }
    score, priority = score_lead(row)
    tags = lead_tags(row, priority)
    dataset_id = new_id("ds_manual")
    kol_id = new_id("kol")
    ts = now_iso()
    with connect() as conn:
        session_id = create_session(conn, f"手动录入 KOL：{row['handle']}", "manual_lead_import")
        conn.execute(
            "INSERT INTO datasets (id, filename, source, row_count, email_count, field_map, created_at) VALUES (?, ?, 'manual', 1, ?, ?, ?)",
            (dataset_id, f"manual-{row['handle']}", 1 if email else 0, dumps({"mode": "single_kol"}), ts),
        )
        conn.execute(
            """
            INSERT INTO kol_leads (
              id, dataset_id, platform, handle, email, whatsapp, other_contacts, homepage_url, fastmoss_url,
              country, language, category, commerce_niche, followers, avg_views, engagement_rate, sales_28d,
              score, priority, tags, status, raw_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scored', ?, ?, ?)
            """,
            (
                kol_id,
                dataset_id,
                row["platform"],
                row["handle"],
                row["email"],
                row["whatsapp"],
                row["other_contacts"],
                row["homepage_url"],
                row["fastmoss_url"],
                row["country"],
                str(data.get("language") or "").strip(),
                row["category"],
                row["commerce_niche"],
                row["followers"],
                row["avg_views"],
                row["engagement_rate"],
                row["sales_28d"],
                score,
                priority,
                dumps(tags),
                dumps(data),
                ts,
                ts,
            ),
        )
        enqueue_sync(conn, "kol_leads", kol_id, {"id": kol_id, "dataset_id": dataset_id, **{k: row.get(k, "") for k in ("platform", "handle", "email", "homepage_url", "country", "category", "commerce_niche")}, "score": score, "priority": priority, "tags": tags})
        audit(conn, "kol.manual_created", "kol_lead", kol_id, f"手动录入 KOL：{row['handle']}")
        event(conn, session_id, "task.completed", "手动 KOL 已入库并评分", {"kol_id": kol_id, "email": email})
        finish_session(conn, session_id, f"手动录入 1 条 KOL：{row['handle']}")
        return row_to_dict(conn.execute("SELECT * FROM kol_leads WHERE id = ?", (kol_id,)).fetchone()) or {}


def _set_setting(conn: Any, key: str, value: str, sensitive: bool = False) -> None:
    conn.execute(
        """
        INSERT INTO app_settings (key, value, sensitive, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, sensitive = excluded.sensitive, updated_at = excluded.updated_at
        """,
        (key, value, 1 if sensitive else 0, now_iso()),
    )


def _get_setting(conn: Any, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def get_model_config(include_secret: bool = False) -> dict[str, Any]:
    with connect() as conn:
        encrypted_key = _get_setting(conn, "model.api_key", "")
        config = {
            "provider": _get_setting(conn, "model.provider", "openai"),
            "baseUrl": _get_setting(conn, "model.base_url", ""),
            "modelName": _get_setting(conn, "model.name", ""),
            "hasApiKey": bool(encrypted_key),
        }
        if include_secret and encrypted_key:
            config["apiKey"] = unprotect_text(encrypted_key)
        return config


def save_model_config(provider: str, base_url: str, model_name: str, api_key: str = "", clear_api_key: bool = False) -> dict[str, Any]:
    with connect() as conn:
        _set_setting(conn, "model.provider", provider.strip() or "openai")
        _set_setting(conn, "model.base_url", base_url.strip())
        _set_setting(conn, "model.name", model_name.strip())
        if clear_api_key:
            _set_setting(conn, "model.api_key", "", True)
        elif api_key:
            _set_setting(conn, "model.api_key", protect_text(api_key), True)
        audit(conn, "settings.model_saved", "app_settings", "model", "模型配置已保存到本地加密设置")
    return get_model_config()


def get_current_user() -> dict[str, Any]:
    with connect() as conn:
        return row_to_dict(conn.execute("SELECT * FROM local_user_profiles ORDER BY created_at ASC LIMIT 1").fetchone()) or {
            "id": "local_user_placeholder",
            "display_name": "BD Admin",
            "email": "bd-local@example.com",
            "role": "BD",
        }


def save_current_user(display_name: str, email: str = "", role: str = "BD") -> dict[str, Any]:
    profile = get_current_user()
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            "UPDATE local_user_profiles SET display_name = ?, email = ?, role = ?, updated_at = ? WHERE id = ?",
            (display_name.strip() or "BD Admin", email.strip(), role.strip() or "BD", ts, profile["id"]),
        )
        audit(conn, "settings.user_saved", "local_user_profile", profile["id"], "开发期账号占位资料已保存")
        return row_to_dict(conn.execute("SELECT * FROM local_user_profiles WHERE id = ?", (profile["id"],)).fetchone()) or {}


def list_gmail_accounts() -> list[dict[str, Any]]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM gmail_accounts ORDER BY updated_at DESC").fetchall())


def save_gmail_account(email: str, browser_name: str = "", browser_profile: str = "", notes: str = "", browser_path: str = "") -> dict[str, Any]:
    if not email.strip():
        raise ValueError("Gmail email is required.")
    account_id = new_id("gmail")
    ts = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO gmail_accounts (id, email, browser_name, browser_path, browser_profile, auth_status, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'configured_placeholder', ?, ?, ?)
            """,
            (account_id, email.strip(), browser_name.strip(), browser_path.strip(), browser_profile.strip(), notes.strip(), ts, ts),
        )
        audit(conn, "gmail_account.configured", "gmail_account", account_id, "Gmail 浏览器授权配置占位已保存")
        return row_to_dict(conn.execute("SELECT * FROM gmail_accounts WHERE id = ?", (account_id,)).fetchone()) or {}


def save_gmail_accounts(emails: list[str], browser_name: str = "", browser_profile: str = "", notes: str = "", browser_path: str = "") -> list[dict[str, Any]]:
    cleaned: list[str] = []
    for email in emails:
        value = str(email or "").strip()
        if value and value not in cleaned:
            cleaned.append(value)
    if not cleaned:
        raise ValueError("At least one Gmail email is required.")
    return [save_gmail_account(email, browser_name, browser_profile, notes, browser_path) for email in cleaned]


def delete_gmail_account(account_id: str) -> dict[str, Any]:
    with connect() as conn:
        conn.execute("DELETE FROM gmail_accounts WHERE id = ?", (account_id,))
        audit(conn, "gmail_account.deleted", "gmail_account", account_id, "删除 Gmail 授权配置占位")
    return {"ok": True, "deleted": account_id}


def app_settings() -> dict[str, Any]:
    return {"model": get_model_config(), "gmailAccounts": list_gmail_accounts(), "user": get_current_user()}


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


def _json_from_model_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def call_model(messages: list[dict[str, str]], temperature: float = 0.4) -> str:
    config = get_model_config(include_secret=True)
    provider = (config.get("provider") or "openai").lower()
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = config.get("modelName") or ""
    api_key = config.get("apiKey") or ""
    if provider != "local" and (not base_url or not model or not api_key):
        raise ValueError("请先在设置中保存模型 Base URL、Model Name 和 API Key。")
    if provider == "local" and (not base_url or not model):
        raise ValueError("请先在设置中保存本地模型 Base URL 和 Model Name。")

    if provider == "local" or "ollama" in base_url.lower():
        endpoint = f"{base_url}/api/chat"
        payload = {"model": model, "messages": messages, "stream": False, "options": {"temperature": temperature}}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
    else:
        endpoint = f"{base_url}/chat/completions"
        payload = {"model": model, "messages": messages, "temperature": temperature}
        headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": f"Bearer {api_key}"}

    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise ValueError(f"Model request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Model request failed: {exc.reason}") from exc

    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    if isinstance(result.get("message"), dict):
        return result["message"].get("content", "")
    if isinstance(result.get("response"), str):
        return result["response"]
    raise ValueError("Model response did not contain generated text.")


def answer_native_session(message: str, language: str = "zh", kol_summary: str = "", history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    text = str(message or "").strip()
    if not text:
        raise ValueError("Message is required.")

    config = get_model_config(include_secret=False)
    safe_config = {
        "provider": config.get("provider") or "openai",
        "baseUrl": config.get("baseUrl") or "",
        "modelName": config.get("modelName") or "",
        "hasApiKey": bool(config.get("hasApiKey")),
    }

    model_messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are the native Harness assistant inside a local desktop KOL Workbench shell. "
                "Answer the operator directly using the configured model. "
                "The KOL Workbench is an installed plugin whose business data stays local unless an approved business sync runs. "
                "Do not claim to send Gmail automatically, read Gmail passwords, read browser cookies, or bypass human approval. "
                "If the user asks for KOL plugin context, use only the provided summary and ask them to open the plugin for detailed records. "
                "Prefer the user's input language. If the language is unclear, use the requested target language. "
                "Keep answers concise and practical."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "target_language": language_name(language),
                    "model_router": safe_config,
                    "kol_plugin_summary": str(kol_summary or "")[:2000],
                },
                ensure_ascii=False,
            ),
        },
    ]

    if isinstance(history, list):
        for item in history[-8:]:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content") or item.get("message") or "").strip()
            if not content:
                continue
            role = "user" if str(item.get("role") or "").lower() == "user" else "assistant"
            model_messages.append({"role": role, "content": content[:1500]})

    model_messages.append({"role": "user", "content": text})
    answer = call_model(model_messages, temperature=0.35).strip()
    if not answer:
        raise ValueError("Model returned an empty answer.")
    return {
        "answer": answer,
        "model": safe_config["modelName"],
        "provider": safe_config["provider"],
        "hasApiKey": safe_config["hasApiKey"],
    }


def generate_email_copy_with_model(kol: dict[str, Any], brief: str = "", language: str = "en", template: dict[str, Any] | None = None, scenario: str = "first_touch", reply_text: str = "") -> tuple[str, str]:
    rendered_template = ""
    if template:
        rendered_template = (
            "Template subject:\n"
            + render_template_text(template.get("subject", ""), kol, brief)
            + "\n\nTemplate body:\n"
            + render_template_text(template.get("body", ""), kol, brief)
        )
    prompt = {
        "scenario": scenario,
        "language": language_name(language),
        "kol": {
            "name": kol.get("handle") or "there",
            "email": kol.get("email") or "",
            "platform": kol.get("platform") or "TikTok",
            "country": kol.get("country") or "",
            "niche": kol.get("commerce_niche") or kol.get("category") or "",
            "homepage": kol.get("homepage_url") or "",
            "followers": kol.get("followers") or 0,
            "sales_28d": kol.get("sales_28d") or 0,
        },
        "campaign_brief": brief,
        "template": rendered_template,
        "reply_text": reply_text[:1200],
    }
    content = call_model(
        [
            {
                "role": "system",
                "content": "You write concise KOL outreach emails for BD teams. Return valid JSON only with keys subject and body. Write the entire email in the requested target language, keeping brand, platform, and product names unchanged when appropriate. Do not promise price, commission, or samples unless explicitly provided. Keep the tone natural and require human review.",
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        temperature=0.5,
    )
    try:
        data = _json_from_model_text(content)
        subject = str(data.get("subject") or "").strip()
        body = str(data.get("body") or "").strip()
    except Exception:
        subject = f"Collaboration idea for {kol.get('handle') or 'you'}"
        body = content.strip()
    if not subject or not body:
        raise ValueError("Model returned an empty draft.")
    return subject, body


def email_copy(kol: dict[str, Any], brief: str = "", language: str = "en", template: dict[str, Any] | None = None) -> tuple[str, str]:
    if template:
        subject = render_template_text(template.get("subject", ""), kol, brief)
        body = render_template_text(template.get("body", ""), kol, brief)
        return subject, body
    handle = kol.get("handle") or "there"
    niche = kol.get("commerce_niche") or kol.get("category") or "your content niche"
    country = kol.get("country") or "your market"
    code = (language or "en").strip().lower()
    fallback_templates = {
        "zh": (
            f"{handle}，想和你聊一个合作机会",
            (
                f"Hi {handle}，\n\n"
                f"我们关注到你的 TikTok 内容，受众和 {country} 市场的 {niche} 方向比较匹配。"
                "我们正在准备一个达人合作活动，希望先把产品信息和样品计划发给你看看。\n\n"
                "如果你感兴趣，我们可以再根据你的内容风格沟通合作形式。\n\n"
                "祝好，\nBD Team"
            ),
        ),
        "de": (
            f"Kooperationsidee fuer {handle}",
            (
                f"Hallo {handle},\n\n"
                f"ich bin auf deine TikTok-Inhalte aufmerksam geworden und finde, dass dein Publikum gut zu {niche} in {country} passt. "
                "Wir bereiten gerade eine Creator-Kampagne fuer praktische Produkte vor und wuerden dir gern die Produktinfos und den Musterplan schicken.\n\n"
                "Waerst du offen, dir die Details anzusehen? Wenn es fuer dich relevant ist, koennen wir danach das passende Kooperationsformat besprechen.\n\n"
                "Viele Gruesse,\nBD Team"
            ),
        ),
        "fr": (
            f"Idee de collaboration pour {handle}",
            (
                f"Bonjour {handle},\n\n"
                f"j'ai decouvert votre contenu TikTok et votre audience semble bien correspondre a {niche} sur le marche {country}. "
                "Nous preparons une campagne createur pour des produits pratiques et aimerions vous envoyer les informations produit et le plan d'echantillon.\n\n"
                "Seriez-vous ouvert(e) a les consulter ? Si cela vous semble pertinent, nous pourrons discuter du format de collaboration.\n\n"
                "Bien cordialement,\nBD Team"
            ),
        ),
        "es": (
            f"Idea de colaboracion para {handle}",
            (
                f"Hola {handle},\n\n"
                f"encontramos tu contenido en TikTok y creemos que tu audiencia encaja bien con {niche} en {country}. "
                "Estamos preparando una campana con creadores para productos practicos y nos gustaria enviarte la informacion del producto y el plan de muestra.\n\n"
                "Te interesaria revisarlo? Si encaja con tu contenido, podemos hablar del formato de colaboracion.\n\n"
                "Saludos,\nBD Team"
            ),
        ),
        "it": (
            f"Idea di collaborazione per {handle}",
            (
                f"Ciao {handle},\n\n"
                f"ho visto i tuoi contenuti su TikTok e penso che il tuo pubblico sia in linea con {niche} in {country}. "
                "Stiamo preparando una campagna creator per prodotti pratici e vorremmo inviarti le informazioni sul prodotto e il piano campioni.\n\n"
                "Ti andrebbe di valutarli? Se ti sembrano adatti, possiamo poi discutere il formato della collaborazione.\n\n"
                "Un saluto,\nBD Team"
            ),
        ),
        "pt": (
            f"Ideia de colaboracao para {handle}",
            (
                f"Ola {handle},\n\n"
                f"encontrei seu conteudo no TikTok e percebi que sua audiencia combina bem com {niche} em {country}. "
                "Estamos preparando uma campanha com criadores para produtos praticos e gostariamos de enviar as informacoes do produto e o plano de amostra.\n\n"
                "Voce teria interesse em avaliar? Se fizer sentido, podemos conversar sobre o formato da cooperacao.\n\n"
                "Atenciosamente,\nBD Team"
            ),
        ),
        "nl": (
            f"Samenwerkingsidee voor {handle}",
            (
                f"Hallo {handle},\n\n"
                f"ik kwam je TikTok-content tegen en denk dat je publiek goed past bij {niche} in {country}. "
                "We bereiden een creator-campagne voor praktische producten voor en sturen je graag de productinformatie en het sampleplan.\n\n"
                "Sta je ervoor open om dit te bekijken? Als het relevant voelt, kunnen we daarna de samenwerkingsvorm bespreken.\n\n"
                "Met vriendelijke groet,\nBD Team"
            ),
        ),
        "pl": (
            f"Pomysl na wspolprace dla {handle}",
            (
                f"Czesc {handle},\n\n"
                f"trafilismy na Twoje tresci na TikToku i widzimy, ze Twoja publicznosc dobrze pasuje do {niche} w {country}. "
                "Przygotowujemy kampanie creatorska dla praktycznych produktow i chetnie przeslemy informacje o produkcie oraz plan probek.\n\n"
                "Czy chcesz to sprawdzic? Jesli bedzie to pasowalo do Twojego stylu, omowimy format wspolpracy.\n\n"
                "Pozdrawiamy,\nBD Team"
            ),
        ),
        "ja": (
            f"{handle}さんへのコラボレーションのご提案",
            (
                f"{handle}さん、こんにちは。\n\n"
                f"TikTokのコンテンツを拝見し、{country}市場の{niche}領域と相性がよいと感じました。"
                "現在、実用的な商品のクリエイターキャンペーンを準備しており、商品情報とサンプル計画をお送りしたいと考えています。\n\n"
                "ご興味があれば、まず内容をご確認いただけますでしょうか。合いそうであれば、投稿スタイルに合わせて協業形式を相談できれば幸いです。\n\n"
                "よろしくお願いいたします。\nBD Team"
            ),
        ),
        "ko": (
            f"{handle}님께 드리는 협업 제안",
            (
                f"안녕하세요 {handle}님,\n\n"
                f"TikTok 콘텐츠를 보고 {country} 시장의 {niche} 분야와 잘 맞는다고 느꼈습니다. "
                "현재 실용적인 제품 관련 크리에이터 캠페인을 준비 중이며, 제품 정보와 샘플 계획을 먼저 공유드리고 싶습니다.\n\n"
                "검토해 보실 의향이 있으실까요? 적합하다고 느끼시면 콘텐츠 스타일에 맞는 협업 방식을 함께 논의하겠습니다.\n\n"
                "감사합니다.\nBD Team"
            ),
        ),
        "ar": (
            f"فرصة تعاون مع {handle}",
            (
                f"مرحباً {handle}،\n\n"
                f"اطلعنا على محتواك في TikTok ولاحظنا أن جمهورك مناسب لفئة {niche} في {country}. "
                "نحضّر حالياً حملة مع صناع محتوى لمنتجات عملية، ونود إرسال معلومات المنتج وخطة العينة لك للمراجعة.\n\n"
                "هل ترغب في الاطلاع على التفاصيل؟ إذا كان الأمر مناسباً، يمكننا مناقشة شكل التعاون بعد ذلك.\n\n"
                "مع التحية،\nBD Team"
            ),
        ),
    }
    subject, body = fallback_templates.get(code, (
        f"Collaboration idea for {handle}",
        (
            f"Hi {handle},\n\n"
            f"I came across your TikTok content and noticed your audience fits {niche} in {country}. "
            "We are preparing a creator campaign for practical products and would like to share the details with you.\n\n"
            "Would you be open to reviewing the product information and sample plan? "
            "If it looks relevant, we can discuss the cooperation format after your review.\n\n"
            "Best,\nBD Team"
        ),
    ))
    if brief.strip():
        body += f"\n\nReviewer note: {brief.strip()[:400]}"
    return subject, body


def get_default_template(conn: Any, language: str = "en", scenario: str = "first_touch") -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM reply_templates WHERE language = ? AND scenario = ? AND is_default = 1 ORDER BY updated_at DESC LIMIT 1",
        (language, scenario),
    ).fetchone()
    if not row:
        row = conn.execute(
            "SELECT * FROM reply_templates WHERE language = ? AND scenario = ? ORDER BY updated_at DESC LIMIT 1",
            (language, scenario),
        ).fetchone()
    return row_to_dict(row)


def generate_drafts(limit: int = 20, brief: str = "", from_account: str = "", kol_ids: list[str] | None = None, language: str = "en", template_id: str = "") -> list[dict[str, Any]]:
    with connect() as conn:
        session_id = create_session(conn, "生成 Gmail 触达草稿", "outreach_generation")
        template = get_template_by_id(conn, template_id) if template_id else get_default_template(conn, language, "first_touch")
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
            subject, body = generate_email_copy_with_model(kol, brief, language, template, "first_touch")
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
        return rows_to_dicts(conn.execute("SELECT * FROM reply_templates ORDER BY is_default DESC, updated_at DESC").fetchall())


def set_default_template(template_id: str) -> dict[str, Any]:
    if not template_id:
        raise ValueError("Template id is required.")
    with connect() as conn:
        template = get_template_by_id(conn, template_id)
        if not template:
            raise ValueError("Template does not exist.")
        ts = now_iso()
        conn.execute(
            "UPDATE reply_templates SET is_default = 0, updated_at = ? WHERE language = ? AND scenario = ?",
            (ts, template.get("language", "en"), template.get("scenario", "first_touch")),
        )
        conn.execute("UPDATE reply_templates SET is_default = 1, updated_at = ? WHERE id = ?", (ts, template_id))
        audit(conn, "template.default_set", "reply_template", template_id, f"Default template set: {template.get('name', template_id)}")
        return get_template_by_id(conn, template_id) or {}


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


def delete_template(template_id: str) -> dict[str, Any]:
    if not template_id:
        raise ValueError("Template id is required.")
    with connect() as conn:
        existing = row_to_dict(conn.execute("SELECT id, name, language, scenario, is_default FROM reply_templates WHERE id = ?", (template_id,)).fetchone())
        if not existing:
            raise ValueError("Template does not exist.")
        conn.execute("DELETE FROM reply_templates WHERE id = ?", (template_id,))
        if existing.get("is_default"):
            fallback = conn.execute(
                "SELECT id FROM reply_templates WHERE language = ? AND scenario = ? ORDER BY updated_at DESC LIMIT 1",
                (existing.get("language", "en"), existing.get("scenario", "first_touch")),
            ).fetchone()
            if fallback:
                conn.execute("UPDATE reply_templates SET is_default = 1, updated_at = ? WHERE id = ?", (now_iso(), fallback["id"]))
        audit(conn, "template.deleted", "reply_template", template_id, f"Deleted template: {existing.get('name', template_id)}")
        return {"ok": True, "deleted": template_id}


def generate_template_ai(language: str = "en", scenario: str = "first_touch", brief: str = "") -> dict[str, Any]:
    target_language = language_name(language)
    content = call_model(
        [
            {
                "role": "system",
                "content": "Create a reusable KOL outreach email template. Return valid JSON only with keys name, subject, body. Write the reusable template in the requested target language. The template must include dynamic fields such as {{kol_name}}, {{platform}}, {{country}}, {{niche}}, and {{brief}}.",
            },
            {
                "role": "user",
                "content": json.dumps({"language": target_language, "language_code": language, "scenario": scenario, "campaign_brief": brief}, ensure_ascii=False),
            },
        ],
        temperature=0.55,
    )
    data = _json_from_model_text(content)
    name = str(data.get("name") or ("AI generated template" if language != "zh" else "AI 生成模板")).strip()
    subject = str(data.get("subject") or "").strip()
    body = str(data.get("body") or "").strip()
    if not subject or not body:
        raise ValueError("Model returned an empty template.")
    return {"name": name, "language": language, "scenario": scenario, "subject": subject, "body": body, "tags": ["ai_generated", scenario, language]}
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


def _gmail_account_for(conn: Any, email: str = "") -> dict[str, Any] | None:
    if email:
        row = conn.execute("SELECT * FROM gmail_accounts WHERE email = ? ORDER BY updated_at DESC LIMIT 1", (email.strip(),)).fetchone()
        if row:
            return row_to_dict(row)
    row = conn.execute("SELECT * FROM gmail_accounts WHERE browser_path != '' ORDER BY updated_at DESC LIMIT 1").fetchone()
    if row:
        return row_to_dict(row)
    row = conn.execute("SELECT * FROM gmail_accounts ORDER BY updated_at DESC LIMIT 1").fetchone()
    return row_to_dict(row)


def _browser_launch_args(account: dict[str, Any], url: str) -> list[str]:
    browser_path = str(account.get("browser_path") or "").strip()
    if not browser_path:
        raise ValueError("请先在设置中配置 Gmail 账号对应的浏览器程序路径。")
    browser = Path(browser_path)
    if not browser.exists():
        raise ValueError(f"浏览器程序不存在：{browser_path}")

    args = [str(browser)]
    profile_text = str(account.get("browser_profile") or "").strip()
    if profile_text:
        profile = Path(profile_text)
        if profile.exists():
            name = profile.name
            if name.lower() == "default" or name.lower().startswith("profile"):
                args.append(f"--user-data-dir={profile.parent}")
                args.append(f"--profile-directory={name}")
            else:
                args.append(f"--user-data-dir={profile}")
        else:
            args.append(f"--profile-directory={profile_text}")
    args.extend(["--new-window", url])
    return args


def open_gmail_compose(draft_id: str, account_email: str = "") -> dict[str, Any]:
    with connect() as conn:
        draft = get_draft_by_id(conn, draft_id)
        if not draft:
            raise ValueError("草稿不存在")
        selected_email = (account_email or draft.get("from_account") or "").strip()
        account = _gmail_account_for(conn, selected_email)
        if not account:
            raise ValueError("请先在设置中添加 Gmail 账号和浏览器配置。")
        query = urllib.parse.urlencode(
            {
                "view": "cm",
                "fs": "1",
                "to": draft.get("to_email") or "",
                "su": draft.get("subject") or "",
                "body": draft.get("body") or "",
            }
        )
        url = f"https://mail.google.com/mail/?{query}"
        args = _browser_launch_args(account, url)
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audit(
            conn,
            "gmail.compose_opened",
            "outreach_draft",
            draft_id,
            "已打开 Gmail 撰写窗口，等待人工检查并发送",
            {"gmail_account": account.get("email"), "external_sent": False},
        )
        return {"ok": True, "draft": draft, "account": account.get("email"), "browser": account.get("browser_name") or account.get("browser_path"), "externalSent": False}


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


def archive_draft(draft_id: str) -> dict[str, Any]:
    with connect() as conn:
        draft = get_draft_by_id(conn, draft_id)
        if not draft:
            raise ValueError("Draft does not exist.")
        ts = now_iso()
        conn.execute("UPDATE outreach_drafts SET status = 'archived', archived_at = ?, updated_at = ? WHERE id = ?", (ts, ts, draft_id))
        audit(conn, "draft.archived", "outreach_draft", draft_id, "草稿已归档")
        return get_draft_by_id(conn, draft_id) or {}


def restore_draft(draft_id: str) -> dict[str, Any]:
    with connect() as conn:
        draft = get_draft_by_id(conn, draft_id)
        if not draft:
            raise ValueError("Draft does not exist.")
        ts = now_iso()
        conn.execute("UPDATE outreach_drafts SET status = 'pending_review', archived_at = NULL, updated_at = ? WHERE id = ?", (ts, draft_id))
        audit(conn, "draft.restored", "outreach_draft", draft_id, "草稿已恢复到待审核")
        return get_draft_by_id(conn, draft_id) or {}


def delete_draft(draft_id: str) -> dict[str, Any]:
    with connect() as conn:
        draft = get_draft_by_id(conn, draft_id)
        if not draft:
            raise ValueError("Draft does not exist.")
        conn.execute("DELETE FROM outreach_drafts WHERE id = ?", (draft_id,))
        audit(conn, "draft.deleted", "outreach_draft", draft_id, "草稿已从本地删除")
    return {"ok": True, "deleted": draft_id}


def _normalize_mail_items(items: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    draft_ids: list[str] = []
    reply_ids: list[str] = []
    for item in items or []:
        kind = str(item.get("kind") or item.get("type") or "").strip().lower()
        item_id = str(item.get("id") or "").strip()
        if not item_id:
            continue
        if kind in {"draft", "outreach_draft"}:
            draft_ids.append(item_id)
        elif kind in {"reply", "gmail_reply"}:
            reply_ids.append(item_id)
    return list(dict.fromkeys(draft_ids)), list(dict.fromkeys(reply_ids))


def archive_mail_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    draft_ids, reply_ids = _normalize_mail_items(items)
    if not draft_ids and not reply_ids:
        raise ValueError("No mail items selected.")
    ts = now_iso()
    with connect() as conn:
        archived_drafts = 0
        archived_replies = 0
        if draft_ids:
            placeholders = ",".join("?" for _ in draft_ids)
            result = conn.execute(
                f"UPDATE outreach_drafts SET status = 'archived', archived_at = ?, updated_at = ? WHERE id IN ({placeholders})",
                [ts, ts, *draft_ids],
            )
            archived_drafts = result.rowcount if result.rowcount is not None else 0
        if reply_ids:
            placeholders = ",".join("?" for _ in reply_ids)
            result = conn.execute(
                f"UPDATE replies SET archived_at = ? WHERE id IN ({placeholders})",
                [ts, *reply_ids],
            )
            archived_replies = result.rowcount if result.rowcount is not None else 0
        audit(conn, "gmail.batch_archived", "gmail_item", "", "Batch archived local Gmail items", {"drafts": archived_drafts, "replies": archived_replies})
    return {"ok": True, "archived": archived_drafts + archived_replies, "drafts": archived_drafts, "replies": archived_replies}


def delete_mail_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    draft_ids, reply_ids = _normalize_mail_items(items)
    if not draft_ids and not reply_ids:
        raise ValueError("No mail items selected.")
    with connect() as conn:
        deleted_drafts = 0
        deleted_replies = 0
        if draft_ids:
            placeholders = ",".join("?" for _ in draft_ids)
            result = conn.execute(f"DELETE FROM outreach_drafts WHERE id IN ({placeholders})", draft_ids)
            deleted_drafts = result.rowcount if result.rowcount is not None else 0
        if reply_ids:
            placeholders = ",".join("?" for _ in reply_ids)
            result = conn.execute(f"DELETE FROM replies WHERE id IN ({placeholders})", reply_ids)
            deleted_replies = result.rowcount if result.rowcount is not None else 0
        audit(conn, "gmail.batch_deleted", "gmail_item", "", "Batch deleted local Gmail items", {"drafts": deleted_drafts, "replies": deleted_replies})
    return {"ok": True, "deleted": deleted_drafts + deleted_replies, "drafts": deleted_drafts, "replies": deleted_replies}


def save_reply(kol_id: str, reply_text: str, account_email: str = "", intent: str = "needs_review", language: str = "en") -> dict[str, Any]:
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
        subject, body = generate_email_copy_with_model(kol, "", language, None, "follow_up", reply_text)
        draft_id = new_id("draft")
        conn.execute(
            """
            INSERT INTO outreach_drafts (id, kol_id, type, status, to_email, from_account, subject, body, risk_labels, external_sent, created_at, updated_at)
            VALUES (?, ?, 'follow_up', 'pending_review', ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (draft_id, kol_id, kol.get("email", ""), account_email, subject, body, dumps(["manual_review_required", "follow_up"]), ts, ts),
        )
        audit(conn, "reply.saved", "reply", reply_id, "保存回复并生成二次跟进草稿", {"language": language})
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


def list_supported_models(provider: str = "openai", base_url: str = "", api_key: str = "") -> dict[str, Any]:
    saved = get_model_config(include_secret=True)
    provider = provider or saved.get("provider", "openai")
    base = (base_url or saved.get("baseUrl", "") or "").strip().rstrip("/")
    api_key = api_key or saved.get("apiKey", "")
    if not base:
        raise ValueError("Base URL is required before fetching models.")

    provider_key = (provider or "").strip().lower()
    if provider_key == "local" or "ollama" in base.lower():
        endpoint = f"{base}/api/tags"
    else:
        endpoint = f"{base}/models"

    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise ValueError(f"Model list request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Model list request failed: {exc.reason}") from exc

    models: set[str] = set()
    candidates = []
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            candidates.extend(payload["data"])
        if isinstance(payload.get("models"), list):
            candidates.extend(payload["models"])
    elif isinstance(payload, list):
        candidates.extend(payload)

    for item in candidates:
        if isinstance(item, str):
            models.add(item)
        elif isinstance(item, dict):
            model_id = item.get("id") or item.get("name") or item.get("model")
            if model_id:
                models.add(str(model_id))

    if not models:
        raise ValueError("No model names were found in the provider response.")
    return {"ok": True, "models": sorted(models, key=str.lower), "source": endpoint}


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
