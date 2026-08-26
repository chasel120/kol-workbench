# KOL 管理工作台交接说明

## 当前交接状态

本项目刚进入重新规划阶段，当前只建立项目规则、计划和蓝图文件，尚未开始新业务代码实现。

## 后续 Agent 必读文件

后续 Agent 开始任何开发前，必须读取：

1. `AGENTS.md`
2. `.agent_cache/project-upgrade/task_plan.md`
3. `.agent_cache/project-upgrade/findings.md`
4. `.agent_cache/project-upgrade/progress.md`
5. `.agent_cache/project-upgrade/handoff.md`
6. `.agent_cache/project-upgrade/web_blueprint.md`
7. `.agent_cache/project-upgrade/agent_harness_architecture.md`
8. `.agent_cache/project-upgrade/supabase_data_architecture.md`

其中 `web_blueprint.md` 是本项目 SOP 扩展文件，不属于 Planning with Files 插件默认文件，但本项目是 Web/运营工具，因此必须读取。

其中 `agent_harness_architecture.md` 是本项目基于 OpenAI Harness 思路新增的 Agent 调度架构文件，后续设计 Agent、任务、工具、人审和 Gmail 动作前必须读取。

其中 `supabase_data_architecture.md` 是本项目的数据库边界文件，明确哪些 KOL 业务数据上传 Supabase，哪些 Agent 会话和敏感数据必须保存在本地。后续设计数据库、API、同步和安全策略前必须读取。

## 用户已确认

- 项目名称：KOL 管理工作台。
- 项目形态：本地 Agent 工作台，桌面 Web 只是本地操作壳。
- 后续方向：未来可能多人协作。
- 文件策略：允许后续覆盖现有文件。
- Gmail 方案：需要先讨论，不直接实现真实发送。
- Agent 调度架构：参考 OpenAI Codex Harness，采用 Model + Harness = Agent 思路。
- 数据库方案：用户提供 Supabase 作为 KOL 业务数据库；所有 Agent 会话处理、模型上下文、草稿正文和原始邮件内容保存在本地，不上传 Supabase。

## 当前目录情况

已有旧文件：

- `kol-bd-workbench-demo.html`
- `kol_agent_server.py`
- `start_kol_agent_workbench.bat`
- `start_kol_workbench.bat`
- `agent_runtime/`
- `desktop_shell/index.html`
- `README.md`
- `.gitignore`
- `KOL-Agent-RPD.md`
- `KOL_Agent_Workbench_PRD_Review.md`
- `KOL_Agent_Workbench_PRD_Enhanced.md`
- `kol_agent_data/`

这些文件目前没有被删除或覆盖。后续若要重构或覆盖，应先说明覆盖范围。

## 当前实现状态

2026-08-22 已完成本地 Agent MVP 骨架：

- Python 标准库本地 Agent Runtime。
- SQLite 本地运行态数据库。
- 本地 Agent 会话和任务事件。
- FastMoss xlsx/csv 导入。
- KOL 评分和线索池。
- Gmail 草稿生成。
- 回复回传和二次跟进草稿。
- Supabase 业务摘要同步预留。

启动方式：

```bat
start_kol_workbench.bat
```

访问：

```text
http://127.0.0.1:8766
```

注意：当前 Gmail 发送为安全占位，只记录发送动作，不真实对外发送。

## 重要安全提醒

Gmail 相关开发必须谨慎：

- 不保存 Gmail 密码。
- 不获取 2FA 验证码。
- 不直接接管浏览器登录态。
- 真实发送前必须完成 OAuth 授权方案设计。
- AI 生成邮件必须先进入人工审核。

## 下一步建议

建议下一轮先做产品和技术方案确认，而不是立刻写代码：

- 优先读取 `KOL_Agent_Workbench_PRD_Enhanced.md`，该文件是用户原 PRD 的完善版。
- 本地 Agent Runtime 是否继续使用 Python 标准库，还是切换到更完整的 Agent SDK / Tauri sidecar。
- MVP 是否只做数据导入、线索池、草稿、回复回传和审核。
- Gmail 是否先做安全占位，后续再接入 Google OAuth。
- 是否从旧 demo 迁移能力，还是创建全新目录结构。
- 是否先实现轻量本地 Harness，再评估 Codex SDK / app-server 接入。
- 确认用户提供的 Supabase 项目、表结构、RLS 策略和本地运行态同步队列。
- 配置 GitHub remote 后执行 push。
# 2026-08-22 最新交接

- 本次修改集中在 `desktop_shell/index.html`、`agent_runtime/harness.py`、`agent_runtime/server.py`。
- Gmail 队列现在分页显示：`state.gmailPageSize = 10`，三个 Tab 共用 `activeGmailItems()`、`updateGmailPager()` 和新版 `renderGmail()`。
- 设置弹窗增加“拉取模型”按钮：前端调用 `POST /api/models/list`，返回模型写入 `#model-options`，并在模型名为空时自动填入第一个模型。
- `/api/models/list` 支持 OpenAI-compatible `/models` 响应，也兼容部分 Ollama 风格响应。API Key 只走内存请求，不落盘。
- 注意：如果本地服务已在 8766 运行，需要重启 `start_kol_workbench.bat` 才能加载新的 Python 接口；HTML 改动可通过刷新页面看到。
# 2026-08-22 本轮交接

- 新增文件：`agent_runtime/secure_store.py`，使用 Windows DPAPI 加密/解密模型 API Key。
- `agent_runtime/storage.py` 新增 `app_settings`、`gmail_accounts`、`local_user_profiles` 表，并给 `outreach_drafts` 增加 `archived_at`。
- `agent_runtime/harness.py` 新增设置、用户占位、Gmail 配置、全量 KOL ID、草稿归档/恢复/删除、模型调用函数。
- `agent_runtime/server.py` 新增 `/api/settings`、`/api/settings/model`、`/api/settings/user`、`/api/gmail-accounts`、`/api/kols/ids`、`/api/drafts/archive|restore|delete`。
- `desktop_shell/index.html` 新增全量全选、账号入口、设置内 Gmail 配置、已存档 Tab、草稿删除/存档按钮。
- 当前真实 Gmail OAuth 仍未实现，只保存多浏览器授权占位配置；真实授权和发送仍需后续明确安全方案。
- 本轮后必须重启本地 Agent 服务，旧 8766 进程不会自动加载新增 Python 接口。
# 2026-08-22 Gmail Batch And Default Template Handoff

- New local API routes: `POST /api/gmail/archive-batch`, `POST /api/gmail/delete-batch`, and `POST /api/templates/default`.
- `reply_templates.is_default` and `replies.archived_at` are added through `storage.init_db()` migrations.
- The Gmail queue now uses `state.gmailSelected` with keys like `draft:<id>` and `reply:<id>` for batch actions.
- Archived tab includes archived drafts and archived replies.
- Model fetch renders all returned model names in `#model-list`; clicking `使用` writes the chosen value into `#setting-model-name`.
- Restart `start_kol_workbench.bat` after pulling this change so the new local Python routes and SQLite migrations load.

# 2026-08-22 Reply Template Handoff

- `desktop_shell/index.html` now renders Edit/Delete actions for each reply template card.
- `#template-dialog` uses hidden `#tpl-id` to distinguish create vs update.
- `POST /api/templates/delete` deletes a local reply template by id.
- Existing drafts are not deleted when a template is deleted; drafts keep their already-rendered subject/body.
- If the local Agent service is already running, restart `start_kol_workbench.bat` so the new Python route is loaded.

# 2026-08-22 Batch Delete Compatibility Handoff

- `desktop_shell/index.html` now catches `not found` from `/api/gmail/archive-batch` and `/api/gmail/delete-batch`.
- When the batch route is missing, selected `draft:<id>` items are archived/deleted one by one through `/api/drafts/archive` or `/api/drafts/delete`.
- Selected `reply:<id>` items still need the current backend routes; ask the user to restart `start_kol_workbench.bat` if reply batch actions fail.
- If the user sees `not found` again after refreshing the page, stop stale Python processes bound to port 8766 and restart the workbench from the current repository.

# 2026-08-22 Template Delete Handoff

- `desktop_shell/index.html` now has one `renderTemplates()` implementation with default/edit/delete controls.
- Template action clicks use event delegation via `closest("[data-edit-template], [data-delete-template], [data-default-template]")`.
- If `/api/templates/delete` returns `not found`, the UI now tells the user the local Agent is stale and must be restarted.
- Current-code smoke validation passed for creating a template, setting it as default, deleting it, and assigning a fallback default.

# 2026-08-22 Default Template Handoff

- `desktop_shell/index.html` now renders `#template-library-toast` below the template list.
- `setDefaultTemplate()` catches stale-route errors and writes a clear restart instruction into the template-library status line.
- Template delete failures also write to the same status line.
- Removed the duplicate `renderTemplateOptions()` function; the remaining version marks the current default in the generate-draft template dropdown.

# 2026-08-22 Gmail Draft Multilingual Handoff

- `desktop_shell/index.html` now supports draft/template language selection for `en`, `zh`, `de`, `fr`, `es`, `it`, `pt`, `nl`, `pl`, `ja`, `ko`, and `ar`.
- `draftLanguage` is saved in browser local settings separately from `panelLanguage`.
- `renderTemplateOptions()` now prioritizes templates that match the selected draft language and labels other-language templates.
- `POST /api/replies` accepts `language` so reply follow-up drafts use the selected multilingual draft language.
- `agent_runtime/harness.py` now maps language codes to readable names for model prompts and uses language-specific default-template lookup.
- Restart `start_kol_workbench.bat` after pulling this change so the updated Python Harness prompt behavior is loaded.

# 2026-08-22 Header Cleanup Handoff

- The main header keeps only Import Data and Log Reply global shortcuts.
- Add Template and Generate Draft remain removed from the header and should be accessed from workspace panels/dialogs.
- The progress strip no longer shows the Agent language selector. `#agent-language` remains hidden in the DOM to preserve the existing draft-language state bridge.

# 2026-08-26 Dynamic UI Language Handoff

- `desktop_shell/index.html` now tracks the current panel language in `state.panelLanguage`.
- Dynamic renderers should use `uiText()` for UI labels and `translateBusinessValue()`/`localizedTag()` for display-only imported values.
- Do not mutate stored KOL country/category/tag data when adding translations; translate only at render time.
- If adding new dynamic UI text, add dictionary keys to both `i18n.zh` and `i18n.en` instead of hard-coding Chinese in render functions.

# 2026-08-26 Gmail Settings Handoff

- `gmail_accounts.browser_path` is now a local SQLite field created by `storage.init_db()`.
- `POST /api/gmail-accounts/batch` accepts `emails`, `browserName`, `browserPath`, `browserProfile`, and `notes`, then creates one local placeholder row per email.
- `POST /api/system/select-path` opens a local native file picker for selecting a browser executable path. It is a desktop-only helper and should not be treated as a web/SaaS pattern.
- The Gmail settings UI now uses `#gmail-emails` for multiple accounts and `#gmail-browser-path` for the selected browser executable.
- This remains an authorization placeholder only; no Gmail password, browser cookie, OAuth token, 2FA code, or login state is read or stored.
- Restart `start_kol_workbench.bat` after pulling this change so the new backend routes and SQLite migration load.

# 2026-08-26 Gmail Folder Picker Handoff

- Gmail settings now expose two separate local path fields: `#gmail-browser-path` for the browser executable and `#gmail-browser-profile` for the Profile/User Data folder.
- `#browse-browser-path` calls `/api/system/select-path` with `kind: "file"`; `#browse-browser-profile` calls the same route with `kind: "directory"`.
- The Python `select_local_path()` helper sets the Tk dialog as topmost and passes the hidden root as parent so the picker is less likely to appear behind the browser.
- If clicking either browse button has no visible effect, first restart `start_kol_workbench.bat` so the currently running local Agent loads the updated route and script.

# 2026-08-26 Gmail Picker No-Response Handoff

- `agent_runtime.server.select_local_path()` now launches the Tk picker in a short-lived Python subprocess and returns stdout as the selected path.
- This avoids opening Tk dialogs directly from HTTP worker threads, which was the likely cause of the browse buttons appearing to do nothing.
- `desktop_shell/index.html` now renders `#gmail-path-toast` directly below the two path fields and writes picker progress/failure there as well as to the settings footer toast.
