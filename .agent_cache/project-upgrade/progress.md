# KOL 管理工作台进度记录

## 2026-08-21

### 已完成

- 用户确认新项目目标：开发「KOL 管理工作台」。
- 用户确认项目形态：本地桌面 Web。
- 用户进一步澄清：产品不是传统前后端架构，应是用户提供 Supabase 数据库，本地 Agent 负责计算。
- 用户确认未来可能考虑多人协作版本。
- 用户确认允许后续覆盖现有文件。
- 用户确认 Gmail 方案需要进一步讨论。
- 开始建立 Planning with Files 风格的项目规则与计划文件。
- 用户补充 Agent 调度架构参考 OpenAI Codex Harness。
- 已新增 `agent_harness_architecture.md`，沉淀 Model + Harness = Agent 架构。
- 已同步更新 `AGENTS.md`、`handoff.md`、`task_plan.md`、`findings.md`、`web_blueprint.md`。
- 已审查用户提供的 `KOL_Agent_Workbench_PRD.pdf`。
- 已创建 `KOL_Agent_Workbench_PRD_Review.md`，记录 PRD 问题清单。
- 已创建 `KOL_Agent_Workbench_PRD_Enhanced.md`，作为完善版 PRD。
- 用户确认数据库使用 Supabase 保存 KOL 和重要业务信息。
- 用户明确要求所有会话处理保存在本地，不上传数据库。
- 已创建 `supabase_data_architecture.md`，定义 Supabase 与本地数据边界、表结构、同步策略和 RLS 要求。

### 当前状态

项目处于规划初始化阶段。

尚未开始业务代码开发。

### 下一步

等待用户确认后，可进入产品方案确认阶段：

- 明确 MVP 功能边界。
- 明确技术栈。
- 明确数据保存方案。
- 明确 Gmail 多账号安全方案。
- 决定复用旧 demo 还是重建项目结构。
- 明确轻量本地 Harness 与 Codex SDK / app-server 的阶段关系。
- 以 `KOL_Agent_Workbench_PRD_Enhanced.md` 作为下一阶段 MVP 和技术方案确认的主要依据。
- 以 `supabase_data_architecture.md` 作为数据库、同步和数据安全设计依据。

## 2026-08-22

### 已完成

- 开始编写「KOL 管理工作台」本地桌面 Web 程序代码。
- 最初新增 `backend/` 模块，后续已重命名为 `agent_runtime/`：
  - `storage.py`：SQLite schema、本地会话、任务事件、同步队列、审计日志。
  - `importers.py`：xlsx/csv 导入和字段映射。
  - `harness.py`：轻量 Harness，支持导入、评分、草稿生成、回复回传、Supabase 同步边界。
  - `server.py`：本地 HTTP API。
- 最初新增 `frontend/index.html`，后续已重命名为 `desktop_shell/index.html`。
- 新增 `start_kol_workbench.bat`，并更新旧启动脚本指向本地 Agent Runtime。
- 新增 `.gitignore` 和 `README.md`。
- 已完成端到端验证：
  - 本地页面返回 200。
  - CSV 导入成功。
  - KOL 邮箱提取成功。
  - Gmail 草稿生成成功。
  - 回复回传成功。
  - 二次跟进草稿生成成功。
- 根据用户反馈，确认项目不应采用传统前后端架构表述。
- 已将项目结构调整为 `agent_runtime/` + `desktop_shell/`。
- 已将启动入口改为 `python -m agent_runtime.server`。
- 已更新 README，明确 Supabase 是 KOL 业务数据库，本地 Agent 只负责计算和运行态保存。
- 修复直接 file 打开桌面 Shell 时 API 连接失败的提示与连接方式。
- 启动脚本现在会自动打开 `http://127.0.0.1:8766`。
- README 已补充运行注意事项：必须保持本地 Agent 命令行窗口运行，不建议直接打开 HTML 文件。
- 根据用户截图反馈优化工作台布局：
  - 顶部四个数字卡片改为紧凑进度管。
  - 侧栏支持收缩。
  - 每个业务栏目支持收缩/展开。
  - 下方工作区支持单栏/双栏切换，并支持拖拽调整栏目位置。
  - 表格改为内部横向滚动，避免撑开主画布导致右侧信息不可见。
- 根据用户最新反馈升级 KOL BD 工作流：
  - KOL 线索池改为左侧主栏，线索卡展示完整信息、标签和可勾选状态。
  - Gmail 工作区更名为 Gmail，并拆分为草稿、已发送、已回复。
  - 生成草稿改为页面弹框流程，支持选择 KOL、发送账号、Agent 中英文和模板。
  - 草稿生成后会刷新 KOL 状态和 Gmail 草稿队列，并在弹框内展示步骤状态。
  - 新增回复模板库，支持 AI 生成模板、手动保存模板和动态字段。
  - 草稿预览改为可展开卡片，带收缩动效。
- 修复左侧导航按钮没有响应的问题：
  - 线索池/Gmail/模板库/Supabase 均绑定真实导航动作。
  - 点击导航会切换激活态、展开目标栏目并高亮对应区域。
  - Gmail 导航会自动切回草稿 Tab。
- 新增左下角设置入口：
  - 支持面板语言中文/英文切换，并保存到浏览器本地配置。
  - 增加大模型 Provider、Base URL、Model Name 配置入口。
  - API Key 输入框仅作为占位，不写入桌面 Shell 本地存储，保存后会清空。
- 修复 KOL 线索池点击收缩后像消失的问题：收缩态保留清晰标题栏、最小高度和展开按钮。
- 根据数据量过大导致按钮被挤到页面底部的问题，调整为应用级固定高度布局：
  - 左侧主导航固定在视窗高度内，底部设置入口不再随数据滚动。
  - KOL 线索列表改为栏内滚动。
  - Gmail 草稿列表和右侧模板/Supabase 信息改为各自内部滚动。
  - 主页面不再因大量数据把顶部按钮和侧栏挤走。

### 当前状态

已完成本地 Agent MVP 技术骨架。

当前版本不会真实发送 Gmail。点击人工确认发送只会记录本地发送动作。

Supabase 同步已预留本地 Agent 接口和数据边界。后续拿到用户提供的 Supabase 配置后，应让 KOL 业务事实进入 Supabase，本地只保留运行态、缓存和敏感内容。

### 下一步

- 创建 git 首次提交。
- 配置 GitHub 远程仓库后推送。
- 后续可继续补充 Supabase SQL migration、RLS policy 和真实 Google OAuth 设计。
# 2026-08-22 最新补充

## 已完成
- Gmail 草稿队列增加分页显示，当前每页显示 10 条，避免 50+ 草稿挤压列表导致卡片和按钮不可见。
- Gmail 草稿卡片增加折叠态正文摘要，保留预览展开动效。
- 设置弹窗的 Model Name 增加“拉取模型”按钮和 datalist 建议列表。
- 本地 Agent Runtime 新增 `/api/models/list`，按 OpenAI-compatible `/models` 响应解析 `data[].id`；同时兼容本地 Ollama 风格 `models/name/id`。
- API Key 仅用于本次模型列表请求，不写入 localStorage、不写 SQLite、不上传 Supabase。

## 验证
- `python -m py_compile agent_runtime\harness.py agent_runtime\server.py`
- 前端脚本解析检查通过。
- 浏览器验证：当前真实数据有 58 条待审草稿，页面显示 `1-10 / 58`，点击下一页后显示 `11-20 / 58`。
- 模型列表解析使用本地 mock 验证通过。
# 2026-08-22 本轮功能补充

## 已完成
- KOL 线索池新增“全量全选”，通过本地 Agent 获取当前筛选条件下全部可触达 KOL ID。
- 设置弹窗新增 Gmail 多浏览器授权配置占位，可保存 Gmail 邮箱、浏览器名称、Profile 路径和备注。
- 左下角新增开发期账号入口，可保存账号名、邮箱和角色占位资料；当前不保存密码。
- 模型配置改为本地 Agent 保存，API Key 使用 Windows DPAPI 加密后写入本地 SQLite。
- 草稿生成、AI 模板生成、回复 follow-up 生成均改为调用配置的大模型；未配置模型时明确失败。
- Gmail 草稿增加存档、恢复和删除动作，并新增“已存档”Tab。

## 验证
- `python -m py_compile agent_runtime\storage.py agent_runtime\secure_store.py agent_runtime\harness.py agent_runtime\server.py`
- 前端脚本解析检查通过。
- 临时 SQLite 功能烟测通过：加密模型配置、Gmail 配置、账号占位、模型生成路径、KOL 全量 ID、草稿归档/恢复/删除。
- 临时 8767 服务验证 `/api/settings` 和 `/api/kols/ids` 正常。
# 2026-08-22 Gmail Batch And Default Templates

- Completed: Gmail module now supports selecting visible mail items and batch archive/delete across draft, sent, archived, and replied records.
- Completed: replies now support local `archived_at`, so replied mail can move out of the active replied tab.
- Completed: reply templates can be marked as the default version, and draft generation uses the default template when no template is manually selected.
- Completed: model fetch results are shown as a full selectable list instead of only auto-filling one model name.

# 2026-08-22 Reply Template Management

- Completed: reply templates in the local template library can now be edited from the template card.
- Completed: reply templates can now be deleted after user confirmation.
- Completed: template save flow now sends the template id when editing, so existing templates are updated instead of duplicated.
- Data boundary: template subject/body remains local SQLite runtime data and is not uploaded to Supabase.

# 2026-08-22 Batch Delete Compatibility Fix

- Completed: confirmed the live `127.0.0.1:8766` Agent still returned `{"error":"not found"}` for `POST /api/gmail/delete-batch`, which means the running process was an older backend.
- Completed: added desktop-shell fallback logic for Gmail batch archive/delete. If the batch route is missing, selected draft records are processed one by one through the older `/api/drafts/archive` and `/api/drafts/delete` routes.
- Note: reply-record batch archive/delete still requires the current Python backend routes, because older backends only expose draft lifecycle routes.

# 2026-08-22 Template Delete Fix

- Completed: confirmed the live `127.0.0.1:8766` Agent also returned `{"error":"not found"}` for `POST /api/templates/delete`, so the visible failure is caused by a stale backend process.
- Completed: removed duplicate `renderTemplates()` definitions from the desktop shell and kept the single default/edit/delete-capable renderer.
- Completed: made template action event delegation use `closest()` so button clicks remain stable if nested content is added later.
- Completed: added a clear stale-Agent error message for template deletion when the local backend has not loaded the delete route.

# 2026-08-22 Default Template Feedback Fix

- Completed: confirmed the live `127.0.0.1:8766` Agent returned `{"error":"not found"}` for `POST /api/templates/default`, so the user's current failure is caused by the same stale backend process issue.
- Completed: added a visible template-library status line for default/delete actions.
- Completed: default template setting now shows success, failure, and stale-Agent restart guidance instead of failing silently.
- Completed: removed the duplicate `renderTemplateOptions()` definition.

# 2026-08-22 Gmail Draft Multilingual Support

- Completed: Gmail draft language is now a dedicated setting, separate from the UI panel language.
- Completed: Agent language, generate-draft language, and template language selectors now support English, Chinese, German, French, Spanish, Italian, Portuguese, Dutch, Polish, Japanese, Korean, and Arabic.
- Completed: model prompts now pass a clear target language name and instruct the model to write the full email/template in that language.
- Completed: default template matching is language-specific; selecting German no longer silently falls back to an English default template.
- Completed: manually logged Gmail replies can now choose the follow-up draft language, using the same multilingual language list.
- Completed: local compatibility copy generation now has multilingual fallback text for major KOL outreach markets.
- Validation: Python compile passed, frontend script parse passed, and multilingual copy smoke test passed with UTF-8 output.

# 2026-08-22 Header Cleanup

- Completed: restored the top Import Data and Log Reply global shortcuts because they remain primary operational entry points.
- Completed: kept Add Template and Generate Draft out of the header because they are already available inside the relevant workflow panels/dialogs.
- Completed: removed the visible Agent language selector from the progress strip while preserving hidden state for the draft-language workflow.

# 2026-08-26 Dynamic UI Language Fix

- Completed: extended panel language switching to placeholders, progress labels, KOL card field labels, selected-count text, Gmail batch controls, empty states, and template-card actions.
- Completed: added common imported business-value display translations, including Germany, Other, Apparel & Accessories, Home/Furniture/Appliances, IT/Tech, and status/tag labels, without changing stored KOL data.
- Validation: frontend script parse passed.

# 2026-08-26 Gmail Settings Simplification

- Completed: redesigned Gmail settings so a single browser configuration can bind multiple Gmail account placeholders.
- Completed: added `browser_path` to the local Gmail account table and preserved `browser_profile` as an optional Profile/account-group label.
- Completed: added `POST /api/gmail-accounts/batch` and `POST /api/system/select-path`.
- Completed: changed the desktop shell to use a browse button for browser executable path selection.
- Validation: Python compile passed and frontend script parse passed.

# 2026-08-26 Gmail Folder Picker Fix

- Completed: split Gmail browser selection into browser executable path and Profile/User Data folder path.
- Completed: added a dedicated folder browse action for the Profile/User Data field.
- Completed: improved the native picker so the system dialog is parented and brought to the front.
- Validation: Python compile passed, frontend script parse passed, and `git diff --check` returned only line-ending warnings.

# 2026-08-26 Gmail Picker No-Response Fix

- Completed: moved native file/folder picker execution into a short-lived Python subprocess so Tk dialogs are not opened from the HTTP worker thread.
- Completed: added an inline path status message near the Gmail browser buttons so click progress and errors are visible without scrolling to the bottom of the settings dialog.
- Validation: Python compile passed, frontend script parse passed, and `git diff --check` returned only line-ending warnings.

# 2026-08-26 Gmail Picker Default Directory Fix

- Completed: browser executable picker now starts from the existing input path or common Chrome/Edge installation folders instead of an arbitrary root directory.
- Completed: Profile/User Data picker now starts from the existing input path or common Chrome/Edge User Data folders.
- Completed: stale `/api/system/select-path` `not found` errors now display a restart instruction instead of a raw backend message.
- Validation: Python compile passed, frontend script parse passed, default directory smoke test returned a local Chrome path, and `git diff --check` returned only line-ending warnings.

# 2026-08-26 Manual KOL And Gmail Compose Launch

- Completed: added a manual single-KOL entry path in the import dialog.
- Completed: manual KOL entries are saved into local SQLite, scored, tagged, queued for allowed business sync, and selected in the lead pool after refresh.
- Completed: added a local Gmail compose launch tool that opens the configured browser/Profile with a prefilled Gmail compose URL.
- Safety: Gmail compose launch does not auto-send, read cookies, read login state, or mark the draft as sent; users must send in Gmail and then record sent in the workbench.
- Validation: Python compile passed, frontend script parse passed, `git diff --check` returned only line-ending warnings, and a temporary SQLite smoke test passed for manual KOL creation plus Gmail launch argument generation.

# 2026-08-26 Gmail Generate Account Selection Fix

- Completed: removed the hard-coded `bd-local@gmail.com` value from the generate-draft dialog.
- Completed: generate-draft sender account now renders from locally configured Gmail accounts.
- Completed: draft generation is blocked with a visible message when no Gmail account has been configured.
- Validation: frontend script parse passed, Python compile passed, and static smoke check confirmed `#gen-account` no longer contains the placeholder sender.

# 2026-08-27 DeepSeek Harness Plugin Bundle

- Completed: reviewed the DeepSeek Harness basic development pattern and extracted the plugin structure: `apply(ctx)`, `inject = ['tools']`, `defineTool`, and `dsh.bundle.patch`.
- Completed: added `harness_plugins/kol-workbench-plugin` as a bundle-style Harness plugin for the local KOL Workbench runtime.
- Completed: exposed local tools for status, lead listing, manual lead creation, draft generation, draft listing, Gmail compose launch, and sent-record updates.
- Safety: plugin calls only the local KOL Workbench Agent API and preserves the no-auto-send Gmail boundary.
- Validation: `node --check` passed, package manifest smoke test passed, and `git diff --check` returned only line-ending warnings.

# 2026-08-27 Harness Console UI Mode

- Completed: added a DeepSeek Harness-style console surface inside the desktop shell right workspace.
- Completed: added a left navigation entry for Harness and a dark local trace panel with `planner`, `tool`, and `result` events.
- Completed: added command routing for status, draft generation, Gmail queue focus, and import/manual lead entry.
- Safety: console events are local UI/runtime traces only; raw prompts, generated mail bodies, browser paths, and credentials remain local-only and are not synced to Supabase.
- Validation: frontend script parse passed and Python compile passed.

# 2026-08-27 Harness Panel UI Refinement

- Completed: upgraded the small console card into a fuller Harness-style panel.
- Completed: widened the Gmail right-side workspace and added a visible `Model -> Harness` architecture strip.
- Completed: added Task Runner, Tool Registry, Memory Scope, and Approval Gate lanes above the event stream.
- Completed: wired the panel to live local state for model name, event count, lead/draft/reply memory counts, and pending review count.
- Safety: the richer panel is still a UI/control layer only; it does not add background Gmail sending or cloud sync of local session content.
- Validation: frontend script parse passed and Python compile passed.

# 2026-08-27 Harness Host UI And KOL Plugin Module

- Completed: reframed the desktop shell as a DeepSeek Harness-style host UI rather than a KOL-first app shell.
- Completed: changed the sidebar/header to present `DeepSeek Harness · KOL Plugin`.
- Completed: added a Harness host panel with profile, plugin id, runtime, model, tools, memory, and approval summaries.
- Completed: wrapped the existing lead/Gmail/template/Supabase workspace inside a `KOL Workbench Plugin` module frame.
- Safety: this remains a local host UI change; KOL plugin actions still use the existing local Agent API and approval boundaries.

# 2026-08-27 Native Harness UI With Docked KOL Plugin

- Completed: removed KOL business actions from the first-level header and sidebar.
- Completed: changed the first-level navigation to native Harness concepts: Workspace, Sessions, Plugins, and Models.
- Completed: added a native Harness session board with workspace list, session transcript, composer, runtime/model/tool/memory/approval cards.
- Completed: moved the KOL progress strip and all KOL business panels into a bottom-right docked plugin window.
- Completed: the KOL plugin window is collapsed by default and only expands when the user clicks the plugin bar, Plugins entry, or Open KOL Plugin action.
- Safety: no new Gmail automation or cloud sync was introduced.

# 2026-08-27 KOL Plugin Page And Session Mention

- Completed: replaced the bottom-right KOL plugin dock with a page-based plugin module.
- Completed: Plugins navigation and the top Plugins action now switch to the KOL Workbench plugin page.
- Completed: Back to Session returns from the KOL plugin page to the native Harness session.
- Completed: New Session resets the native Harness transcript and keeps the session local.
- Completed: the native Harness command input now runs on Enter and supports @KOL summary injection.
- Safety: @KOL summary uses local in-memory/workbench state only; no Gmail send, external account access, or Supabase upload was added.

# 2026-08-27 Native Session Model Intent Fix

- Completed: changed native Harness prompts such as "你是什么模型" to answer with the current ModelRouter configuration instead of opening Settings.
- Completed: kept explicit settings/configuration commands routed to the Settings dialog.
- Completed: added a shared dialog opener for Settings, Import, Generate, and Template dialogs.
- Validation: frontend script parse passed and Python compile passed.
