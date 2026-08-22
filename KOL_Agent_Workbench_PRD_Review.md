# KOL Agent Workbench PRD 审查报告

来源文件：`D:\yloy\Documents\KOL_Agent_Workbench_PRD.pdf`  
审查日期：2026-08-21  
项目形态：本地桌面 Web，后续预留多人协作版本  

## 总体评价

原 PRD 已经明确了产品方向：通过 KOL 数据导入、LLM 文案生成、邮件触达、回复识别和二次沟通草稿形成营销闭环。

但当前文档仍偏概念层，距离可直接交给开发、测试和 UI 执行还有明显缺口。主要问题集中在：产品边界不够清晰、安全方案过于粗略、Gmail 接入方式存在风险、Agent 调度架构未定义、数据结构和验收标准不足。

## 优点

- 已覆盖完整业务链路：导入、筛选、生成、触达、回复、二次沟通、人工确认。
- 已意识到 Human-in-the-loop 的必要性。
- 已提出多层架构：展示层、业务逻辑层、模型与外部服务层、数据层。
- 已覆盖基础非功能需求：安全、发信风控、性能、易用性。
- 功能优先级中已标注 P0，有助于后续 MVP 拆分。

## 主要问题

### 1. 产品范围过宽，MVP 边界不清

原文同时提到跨境电商、数字营销、多平台 KOL、自动邮件触达、自动监听、第三方数据抓取、报表 Dashboard 等能力，但没有说明第一阶段必须做什么、暂不做什么。

建议：

- 第一阶段聚焦本地桌面 Web。
- 数据源优先支持 FastMoss xlsx/csv。
- 触达渠道优先 Gmail。
- 回复回传先支持手动录入，再考虑 Gmail 自动同步。
- 多人协作、第三方抓取、完整 Dashboard 放到 V2/V3。

### 2. Gmail 方案存在安全风险

原文写到 SMTP/IMAP 自动触达和监听，但对 Gmail 多账号场景而言，直接 SMTP/IMAP 或保存账号密码都不适合作为首选方案。

风险：

- 可能要求保存 Gmail 密码或 app password。
- 无法清晰管理每个账号授权边界。
- 难以做撤销授权、权限最小化和审计。
- 自动发送容易绕过人工审核。

建议：

- 浏览器只用于 Google OAuth 授权。
- 后端通过 Gmail API 创建草稿、读取回复、发送邮件。
- token 放系统凭据库，不进入前端。
- 发送动作必须经过人工确认。
- 每个 Gmail 账号独立队列、限流、暂停和审计日志。

### 3. “自动邮件触达”表述需要收敛

原文将“邮件自动触达”列为 P0，但未区分“自动生成草稿”和“自动真实发送”。

建议改为：

- P0：AI 生成 Gmail 草稿。
- P0：人工确认后记录发送动作。
- P1：接入 Gmail API 创建草稿。
- P1/P2：人工确认后通过 Gmail API 发送。
- 禁止无审核批量发送。

### 4. Agent 架构不足

原文提到“回复解析 Agent、草稿生成 Agent”，但没有定义 Agent Harness、任务拆解、工具调用、人审网关、事件流、记忆闭环。

建议补充：

- Model + Harness = Agent。
- Harness 调度层包含 TaskRunner、ContextBuilder、ToolRegistry、ApprovalGate、EventLog、ModelRouter。
- 子 Agent 包含 LeadImportAgent、ScoringAgent、OutreachAgent、ReplyAgent、FollowupAgent、GmailOpsAgent、AuditAgent。

### 5. 数据结构缺失

PRD 没有定义核心实体字段，开发难以落库和设计 API。

建议补充：

- Dataset。
- KOLLead。
- Campaign。
- OutreachDraft。
- Reply。
- GmailAccount。
- ReviewTask。
- AuditLog。
- ModelConfig。

### 6. 权限和角色缺失

当前仅写“运营人员”，但实际至少有 BD、主管、管理员三类角色。

建议：

- BD：导入数据、生成草稿、回传回复、提交审核。
- 主管：审核报价、佣金、合同和高风险文案。
- 管理员：配置模型、Gmail OAuth、数据目录和安全策略。

### 7. 缺少可验收标准

原文描述功能，但没有明确验收条件。

建议为每个 P0 功能增加：

- 输入。
- 输出。
- 成功标准。
- 异常处理。
- 验收用例。

### 8. 合规描述过泛

原文提到 GDPR/CAN-SPAM，但没有落实到产品功能。

建议：

- 邮件内支持退订或停止联系标记。
- KOL 可加入 suppression list。
- 审计日志记录生成、审核、发送和撤回。
- 明确数据本地保存和删除机制。

### 9. 性能目标不够现实

“100 人文案 30 秒内”需要区分本地规则生成、云模型生成、并发模型调用。

建议：

- 本地解析 1000 行小于 10 秒。
- 本地评分 1000 行小于 5 秒。
- AI 草稿生成 100 人允许异步队列，前端展示进度。
- 模型调用失败可重试，不阻塞整个任务。

## 结论

原 PRD 可以作为方向稿，但需要升级为面向实施的产品需求文档。完善版应重点补充：

- MVP 边界。
- 本地桌面 Web 产品形态。
- Gmail OAuth/API 安全方案。
- Agent Harness 调度架构。
- 核心数据模型。
- 状态机。
- 人工审核规则。
- 非功能指标。
- 验收标准。
