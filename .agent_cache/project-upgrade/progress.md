# KOL 管理工作台进度记录

## 2026-08-21

### 已完成

- 用户确认新项目目标：开发「KOL 管理工作台」。
- 用户确认项目形态：本地桌面 Web。
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
- 新增 `backend/` 后端模块：
  - `storage.py`：SQLite schema、本地会话、任务事件、同步队列、审计日志。
  - `importers.py`：xlsx/csv 导入和字段映射。
  - `harness.py`：轻量 Harness，支持导入、评分、草稿生成、回复回传、Supabase 同步边界。
  - `server.py`：本地 HTTP API。
- 新增 `frontend/index.html`，实现桌面 Web 工作台 UI。
- 新增 `start_kol_workbench.bat`，并更新旧启动脚本指向新后端。
- 新增 `.gitignore` 和 `README.md`。
- 已完成端到端验证：
  - 本地页面返回 200。
  - CSV 导入成功。
  - KOL 邮箱提取成功。
  - Gmail 草稿生成成功。
  - 回复回传成功。
  - 二次跟进草稿生成成功。

### 当前状态

已完成本地 MVP 技术骨架。

当前版本不会真实发送 Gmail。点击人工确认发送只会记录本地发送动作。

Supabase 同步已预留后端接口和数据边界，但未配置真实 Supabase 环境变量时保持本地-only。

### 下一步

- 创建 git 首次提交。
- 配置 GitHub 远程仓库后推送。
- 后续可继续补充 Supabase SQL migration、RLS policy 和真实 Google OAuth 设计。
