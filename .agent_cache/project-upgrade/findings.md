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
