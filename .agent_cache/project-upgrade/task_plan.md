# KOL 管理工作台任务计划

## 当前目标

将「KOL 管理工作台」明确为本地 Agent 工作台，而不是传统前后端业务系统。Supabase 由用户提供并作为 KOL 业务数据库，本地 Agent 负责计算、会话处理、草稿生成和安全边界。

## 已确认信息

- 项目形态：本地桌面 Agent 工作台，使用本地 Web UI 作为操作壳。
- 后续方向：未来可能演进为多人协作版本。
- 文件策略：允许后续覆盖现有旧 demo 文件。
- Gmail 方案：需要先讨论，不直接实现真实发送。
- Agent 调度架构：参考 OpenAI Codex Harness，采用 Model + Harness = Agent。
- 用户已有 PRD 已审查，并产出完善版 `KOL_Agent_Workbench_PRD_Enhanced.md`。
- 数据库方案：Supabase 保存 KOL 业务事实；Agent 会话处理、模型上下文、提示词、草稿正文和原始邮件内容保存在本地。
- 当前阶段：已完成本地 Agent MVP 骨架，并正在修正架构表述，避免传统前后端误解。

## 阶段计划

### 阶段 0：项目规则与规划

状态：进行中

任务：

- 创建 `AGENTS.md`。
- 创建 `.agent_cache/project-upgrade/task_plan.md`。
- 创建 `.agent_cache/project-upgrade/findings.md`。
- 创建 `.agent_cache/project-upgrade/progress.md`。
- 创建 `.agent_cache/project-upgrade/handoff.md`。
- 创建 `.agent_cache/project-upgrade/web_blueprint.md`。

### 阶段 1：产品方案确认

状态：待开始

任务：

- 基于 `KOL_Agent_Workbench_PRD_Enhanced.md` 确认最终 MVP 范围。
- 明确 MVP 功能边界。
- 明确本地 Agent 运行态保存方式。
- 明确 Supabase 业务事实与本地运行态数据边界。
- 明确 Gmail 多账号安全方案。
- 明确本地 Agent Runtime 与桌面 Shell 的技术边界。
- 明确 UI 页面结构和核心业务流程。

### 阶段 2：技术方案设计

状态：待开始

任务：

- 确定桌面 Shell 技术栈。
- 确定本地 Agent Runtime 技术栈。
- 确定本地运行态数据库或文件存储方案。
- 设计 Supabase schema、RLS、同步队列和本地-only 会话表。
- 设计轻量 Harness 调度层，包括任务拆解、上下文装配、工具调用、人审、事件流和审计。
- 设计 KOL、数据集、草稿、回复、账号、审计日志的数据结构。
- 设计 Gmail OAuth/API 的安全接入方案。

### 阶段 2.5：Agent Harness 原型

状态：待开始

任务：

- 实现 `TaskRunner` 原型。
- 实现 `ContextBuilder` 原型。
- 实现 `ToolRegistry` 原型。
- 实现 `ApprovalGate` 原型。
- 实现 `EventLog` 原型。
- 实现 `ModelRouter` 原型。
- 以 KOL 数据导入、草稿生成、回复回传作为首批任务验证。

### 阶段 3：MVP 实现

状态：进行中

任务：

- 搭建本地 Agent Runtime + Desktop Shell 项目结构。已完成
- 实现数据导入。已完成
- 实现 KOL 信息提取。已完成
- 实现线索池。已完成
- 实现触达草稿生成。已完成
- 实现回复回传。已完成
- 实现人工审核队列。初版已完成
- 实现本地保存。已完成
- 实现 Supabase 业务数据同步预留。已完成
- 后续补充 Supabase SQL migration 和 RLS policy。待开始

### 阶段 4：验证与交接

状态：待开始

任务：

- 运行本地服务。
- 验证导入、提取、生成、回传和保存流程。
- 验证页面布局。
- 更新交接文档。
- 输出使用说明。

## 暂不做事项

- 不直接接入真实 Gmail 自动发送。
- 不保存 Gmail 密码。
- 不绕过浏览器或 Google 授权机制。
- 不做多人在线协作。
- 不做公网部署。
# 2026-08-22 最新计划补充

- 已完成：Gmail 草稿队列分页，解决大量草稿显示不可用问题。
- 已完成：模型配置中增加模型列表自动拉取能力，前端只展示结果，不保存 API Key。
- 后续：将模型 API Key 接入 Windows Credential Manager 或系统凭据库，再允许保存凭据引用。
- 后续：若草稿量继续增长到数百/数千条，将分页升级为服务端分页或虚拟列表。
# 2026-08-22 本轮计划补充

- 已完成：全量 KOL 选择、Gmail 授权占位配置、开发期账号占位、本地加密模型配置、文案模型调用、草稿归档/删除。
- 下一步：设计真实 Google OAuth + Gmail API 授权流程，明确多浏览器配置与 Gmail API 账号之间的映射。
- 下一步：补充模型调用的重试、限流、失败恢复、批量生成进度事件。
- 下一步：将本地加密凭据迁移为可选的系统凭据库或后续加密数据库方案。
# 2026-08-22 Gmail Batch Plan Update

- Completed: add batch archive/delete operations in the Gmail workspace.
- Completed: allow reply records to be archived locally.
- Completed: add default reply template support for draft generation.
- Completed: expose all fetched model names as selectable settings UI choices.
- Next: when real Gmail OAuth is introduced, map local batch actions to Gmail API labels only after explicit user approval.

# 2026-08-22 Reply Template Plan Update

- Completed: expose reply template edit/delete in the desktop shell.
- Completed: add local Agent route for deleting templates.
- Completed: keep reply template body/subject local-only, matching the Supabase data boundary.
- Next: add richer template categorization only after the core Gmail/OAuth safety design is settled.

# 2026-08-22 Gmail Draft Multilingual Plan Update

- Completed: make Gmail draft language independent from panel language.
- Completed: extend draft/template language controls to major outreach markets.
- Completed: update Harness prompts and default-template lookup so selected language is respected.
- Completed: route manual reply follow-up draft generation through the selected draft language.
- Next: when Gmail OAuth is implemented, store and display per-recipient preferred language metadata without uploading generated draft bodies to Supabase.

# 2026-08-26 Gmail Settings Plan Update

- Completed: simplify Gmail settings around a browser configuration plus one or more Gmail accounts.
- Completed: add local browser executable path selection through the local Agent runtime.
- Completed: allow one browser/profile/account-group configuration to create multiple Gmail account placeholders.
- Next: real Gmail OAuth should map each saved account placeholder to a separate Google authorization record without reading browser cookies or login state.

# 2026-08-26 Gmail Folder Picker Plan Update

- Completed: separate browser executable selection from Profile/User Data folder selection.
- Completed: add local folder picker support through the same desktop Agent helper route.
- Next: browser launch/OAuth design should consume these fields only after a reviewed Gmail safety plan is approved.

# 2026-08-26 Gmail Picker Start Directory Plan Update

- Completed: pass current path/browser context into the local picker helper.
- Completed: use common Chrome/Edge directories as picker defaults.
- Completed: replace raw stale-backend `not found` picker errors with restart guidance.

# 2026-08-26 Manual KOL And Gmail Compose Plan Update

- Completed: add manual single-KOL entry to the import flow.
- Completed: add safe Gmail compose launch using configured browser account settings.
- Completed: keep Gmail sending as a human action and separate local `Record Sent` step.
- Next: design real Gmail OAuth/API sending only after the safety plan is explicitly approved.

# 2026-08-26 Gmail Sender Selection Plan Update

- Completed: replace generate-draft sender placeholder with configured Gmail account dropdown.
- Completed: block draft generation when no local Gmail account is configured.

# 2026-08-27 DeepSeek Harness Plugin Plan Update

- Completed: extract the main DeepSeek Harness plugin development pattern.
- Completed: create a bundle-style plugin for importing KOL Workbench tools into Harness.
- Next: after DeepSeek Harness is installed locally, test `dsh plugin add` against a real profile and adjust patch syntax if the installed version differs.

# 2026-08-27 Harness Console UI Plan Update

- Completed: add a DeepSeek Harness-style console mode to the local desktop shell.
- Completed: route console actions through existing safe UI flows instead of adding hidden automation paths.
- Completed: keep console trace state local-only and outside the Supabase sync boundary.
- Next: replace the current keyword router with real local Harness task events when the TaskRunner/EventLog API is expanded.

# 2026-08-27 Harness Panel UI Plan Update

- Completed: upgrade the console into a fuller Harness-style UI panel.
- Completed: add explicit Model, Harness, Tool Registry, Memory Scope, and Approval Gate regions.
- Completed: bind the panel to current local model/settings and workspace counts.
- Next: add a dedicated Harness workbench mode only if the user wants the Agent panel to become the primary page instead of a right-side operations panel.

# 2026-08-27 Harness Host UI Plan Update

- Completed: make DeepSeek Harness the top-level desktop shell framing.
- Completed: mount KOL Workbench as a plugin module in the main workspace.
- Completed: preserve existing KOL business workflows inside the plugin module.
- Next: if more plugins are added, introduce plugin switching and workspace/session lists.

# 2026-08-27 Native Harness UI Plan Update

- Completed: remove KOL actions from the first-level host header/sidebar.
- Completed: add a native Harness session board as the default work area.
- Completed: convert KOL Workbench into a collapsed bottom-right plugin dock.
- Completed: keep KOL business actions available only after opening the plugin dock.
- Next: implement a true plugin registry if the user adds additional plugins beyond KOL Workbench.

# 2026-08-27 KOL Plugin Page And Session Mention Plan Update

- Completed: replace the bottom-right KOL plugin dock with a separate page-based plugin module under the Plugins navigation item.
- Completed: make the native Harness session input usable with Enter-to-run and local session reset through New Session.
- Completed: add @KOL mention handling in the native Harness session so the current KOL plugin summary can be injected without opening the plugin page.
- Completed: keep KOL import, reply logging, lead pool, Gmail, templates, Supabase boundary, and plugin Harness console inside the plugin module.
- Next: persist native Harness sessions in local SQLite if the user wants session history beyond the current browser session.
