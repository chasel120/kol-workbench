# KOL 管理工作台发现记录

## 已知上下文

- 工作目录：`D:\yloy\Documents\WorkBench`
- 当前已有旧版 demo：
  - `kol-bd-workbench-demo.html`
  - `kol_agent_server.py`
  - `start_kol_agent_workbench.bat`
  - `KOL-Agent-RPD.md`
  - `kol_agent_data/`
- 用户希望重新开始一个新项目：「KOL 管理工作台」。
- 用户明确当前项目形态应是本地 Agent 工作台，桌面 Web 只是操作壳，未来可能考虑多人协作版本。
- 用户允许后续覆盖现有文件。
- Gmail 方案需要进一步讨论。
- 用户提供 OpenAI Harness 参考图和文章，希望 Agent 调度架构参考 Model + Harness = Agent。

## 业务发现

当前目标产品服务 KOL BD/运营工作流，主要覆盖：

- KOL 数据导入。
- KOL 邮箱和主页提取。
- 线索管理。
- Gmail 多账号触达。
- AI 生成首触达文案。
- 有意向回复回传。
- AI 生成二次回复。
- 人工确认后发送。
- 本地数据沉淀。

## 技术发现

- 当前目录已有 Python + 单 HTML demo。
- 当前已有本地数据目录 `kol_agent_data`。
- 不应按传统“前端 + 后端”理解项目；正确形态是本地 Agent Runtime + Desktop Shell + Supabase 业务数据库。
- 若要真实 Gmail 发送，应优先走 Google OAuth + Gmail API，而不是脚本控制多个浏览器点击 Gmail UI。
- OpenAI 文章强调 Harness 负责上下文、工具调用、边界、人审、事件和跨轮推进；该思路适合作为本项目 Agent 调度层。
- 本项目不应做成单纯聊天框，而应将 Agent 嵌入线索池、草稿队列、回复记录、审核任务和 Gmail 账号等业务对象。
- 用户提供 `D:\yloy\Documents\KOL_Agent_Workbench_PRD.pdf`，原 PRD 已覆盖产品概述、分层架构、数据导入、LLM 文案、邮件触达、回复识别、二次沟通、非功能需求。
- 原 PRD 主要缺口：MVP 边界不清、Gmail 安全方案偏 SMTP/IMAP、Agent Harness 缺失、数据模型缺失、角色权限缺失、验收标准不足。
- 已产出 `KOL_Agent_Workbench_PRD_Review.md` 和 `KOL_Agent_Workbench_PRD_Enhanced.md`，后续产品和技术方案应以增强版为基础。
- 用户新增要求：KOL 信息和部分重要业务信息需要保存到 Supabase；所有会话处理必须保存在本地，不上传数据库。
- 已新增 `supabase_data_architecture.md`，定义 Supabase 云端业务数据、本地会话数据、敏感凭据和同步边界。
- 2026-08-22 已实现新的本地 Agent MVP 骨架：`agent_runtime/`、`desktop_shell/index.html`、`start_kol_workbench.bat`。
- 本地 Agent Runtime 使用 Python 标准库和 SQLite 运行态库，不依赖外部包，便于本地桌面环境启动。
- Supabase 目前通过环境变量 `SUPABASE_URL` 和 `SUPABASE_SERVICE_ROLE_KEY` 预留同步接口；未配置时业务数据先落本地缓存，后续应以 Supabase 作为 KOL 业务事实库。
- 用户运行时出现“Agent 运行失败”，根因是本地 Agent 未监听端口或页面从 file/旧 HTML 入口打开。已调整桌面 Shell 在 file 协议下请求 `http://127.0.0.1:8766`，并让启动脚本自动打开正确地址。
- 用户反馈工作台右侧内容不可见、栏目不能收缩、顶部指标太占空间。已将 UI 调整为更紧凑的后台工作台布局，重点防止表格和工具条撑宽页面。
- 用户要求 KOL 线索支持勾选单独发起邮件、Agent 支持中英文、回复模板可保存且支持动态占位符。已增加本地模板表、KOL 标签字段、模板 API、AI 模板生成 API 和按选中 KOL 生成草稿 API。
- 用户反馈左侧栏目点击没有反应。根因是导航按钮只有视觉样式，没有绑定目标区域行为。已补充导航事件、目标区域高亮、自动展开和 Gmail Tab 切换。
- 用户要求左下角增加设置，包含面板语言和大模型设置，并反馈 KOL 线索池收缩后模块消失。已新增设置弹窗、语言配置和模型配置占位，并增强收缩态可见性。
- 用户反馈数据太多会把按钮挤到最底下，左边栏目应该悬浮固定。已将页面改为 100vh 应用布局，侧栏固定，线索/Gmail/右侧信息分别内部滚动。
- 端到端验证已通过：导入、提取、生成草稿、保存回复、生成 follow-up 草稿。

## 风险发现

- Gmail 多账号自动发送涉及账号安全和平台风控。
- 自动化浏览器发送邮件不可控，容易误发或触发风控。
- 保存账号密码、cookie、token、API Key 都属于高风险。
- AI 生成外发内容必须有人审，尤其是报价、佣金、样品、合同和承诺。
- Harness 层如果没有统一 ApprovalGate，容易让多个子 Agent 绕过人审边界。
- 如果将 Agent 会话、模型消息、Prompt、未审核草稿或原始邮件全文上传 Supabase，会违反用户明确的数据边界要求。
- Supabase 客户端访问必须启用 RLS；service role key 不能出现在桌面 Shell。

## 待确认问题

- 新项目是否复用现有 `kol_agent_server.py`，还是完全新建目录和技术栈。
- 是否需要 Electron/Tauri 打包成本地桌面应用。
- 本地 Agent 运行态存储使用 JSON 文件还是 SQLite。
- Gmail 先做 OAuth 方案文档，还是先做安全占位 UI。
- 多人协作版本是否需要预留组织、角色和权限模型。
- 轻量 Harness 是先手写本地调度层，还是直接接入 Codex SDK / app-server。
- Supabase MVP 是否先只同步 KOL/Contact/Campaign/Outreach 摘要，还是同时启用 Auth 和组织角色。
# 2026-08-22 最新发现

- 草稿数量达到 50+ 时，单页渲染全部卡片会挤压 Gmail 工作区，导致列表像横线堆叠、操作按钮不可见。已改为分页渲染，默认每页 10 条。
- 模型配置不能只依赖手填模型名，用户需要从 Provider 自动拉取支持模型。已新增 `/api/models/list`，由本地 Agent 临时使用 Base URL 与 API Key 拉取模型列表。
- 模型 API Key 仍属于高敏凭据，本次实现仅用于请求，不保存到桌面 Shell、SQLite 或 Supabase。
- 运行中的旧本地 Agent 进程不会自动加载 Python 后端代码变更；若已经启动过，需要重启 `start_kol_workbench.bat` 后模型拉取接口才会生效。
# 2026-08-22 本轮发现

- “全选”需要区分当前可见列表和当前筛选条件下全部可触达 KOL；已新增 `/api/kols/ids` 支持全量选择。
- 模型 API Key 可以在本地阶段使用 Windows DPAPI 加密保存到 SQLite；桌面 Shell 只通过本地 Agent API 提交，不写 localStorage。
- 所有文案生成应从 Harness 调用模型，静态模板只能作为旧代码遗留，不作为正式生成路径。
- Gmail 多浏览器配置当前只能做授权占位和账号队列配置，不能保存 Gmail 密码、cookie 或浏览器登录态。
- 草稿需要生命周期管理：pending_review、sent_recorded、archived，以及本地删除。
# 2026-08-22 Gmail Batch Findings

- Gmail queue items span two local tables: outreach drafts and manually logged replies.
- Draft archive can reuse `outreach_drafts.status = archived`, but replies need their own `archived_at` field to leave the active replied tab.
- Model fetching already returned multiple names from the local Agent, but the UI only exposed them through a datalist and auto-filled the first value; a visible selectable list is clearer.
- Reply templates had an implicit seed default id but no durable default marker; `reply_templates.is_default` is now the local MVP marker.

# 2026-08-22 Reply Template Findings

- The existing `save_template` Harness function already supported update by id, but the desktop shell did not expose edit controls or send the id when saving.
- The local API had list/create/update template routes, but no delete route.
- Reply template content can contain reusable outreach wording and dynamic fields, so it must remain local-only unless a future explicit sanitized sync design is approved.

# 2026-08-22 Batch Delete Findings

- The repository already contained `/api/gmail/delete-batch`, but the user's live service at `127.0.0.1:8766` returned `not found`, so the browser was connected to a stale local Agent process.
- The stale backend still supports single-draft lifecycle routes, so the desktop shell can safely fall back to per-draft calls for selected draft batch delete/archive.
- Multiple Python processes were observed listening on port 8766; stale local Agent processes are a recurring operational risk until the launcher handles restart or port ownership more explicitly.

# 2026-08-22 Template Delete Findings

- Template deletion cannot be polyfilled against the stale backend because older Agent builds do not expose any template delete route.
- The desktop shell had three `renderTemplates()` definitions; JavaScript used the last one, but the duplicates created unnecessary maintenance risk.
- The Harness `delete_template()` path is valid in the current code and correctly reassigns a fallback default template when deleting the current default.

# 2026-08-22 Default Template Findings

- Default template selection cannot be polyfilled against the stale backend because older Agent builds do not expose `/api/templates/default`.
- `set_default_template()` works in the current Harness code and keeps exactly one default for a language/scenario pair.
- The desktop shell previously did not catch errors from `setDefaultTemplate()`, so a missing backend route looked like no UI response.

# 2026-08-22 Gmail Draft Multilingual Findings

- Gmail draft language must be treated as an outreach content setting, not as the same thing as the UI panel language.
- The previous default-template lookup could reuse a default template from another language, which could make a German or Japanese generation inherit English wording.
- Reply follow-up draft generation was previously hard-coded to English and needed to share the same draft language path as first-touch generation.
- The model prompt needs both a readable language name and a strict instruction to write the entire email/template in the selected language.
- Reply template metadata can store arbitrary language codes locally; no SQLite migration is required for multilingual template support.
- Draft subject/body remain local runtime data and must not be synced to Supabase by default, regardless of language.

# 2026-08-22 Header Cleanup Findings

- Import Data and Log Reply remain useful as global shortcuts; Add Template and Generate Draft duplicated workspace-specific actions and made the top bar visually crowded.
- The visible Agent language selector in the progress strip duplicated language controls in draft/reply workflows and distracted from the progress metrics.

# 2026-08-26 Dynamic UI Language Findings

- Panel language switching previously only updated static `[data-i18n]` text, so KOL card field labels, filter placeholders, progress labels, Gmail batch controls, and template-card actions could remain Chinese when the panel was set to English.
- KOL country/category/tag values can come from imported FastMoss data and may be Chinese business values, so the desktop shell needs a lightweight display mapping for common markets and niches while preserving the underlying raw data.

# 2026-08-26 Gmail Settings Findings

- The previous Gmail settings UI forced one Gmail email per browser/profile form submission, which made the common “one browser profile contains multiple Gmail accounts” workflow cumbersome.
- Browser path entry should not be a free-form operational burden; the local desktop Agent can open a native file picker and return only the selected browser executable path.
- Storing a browser path and account placeholders is still a safe MVP boundary because it does not read passwords, cookies, OAuth tokens, 2FA codes, or browser login state.

# 2026-08-26 Gmail Folder Picker Findings

- Business users distinguish the browser program path from the browser Profile/User Data folder; both need explicit controls.
- Browser-native file inputs cannot reliably expose a local folder path for this desktop workflow, so folder selection must go through the local Agent helper route.
- If the current running Agent process is stale, the UI may look correct while `/api/system/select-path` is unavailable; users should restart the local Agent after pulling this change.

# 2026-08-26 Gmail Picker No-Response Findings

- Opening Tk file dialogs directly inside `ThreadingHTTPServer` request threads can look like a no-op on Windows because the dialog may fail to surface or block the request thread.
- Path-picker feedback must be close to the clicked buttons; writing errors only to the bottom of a scrollable settings dialog makes failures look invisible.

# 2026-08-26 Gmail Picker Default Directory Findings

- A raw `not found` response in the picker section indicates the browser is still talking to an older local Agent process without `/api/system/select-path`.
- File/folder pickers should use user-entered path context first, then fall back to common Chrome/Edge directories, so users are not dropped into a root directory.

# 2026-08-26 Manual KOL And Gmail Compose Findings

- BD users need a fast path for one-off KOL leads that are not present in a FastMoss export.
- Manual KOL creation can reuse the same scoring/tagging/sync-queue path as uploaded datasets by creating a `manual` dataset wrapper.
- The safe next step for Gmail integration is launching a prefilled compose window in the configured browser profile, not automatic sending.
- Launching Gmail via browser path/Profile is local configuration assistance and must remain separate from OAuth authorization or Gmail API sending.

# 2026-08-26 Gmail Generate Account Selection Findings

- The generate-draft dialog still had a hard-coded development sender value, so configured Gmail accounts were only available as suggestions rather than the actual selected sender.
- Sender selection should be a controlled dropdown backed by local `gmail_accounts`, because this is an operational account choice rather than free-form campaign text.

# 2026-08-27 DeepSeek Harness Plugin Findings

- DeepSeek Harness plugin development is centered on Cordis services: a plugin exports `apply(ctx)` and registers capabilities through injected services.
- Tool plugins should inject `tools` and register model-callable tools through `defineTool`.
- A bundle package can declare `dsh.bundle.patch` in `package.json`, making it installable into a Harness profile.
- KOL Workbench should be exposed to Harness through local Agent API tools, not by importing SQLite internals directly.

# 2026-08-27 Harness Console UI Findings

- The existing workspace needed a visible agent-operating surface, not a generic chat box.
- A Harness-like UI works best as a local command console plus tool trace beside the Gmail workflow, because the main business objects remain KOL leads, drafts, templates, and Supabase boundaries.
- The console should route to existing approved UI flows instead of silently mutating data; draft generation still opens the human-reviewed generation dialog.
- Local trace items can improve operator confidence, but they must remain runtime UI state and must not become Supabase sync data.
