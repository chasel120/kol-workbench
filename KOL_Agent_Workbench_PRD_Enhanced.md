# KOL 管理工作台 PRD 完善版

版本：V1.1  
状态：Draft for Review  
日期：2026-08-21  
项目形态：本地桌面 Web，后续预留多人协作版本  
适用对象：产品、设计、前端、后端、测试、运营负责人  

## 1. 产品概述

KOL 管理工作台是一款面向跨境电商 BD/运营团队的本地桌面 Web 工具，帮助业务员完成从 KOL 数据导入、线索筛选、AI 触达草稿生成、Gmail 多账号队列、人审发送、回复回传、AI 二次回复到数据沉淀的完整闭环。

第一阶段产品定位不是“自动群发工具”，而是“带安全边界的 KOL BD Agent 工作台”。

## 2. 产品目标

### 2.1 业务目标

- 降低业务员从 FastMoss 表格中筛选 KOL 和提取邮箱的人工成本。
- 提升首触达邮件和二次回复草稿生成效率。
- 将多个 Gmail 账号的触达任务统一收敛到队列和审核流程。
- 避免未经审核的 AI 文案直接外发。
- 沉淀 KOL 状态、回复记录、草稿记录和发送审计。

### 2.2 MVP 目标

MVP 必须完成：

- FastMoss xlsx/csv 导入。
- KOL 信息标准化和邮箱提取。
- KOL 线索池与筛选。
- 本地评分和优先级排序。
- AI 首触达草稿生成。
- 草稿审核队列。
- 手动回复回传。
- AI 二次回复草稿生成。
- 本地数据保存。
- Gmail OAuth/API 安全方案占位。

MVP 暂不完成：

- 无审核批量自动发送。
- 直接控制多个浏览器点击 Gmail 页面发送。
- 保存 Gmail 密码、cookie 或 2FA。
- 多人协作权限系统。
- 公网部署。
- 自动抓取第三方平台数据。

## 3. 用户角色

### 3.1 BD 业务员

负责每日执行：

- 导入 KOL 数据。
- 查看和筛选 KOL。
- 生成触达草稿。
- 编辑和提交草稿。
- 回传 Gmail 回复。
- 确认低风险邮件发送。

### 3.2 BD 主管

负责审核和管理：

- 审核报价、佣金、样品、合同和承诺类内容。
- 查看触达效果和回复情况。
- 暂停异常 Gmail 账号或 Campaign。

### 3.3 系统管理员

负责配置：

- 模型 Provider、Base URL、Model Name、API Key。
- Gmail OAuth Client。
- 本地数据目录。
- 发送限流策略。
- 数据备份和清理策略。

## 4. 核心业务流程

### 4.1 首触达流程

1. BD 导入 FastMoss xlsx/csv。
2. 系统解析字段并生成 KOLLead。
3. 系统提取邮箱、主页、国家、类目、粉丝、播放、销量等信息。
4. ScoringAgent 计算优先级。
5. BD 选择目标线索和 Campaign brief。
6. OutreachAgent 生成 Gmail 首触达草稿。
7. 草稿进入审核队列。
8. BD 或主管预览、编辑、确认。
9. GmailOpsAgent 在授权边界内创建或发送邮件。
10. 系统写入发送记录和审计日志。

### 4.2 回复跟进流程

1. BD 收到 Gmail 回复。
2. MVP 阶段由 BD 手动回传回复。
3. ReplyAgent 识别意向类型。
4. FollowupAgent 生成二次回复草稿。
5. 涉及报价、佣金、样品或承诺时进入主管审核。
6. 人工确认后发送。
7. KOL 状态更新为 replied、followup_pending、negotiated、won、lost 或 recycled。

### 4.3 Gmail 多账号流程

1. 管理员配置 Google OAuth Client。
2. BD 使用浏览器完成 Gmail OAuth 授权。
3. 后端保存加密 token 引用。
4. 每个 Gmail 账号拥有独立队列、额度、发送窗口和风险状态。
5. Harness 根据账号状态分配草稿。
6. 高风险账号自动暂停队列。

## 5. Agent Harness 架构

本项目采用 `Model + Harness = Agent` 思路。

模型只负责分析和生成，Harness 负责业务执行和安全边界。

### 5.1 模型层

支持：

- OpenAI / Codex。
- DeepSeek。
- Ollama 或本地模型。
- 其它 OpenAI-compatible 模型。

要求：

- 模型可配置。
- 模型配置放在设置页，不放首页一级入口。
- 模型不能直接执行 Gmail 发送。

### 5.2 Harness 调度层

核心组件：

- `TaskRunner`：执行导入、评分、生成、回传、审核等任务。
- `ContextBuilder`：从 KOL、Campaign、历史邮件、回复中组装上下文。
- `ToolRegistry`：统一注册文件解析、SQLite、模型、Gmail、Web Search 等工具。
- `ApprovalGate`：拦截发送、报价、账号授权等高风险动作。
- `EventLog`：记录任务进度和审计事件。
- `ModelRouter`：按任务选择模型。

### 5.3 子 Agent

| Agent | 职责 | 是否可执行外部动作 |
| --- | --- | --- |
| LeadImportAgent | 导入和字段映射 | 否 |
| ScoringAgent | 评分和分层 | 否 |
| OutreachAgent | 生成首触达草稿 | 否 |
| ReplyAgent | 识别回复意向 | 否 |
| FollowupAgent | 生成二次回复草稿 | 否 |
| GmailOpsAgent | Gmail 草稿/发送/同步 | 仅在人审和授权后 |
| AuditAgent | 风险审核 | 否 |

## 6. 功能需求

### 6.1 数据导入

优先级：P0

支持：

- `.xlsx`
- `.csv`
- `.tsv`
- `.json`
- 粘贴文本

字段映射：

- 达人昵称。
- 达人邮箱。
- 达人其他联系方式。
- TikTok 达人详情。
- FastMoss 达人详情页。
- 国家/地区。
- 达人分类。
- 带货倾向。
- 粉丝总量。
- 视频平均播放量。
- 视频互动率。
- 近 28 天销量。

验收标准：

- 上传 1000 行 FastMoss 表格后可正常解析。
- 重复邮箱和重复主页可提示。
- 缺失邮箱的 KOL 不进入 Gmail 触达队列。

### 6.2 KOL 线索池

优先级：P0

功能：

- 展示 KOL 列表。
- 支持按国家、类目、平台、粉丝、销量、邮箱状态、优先级筛选。
- 支持保存筛选条件为目标人群。
- 支持查看 KOL 触达状态和回复状态。

验收标准：

- 可快速筛选出有邮箱的目标 KOL。
- 可查看每个 KOL 的主页、邮箱和评分原因。

### 6.3 KOL 评分

优先级：P0

评分维度：

- 粉丝数。
- 平均播放。
- 近 28 天销量。
- 互动率。
- 是否有邮箱。
- 是否有 TikTok 主页。
- niche 匹配度。

输出：

- High。
- Medium。
- Low。
- 暂缓触达。

### 6.4 AI 首触达草稿

优先级：P0

功能：

- 根据 Campaign brief 和 KOL 数据生成英文 Gmail 草稿。
- 支持批量生成。
- 支持预览和编辑。
- 支持退回重写。

要求：

- 默认不直接发送。
- 高相似度文案需提示。
- 涉及报价或承诺时进入审核。

### 6.5 草稿审核队列

优先级：P0

功能：

- 展示收件人、发送账号、主题、正文、风险标签。
- 支持人工编辑。
- 支持通过并发送。
- 支持退回重写。
- 支持主管审核。

强审核规则：

- 报价。
- 佣金。
- 折扣。
- 样品。
- 合同。
- 发货承诺。
- 敏感行业。

### 6.6 回复回传

优先级：P0

MVP 支持手动回传：

- 达人名称。
- 邮箱。
- 主页。
- 来源 Gmail 账号。
- 回复原文。
- 意向分类。
- 下一步动作。

P1 支持 Gmail API 自动同步回复。

### 6.7 二次回复草稿

优先级：P0

功能：

- 根据原始回复生成跟进草稿。
- 识别报价、样品、产品规格、拒绝和无关回复。
- 保持历史上下文一致。
- 默认进入审核队列。

### 6.8 Gmail 账号管理

优先级：P1

功能：

- OAuth 授权 Gmail 账号。
- 查看账号状态。
- 查看今日额度。
- 暂停账号。
- 查看发送记录。
- token 失效提示。

安全要求：

- 不保存 Gmail 密码。
- 不保存 2FA。
- token 不进入前端。
- 每个账号独立限流和审计。

## 7. 数据模型

### 7.1 Dataset

| 字段 | 说明 |
| --- | --- |
| id | 数据集 ID |
| filename | 文件名 |
| createdAt | 导入时间 |
| source | fastmoss/csv/manual |
| meta | 行数、邮箱覆盖率、国家分布、类目分布 |

### 7.2 KOLLead

| 字段 | 说明 |
| --- | --- |
| id | KOL ID |
| datasetId | 来源数据集 |
| handle | 昵称 |
| email | 邮箱 |
| homepage | TikTok 主页 |
| fastmossUrl | FastMoss 链接 |
| country | 国家 |
| category | 类目 |
| commerceNiche | 带货倾向 |
| followers | 粉丝数 |
| avgViews | 平均播放 |
| sales28d | 近 28 天销量 |
| engagementRate | 互动率 |
| score | 评分 |
| priority | 优先级 |
| status | 当前状态 |

### 7.3 OutreachDraft

| 字段 | 说明 |
| --- | --- |
| id | 草稿 ID |
| kolId | KOL ID |
| type | first_touch/follow_up |
| to | 收件人 |
| fromAccount | Gmail 账号 |
| subject | 主题 |
| body | 正文 |
| status | pending_review/approved/sent/returned |
| riskLabels | 风险标签 |
| createdAt | 创建时间 |
| sentAt | 发送时间 |

### 7.4 Reply

| 字段 | 说明 |
| --- | --- |
| id | 回复 ID |
| kolId | KOL ID |
| accountId | Gmail 账号 |
| replyText | 回复原文 |
| intent | 意向分类 |
| nextAction | 下一步 |
| createdAt | 回传或同步时间 |

### 7.5 GmailAccount

| 字段 | 说明 |
| --- | --- |
| id | 账号 ID |
| email | Gmail 地址 |
| oauthStatus | 授权状态 |
| tokenRef | 凭据引用 |
| dailyQuota | 每日额度 |
| sentToday | 今日已发 |
| riskStatus | 风险状态 |
| paused | 是否暂停 |

### 7.6 AuditLog

| 字段 | 说明 |
| --- | --- |
| id | 日志 ID |
| actor | 操作人 |
| action | 操作 |
| targetType | 对象类型 |
| targetId | 对象 ID |
| before | 变更前 |
| after | 变更后 |
| createdAt | 时间 |

## 8. 状态机

### 8.1 KOL 状态

```text
imported -> scored -> draft_ready -> pending_review -> sent -> replied -> followup_pending -> negotiated -> won/lost/recycled
```

### 8.2 草稿状态

```text
generated -> pending_review -> approved -> sent -> replied
generated -> pending_review -> returned
generated -> pending_review -> paused
```

### 8.3 Gmail 账号状态

```text
not_connected -> oauth_pending -> connected -> active -> throttled -> paused
connected -> expired
```

## 9. 非功能需求

### 9.1 安全

- 不保存 Gmail 密码。
- 不保存 2FA。
- 不把 OAuth token 暴露给前端。
- API Key 不写入前端代码。
- 高风险动作必须人审。
- 所有发送动作写审计日志。

### 9.2 性能

- 1000 行表格导入和字段解析小于 10 秒。
- 1000 行本地评分小于 5 秒。
- 100 个 AI 草稿使用异步队列生成，前端展示进度。
- 单个模型失败不影响其它任务继续。

### 9.3 可用性

- 首页聚焦高频动作。
- 数据导入、模型配置、Gmail 配置收进设置或弹窗。
- 表格支持筛选、排序、搜索。
- 草稿支持预览、编辑、退回和确认。

### 9.4 合规

- 支持停止联系标记。
- 支持 suppression list。
- 支持导出和删除本地数据。
- 保留发送和审核记录。

## 10. 验收标准

### P0 验收

- 可导入 FastMoss xlsx/csv。
- 可提取 KOL 邮箱和主页。
- 可展示 KOL 线索池。
- 可按条件筛选目标 KOL。
- 可生成首触达草稿。
- 草稿不能绕过人审直接发送。
- 可手动回传回复。
- 可生成二次回复草稿。
- 本地可保存数据集、草稿、回复和日志。

### 安全验收

- 前端代码中没有 Gmail 密码、OAuth token、API Key。
- Gmail 发送动作有人工确认。
- 报价和承诺类内容进入审核。
- 所有发送记录可追溯。

## 11. 迭代计划

### V1 本地 MVP

- 本地桌面 Web。
- FastMoss 导入。
- KOL 线索池。
- AI 草稿生成。
- 回复手动回传。
- 人工审核队列。
- 本地文件或 SQLite 保存。

### V1.5 Gmail 安全接入

- Google OAuth。
- Gmail API 创建草稿。
- 人工确认后 Gmail API 发送。
- Gmail 回复同步。
- 多账号限流。

### V2 多人协作

- 用户和角色。
- 主管审核台。
- 团队任务分配。
- 协作审计。
- 数据权限。

### V3 增长运营

- Campaign 管理。
- 模板效果分析。
- KOL 成交归因。
- 复投策略。
- 数据看板。

## 12. 待确认问题

- 技术栈是否采用 React/Vite + FastAPI + SQLite。
- 是否先复用旧 demo，还是建立新项目目录。
- Gmail 真实发送放在 V1.5 还是更晚。
- 是否需要支持产品资料库，用于二次回复和报价说明。
- 是否需要主管审核角色在 MVP 中出现，还是先用单用户人审。
