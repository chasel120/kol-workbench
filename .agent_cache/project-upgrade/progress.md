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
