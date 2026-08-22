# KOL 管理工作台任务计划

## 当前目标

从零重新规划「KOL 管理工作台」项目，先建立项目规则、规划文件和 Web 启动蓝图，暂不编写业务代码。

## 已确认信息

- 项目形态：本地桌面 Web。
- 后续方向：未来可能演进为多人协作版本。
- 文件策略：允许后续覆盖现有旧 demo 文件。
- Gmail 方案：需要先讨论，不直接实现真实发送。
- Agent 调度架构：参考 OpenAI Codex Harness，采用 Model + Harness = Agent。
- 用户已有 PRD 已审查，并产出完善版 `KOL_Agent_Workbench_PRD_Enhanced.md`。
- 数据库方案：Supabase 保存重要 KOL 业务数据；Agent 会话处理、模型上下文、提示词和原始邮件内容保存在本地。
- 当前阶段：只创建 Planning with Files 风格的项目管理文件。

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
- 明确本地数据保存方式。
- 明确 Supabase 与本地 SQLite/JSON 的数据边界。
- 明确 Gmail 多账号安全方案。
- 明确是否保留现有 Python 后端或重建技术栈。
- 明确 UI 页面结构和核心业务流程。

### 阶段 2：技术方案设计

状态：待开始

任务：

- 确定前端技术栈。
- 确定本地后端技术栈。
- 确定本地数据库或文件存储方案。
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

- 搭建本地桌面 Web 项目结构。已完成
- 实现数据导入。已完成
- 实现 KOL 信息提取。已完成
- 实现线索池。已完成
- 实现触达草稿生成。已完成
- 实现回复回传。已完成
- 实现人工审核队列。初版已完成
- 实现本地保存。已完成
- 实现 Supabase 业务摘要同步预留。已完成
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
