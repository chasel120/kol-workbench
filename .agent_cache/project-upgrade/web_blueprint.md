# KOL 管理工作台 Web 启动蓝图

## 产品形态

本项目第一阶段是本地 Agent 工作台。桌面 Web 只是操作壳，通过本机控制通道调用本地 Agent Runtime；它不是传统前端 + 后端业务系统。后续可演进为多人协作 SaaS/内网后台，但 MVP 的计算和会话处理都在本地 Agent 完成。

## 目标用户

- BD 业务员：导入 KOL 数据、生成触达草稿、回传回复、确认发送。
- BD 主管：审核报价、查看进度、控制账号风险。
- 系统管理员：配置模型、配置 Gmail 授权、管理本地数据。

## 首页信息架构

首页应聚焦高频执行动作：

- 今日触达作战台。
- KOL 线索池。
- Gmail 草稿队列。
- 回复收集。
- 人工审核。
- 跟进任务。
- 数据概览。

低频功能不放首页一级菜单：

- 数据导入。
- 模型配置。
- Gmail OAuth 配置。
- 账号安全设置。
- 系统配置。

## 推荐页面

### 1. 触达作战台

用途：BD 每日主工作台。

内容：

- 今日待触达数量。
- 待审核草稿数量。
- 有意向回复数量。
- 异常账号提示。
- 快速生成草稿。
- 快速回传回复。

### 2. KOL 线索池

用途：管理导入后的 KOL 数据。

内容：

- 左侧主栏展示全部 KOL 线索信息。
- 每条线索支持勾选，用于对指定 KOL 单独生成 Gmail 草稿。
- KOL 表格。
- 邮箱。
- TikTok 主页。
- FastMoss 链接。
- 国家/地区。
- 类目/niche。
- 粉丝、播放、销量、互动率。
- 评分和优先级。
- 标签，包括邮箱状态、优先级、国家、类目和业务标签。
- 触达状态。

### 3. Gmail

用途：集中管理 Gmail 触达流程。

内容：

- 草稿。
- 已发送。
- 已回复。
- 收件人。
- 发送账号。
- 邮件主题。
- 邮件正文预览。
- 风险标签。
- 人工确认发送。
- 退回重写。
- 草稿卡片支持展开/收起预览。

### 4. 回复收集

用途：沉淀达人回复并触发二次跟进。

内容：

- 回复原文。
- 来源账号。
- 意向分类。
- 报价需求。
- 样品需求。
- 下一步动作。
- 生成二次回复草稿。

### 4.5 回复模板库

用途：沉淀可复用的触达和回复模板。

内容：

- 手动添加模板。
- AI 生成模板。
- 模板保存到本地模板库。
- 支持中英文模板。
- 支持动态字段：`{{kol_name}}`、`{{name}}`、`{{email}}`、`{{platform}}`、`{{country}}`、`{{niche}}`、`{{category}}`、`{{homepage}}`、`{{brief}}`。

### 5. 人工审核

用途：审核高风险内容。

内容：

- 报价审核。
- 佣金审核。
- 样品承诺审核。
- 合同或合作条款审核。
- AI 文案风险提示。

### 6. 设置

用途：低频系统配置。

内容：

- 设置入口位于左侧栏底部，不占用首页一级工作区。
- 面板语言：中文/英文。
- 模型 Provider。
- Base URL。
- Model Name。
- API Key：不得写入桌面 Shell 本地存储，后续应接入系统凭据库。
- Gmail OAuth Client ID。
- 本地数据目录。
- 发送限流策略。

## 核心交互原则

- 操作流程必须清晰，避免让 BD 在多个页面来回跳。
- 表格视图要适合批量扫描、筛选和比较。
- KOL 线索必须支持勾选后对指定对象发起 Agent 任务。
- AI 生成内容必须可预览和编辑。
- Agent 生成草稿必须在页面弹框内处理，展示状态变化，不只用浏览器 prompt/alert。
- 发送动作要有明确二次确认。
- Gmail 账号异常要明显提示。
- 本地保存状态要可见。

## 视觉风格

- 后台/运营工具风格。
- 信息密度中高。
- 控件稳定、清晰、克制。
- 不做营销式 hero 页面。
- 不使用大面积装饰图。
- 侧栏 + 顶部状态栏 + 主工作区布局。

## 数据模型预留

核心实体：

- Dataset
- KOLLead
- GmailAccount
- OutreachDraft
- Reply
- ReviewTask
- FollowupTask
- AuditLog
- ModelConfig

## Supabase 数据边界

本项目使用用户提供的 Supabase 保存 KOL 业务事实，但不保存 Agent 会话处理。

Supabase 保存：

- KOL 标准档案。
- KOL 联系方式。
- 数据集导入摘要。
- Campaign。
- Campaign 与 KOL 的目标关系。
- 触达状态摘要。
- 回复意向摘要。
- 审核任务摘要。
- suppression list。
- 业务审计日志。

本地保存，不上传 Supabase：

- Agent 会话全文。
- 任务运行过程。
- 模型上下文和消息。
- Prompt 运行实例。
- 未审核 AI 草稿正文。
- 原始邮件正文。
- Gmail token、cookie、密码、2FA。
- 模型 API Key。
- 原始上传文件。

桌面 Shell 必须避免直接接触 Supabase service role key。任何暴露给客户端的 Supabase 表必须启用 RLS。

## Gmail 方案蓝图

推荐方向：

- 浏览器用于业务员完成 OAuth 授权。
- 本地 Agent Runtime 保存加密 token 引用。
- 本地 Agent Runtime 通过 Gmail API 创建草稿和发送。
- 默认只生成草稿。
- 人工确认后才发送。
- 多 Gmail 账号独立队列、独立限流、独立审计日志。

暂不推荐：

- 直接保存 Gmail 密码。
- Agent 直接控制多个浏览器点击 Gmail 发送。
- 无人工确认批量发送。
- 将 token 暴露给桌面 Shell。

## Agent Harness 蓝图

本项目 Agent 架构采用 `Model + Harness = Agent` 思路。

页面不是通用聊天框，而是业务对象工作台：

- KOL 线索池承载 LeadImportAgent 和 ScoringAgent。
- Gmail 草稿队列承载 OutreachAgent 和 GmailOpsAgent。
- 回复收集承载 ReplyAgent 和 FollowupAgent。
- 人工审核承载 AuditAgent 和 ApprovalGate。
- 设置页承载 ModelRouter、Gmail OAuth 和工具配置。

Harness 调度层需要支持：

- 任务拆解。
- 上下文装配。
- 工具调用。
- 子 Agent 管理。
- 记忆闭环。
- 人审与授权。
- 事件流与进度。
- 风控与边界。

MVP 可先实现轻量本地 Harness：

- `TaskRunner`
- `ContextBuilder`
- `ToolRegistry`
- `ApprovalGate`
- `EventLog`
- `ModelRouter`

后续再评估接入 Codex SDK 或 Codex app-server，以支持持久会话、流式事件和 approval request。

## 本地 Agent 技术建议

可选方案 A：轻量本地 Agent 方案

- 桌面 Shell：单页 HTML 或 Vite。
- 本地 Agent Runtime：Python 标准库 / FastAPI / Agent SDK。
- 本地运行态：SQLite。
- 业务数据库：Supabase。
- 文件解析：openpyxl 或 pandas。
- 启动：bat 脚本。

可选方案 B：桌面应用方案

- 桌面 Shell：React/Vite。
- 外壳：Tauri 或 Electron。
- 本地 Agent Runtime：Python sidecar 或 Node。
- 本地运行态：SQLite。
- 业务数据库：Supabase。
- 凭据：系统 Keychain/Credential Manager。

## MVP 建议范围

MVP 建议先完成：

- 本地项目结构。
- 数据导入。
- KOL 线索池。
- 邮箱提取。
- 草稿生成。
- 人工审核队列。
- 回复手动回传。
- 二次回复草稿。
- 本地保存。
- Gmail 安全方案占位。

MVP 暂不完成：

- 真实 Gmail 自动发送。
- 自动读取 Gmail inbox。
- 多人协作。
- 权限系统。
- 公网部署。
# 2026-08-22 最新蓝图补充

- Gmail 工作区必须支持分页或虚拟列表。MVP 先采用分页，每页 10 条，避免大量草稿让按钮、预览和右侧信息不可见。
- Gmail 草稿卡片折叠态展示简短摘要，展开态展示完整正文，外发仍必须人工确认。
- 模型配置属于低频能力，放在左下角设置弹窗，不进入首页一级工作区。
- Model Name 支持从 Provider 自动拉取：本地 Agent 调 `/models`，前端显示到 datalist，由用户选择或手填。
- API Key 不保存到前端、本地 SQLite 或 Supabase；当前只用于本次拉取模型请求，后续应接 Windows Credential Manager 或系统凭据库。
# 2026-08-22 本轮蓝图补充

- KOL 线索池提供两类选择：当前列表全选、当前筛选条件下全部可触达 KOL 全选。
- 左下角侧栏显示当前开发期账号名称，点击打开账号占位弹窗；后续扩展注册登录、密码和账号数据保存。
- 设置弹窗承载低频配置：面板语言、模型配置、Gmail 多浏览器授权配置。
- 模型 API Key 可本地加密保存；前端不得保存到 localStorage。
- 文案生成必须通过 ModelRouter/Harness 调用模型，生成失败应展示明确错误并停留在人工操作界面。
- Gmail 草稿队列需要生命周期操作：预览、人工确认发送、存档、恢复、删除。
- Gmail 授权配置 MVP 只保存邮箱、浏览器名称、Profile 路径和备注；不得读取或保存 Gmail 密码、cookie、2FA 或浏览器登录态。
# 2026-08-22 Gmail Batch UI Update

- Gmail workspace toolbar must support selecting the current page, batch archive, and batch delete.
- Draft, sent, archived, and replied cards must render selection checkboxes.
- Archived view must combine archived local draft records and archived local reply records.
- Template Library cards must show the default template badge and provide a Set Default action.
- Model settings must show a visible list of all fetched model names, not only a single auto-filled model.

# 2026-08-22 Reply Template UI Update

- Template Library cards must provide Edit and Delete actions.
- Editing reuses the existing template dialog and pre-fills name, language, subject, and body.
- Deleting requires explicit confirmation and only removes the reusable template, not already generated Gmail drafts.
- Add Template and AI Template actions reset the dialog into create mode before generating or saving new content.

# 2026-08-22 Gmail Draft Multilingual UI Update

- Gmail draft language is a first-class outreach setting, separate from the UI panel language.
- Agent language, generate-draft language, and template language controls support English, Chinese, German, French, Spanish, Italian, Portuguese, Dutch, Polish, Japanese, Korean, and Arabic.
- The generate-draft template dropdown should prioritize templates in the selected draft language and visibly label templates from other languages.
- If no default template exists for the selected language, the Agent should generate directly in that language instead of silently using another language's default template.
- Reply logging should include a follow-up draft language selector and default to the current Agent draft language.
- Multilingual templates remain editable/deletable in the local template library and keep support for dynamic fields such as `{{kol_name}}`, `{{country}}`, `{{niche}}`, and `{{brief}}`.

# 2026-08-22 Header Simplification UI Update

- The main header can keep global shortcuts for Import Data and Log Reply.
- Template management and draft generation actions should live in their relevant workspace panels/dialogs rather than the header.
- The progress strip should show progress metrics only; language selection should remain in task dialogs/settings rather than as a visible progress-strip control.

# 2026-08-26 Panel Language UI Update

- Panel language switching must cover both static markup and dynamic render output.
- KOL lead cards must localize field labels such as Platform, Country, Category, Followers, Sales, and Score.
- Imported business values may be translated for display in English mode, but raw imported values remain unchanged in local storage and future Supabase sync.
- Filter placeholders, progress labels, Gmail batch controls, selected-count text, empty states, and template-library actions must also follow the selected panel language.

# 2026-08-26 Gmail Settings UI Update

- Gmail settings should be organized by browser configuration first, then Gmail accounts under that configuration.
- Browser executable path should be selected with a browse action in the local desktop app instead of being typed manually.
- A single browser/profile/account-group entry may contain multiple Gmail accounts entered one per line or comma-separated.
- The UI must continue to state that saved Gmail entries are placeholders only and do not read passwords, cookies, 2FA, or browser login state.

# 2026-08-26 Gmail Path Picker UI Update

- Browser setup must show separate controls for the browser executable and the Profile/User Data folder.
- The executable control should open a file picker; the Profile/User Data control should open a folder picker.
- Both browse actions are desktop-only helpers backed by the local Agent, not browser-only file inputs.

# 2026-08-26 Gmail Path Picker Feedback Update

- Path picker actions must show click progress and errors near the path fields, not only at the bottom of a scrollable settings dialog.
- If the local Agent picker route is stale or unavailable, the settings dialog should visibly report the failure in the Gmail authorization section.

# 2026-08-26 Gmail Path Picker Start Directory Update

- Browser path pickers should open near the most likely location: current input value first, then known Chrome/Edge directories.
- A raw backend `not found` message should never be shown directly to the user; explain that the local Agent process needs a restart.

# 2026-08-26 Manual KOL And Gmail Compose UI Update

- The import dialog should support both bulk file/CSV import and a compact manual single-KOL form.
- Manual entries should return to the same lead pool immediately and be ready for draft generation.
- Pending Gmail draft cards should separate `Open Gmail Compose` from `Record Sent`; opening Gmail is not the same as sending.
- Browser/Profile compose launch should provide operational convenience while keeping final send confirmation in Gmail and status recording in the workbench.

# 2026-08-26 Gmail Sender Selection UI Update

- Generate-draft sender selection must list configured Gmail accounts, not a development placeholder.
- If no Gmail account exists, the dialog should show a clear setup-required message and prevent draft generation.

# 2026-08-27 Harness Plugin UI/Product Note

- The Harness plugin is not a new UI surface; it exposes the existing local desktop Web runtime to external Harness agents.
- Product behavior should still be owned by the KOL Workbench UI and local Agent API, while Harness tools orchestrate the same approved actions.

# 2026-08-27 Harness Console UI Update

- The desktop shell now includes a Harness Console surface in the right-side workspace.
- Console layout should resemble an agent harness: quick tool chips, command input, local runtime status, and chronological `planner/tool/result` trace cards.
- Console commands should route users into existing workflow panels/dialogs rather than bypassing review gates.
- The KOL lead pool and Gmail queue remain the primary operating surfaces; the console is an orchestration layer for visibility and task routing.
- The console trace should be visually compact, scrollable, and local-only.

# 2026-08-27 Harness Panel UI Update

- The Harness surface should read as a full agent control panel, not a simple terminal card.
- Required panel regions: `Model -> Harness` architecture strip, Task Runner lane, Tool Registry lane, Memory Scope lane, Approval Gate lane, quick tool chips, event stream, and command input.
- The panel should show live operational counts from local state where available.
- The panel may use a focused dark console treatment inside the otherwise light operational dashboard, as long as it remains compact and readable.

# 2026-08-27 Harness Host UI Update

- The first-level UI should read as a DeepSeek Harness-style host, with KOL presented as an installed plugin module.
- Required host regions: active profile, plugin id, local runtime, model summary, registered tools summary, memory scope, and approval boundary.
- The KOL plugin module should own the lead pool, Gmail queue, template library, Supabase boundary, and plugin-specific Harness console.
- Future modules should be added as additional plugin frames rather than as first-level app rewrites.

# 2026-08-27 Native Harness Host With Docked Plugin

- The default viewport should show native Harness concepts only: workspaces, sessions, runtime/model status, memory, tool service, approval gate, and plugin registry.
- KOL business controls must not be first-level header/sidebar items.
- KOL Workbench should appear as a compact docked plugin bar until clicked.
- When expanded, the KOL plugin dock may show its own progress, lead pool, Gmail queue, template library, Supabase boundary, and plugin-specific Agent Harness panel.
- Header-level import/reply shortcuts should remain inside the KOL plugin dock because they are plugin actions.

# 2026-08-27 Page-Based KOL Plugin UI Update

- The docked plugin bar has been replaced by a page-based plugin module.
- The default page remains the native Harness workspace with Workspaces, Sessions, and Runtime cards.
- The Plugins navigation item opens the KOL Workbench plugin page as a full workspace module.
- KOL plugin actions stay inside that page: Import Data, Log Reply, lead pool, Gmail queue, template library, Supabase boundary, and plugin-specific Harness console.
- The native Harness session can mention `@KOL` to inject a concise plugin summary into the current local session.
- The `@KOL` mention should not navigate automatically unless the user asks to open or switch to the plugin page.

# 2026-08-27 Native Session Intent UI Update

- The native Harness session should answer model-status questions in the transcript instead of opening Settings.
- Explicit configuration wording should open the Settings dialog.
- Modal dialogs should be opened through the shared helper so future dialog behavior remains consistent.
