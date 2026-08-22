# KOL 管理工作台交接说明

## 当前交接状态

本项目刚进入重新规划阶段，当前只建立项目规则、计划和蓝图文件，尚未开始新业务代码实现。

## 后续 Agent 必读文件

后续 Agent 开始任何开发前，必须读取：

1. `AGENTS.md`
2. `.agent_cache/project-upgrade/task_plan.md`
3. `.agent_cache/project-upgrade/findings.md`
4. `.agent_cache/project-upgrade/progress.md`
5. `.agent_cache/project-upgrade/handoff.md`
6. `.agent_cache/project-upgrade/web_blueprint.md`
7. `.agent_cache/project-upgrade/agent_harness_architecture.md`
8. `.agent_cache/project-upgrade/supabase_data_architecture.md`

其中 `web_blueprint.md` 是本项目 SOP 扩展文件，不属于 Planning with Files 插件默认文件，但本项目是 Web/运营工具，因此必须读取。

其中 `agent_harness_architecture.md` 是本项目基于 OpenAI Harness 思路新增的 Agent 调度架构文件，后续设计 Agent、任务、工具、人审和 Gmail 动作前必须读取。

其中 `supabase_data_architecture.md` 是本项目的数据库边界文件，明确哪些 KOL 业务数据上传 Supabase，哪些 Agent 会话和敏感数据必须保存在本地。后续设计数据库、API、同步和安全策略前必须读取。

## 用户已确认

- 项目名称：KOL 管理工作台。
- 项目形态：本地 Agent 工作台，桌面 Web 只是本地操作壳。
- 后续方向：未来可能多人协作。
- 文件策略：允许后续覆盖现有文件。
- Gmail 方案：需要先讨论，不直接实现真实发送。
- Agent 调度架构：参考 OpenAI Codex Harness，采用 Model + Harness = Agent 思路。
- 数据库方案：用户提供 Supabase 作为 KOL 业务数据库；所有 Agent 会话处理、模型上下文、草稿正文和原始邮件内容保存在本地，不上传 Supabase。

## 当前目录情况

已有旧文件：

- `kol-bd-workbench-demo.html`
- `kol_agent_server.py`
- `start_kol_agent_workbench.bat`
- `start_kol_workbench.bat`
- `agent_runtime/`
- `desktop_shell/index.html`
- `README.md`
- `.gitignore`
- `KOL-Agent-RPD.md`
- `KOL_Agent_Workbench_PRD_Review.md`
- `KOL_Agent_Workbench_PRD_Enhanced.md`
- `kol_agent_data/`

这些文件目前没有被删除或覆盖。后续若要重构或覆盖，应先说明覆盖范围。

## 当前实现状态

2026-08-22 已完成本地 Agent MVP 骨架：

- Python 标准库本地 Agent Runtime。
- SQLite 本地运行态数据库。
- 本地 Agent 会话和任务事件。
- FastMoss xlsx/csv 导入。
- KOL 评分和线索池。
- Gmail 草稿生成。
- 回复回传和二次跟进草稿。
- Supabase 业务摘要同步预留。

启动方式：

```bat
start_kol_workbench.bat
```

访问：

```text
http://127.0.0.1:8766
```

注意：当前 Gmail 发送为安全占位，只记录发送动作，不真实对外发送。

## 重要安全提醒

Gmail 相关开发必须谨慎：

- 不保存 Gmail 密码。
- 不获取 2FA 验证码。
- 不直接接管浏览器登录态。
- 真实发送前必须完成 OAuth 授权方案设计。
- AI 生成邮件必须先进入人工审核。

## 下一步建议

建议下一轮先做产品和技术方案确认，而不是立刻写代码：

- 优先读取 `KOL_Agent_Workbench_PRD_Enhanced.md`，该文件是用户原 PRD 的完善版。
- 本地 Agent Runtime 是否继续使用 Python 标准库，还是切换到更完整的 Agent SDK / Tauri sidecar。
- MVP 是否只做数据导入、线索池、草稿、回复回传和审核。
- Gmail 是否先做安全占位，后续再接入 Google OAuth。
- 是否从旧 demo 迁移能力，还是创建全新目录结构。
- 是否先实现轻量本地 Harness，再评估 Codex SDK / app-server 接入。
- 确认用户提供的 Supabase 项目、表结构、RLS 策略和本地运行态同步队列。
- 配置 GitHub remote 后执行 push。
# 2026-08-22 最新交接

- 本次修改集中在 `desktop_shell/index.html`、`agent_runtime/harness.py`、`agent_runtime/server.py`。
- Gmail 队列现在分页显示：`state.gmailPageSize = 10`，三个 Tab 共用 `activeGmailItems()`、`updateGmailPager()` 和新版 `renderGmail()`。
- 设置弹窗增加“拉取模型”按钮：前端调用 `POST /api/models/list`，返回模型写入 `#model-options`，并在模型名为空时自动填入第一个模型。
- `/api/models/list` 支持 OpenAI-compatible `/models` 响应，也兼容部分 Ollama 风格响应。API Key 只走内存请求，不落盘。
- 注意：如果本地服务已在 8766 运行，需要重启 `start_kol_workbench.bat` 才能加载新的 Python 接口；HTML 改动可通过刷新页面看到。
# 2026-08-22 本轮交接

- 新增文件：`agent_runtime/secure_store.py`，使用 Windows DPAPI 加密/解密模型 API Key。
- `agent_runtime/storage.py` 新增 `app_settings`、`gmail_accounts`、`local_user_profiles` 表，并给 `outreach_drafts` 增加 `archived_at`。
- `agent_runtime/harness.py` 新增设置、用户占位、Gmail 配置、全量 KOL ID、草稿归档/恢复/删除、模型调用函数。
- `agent_runtime/server.py` 新增 `/api/settings`、`/api/settings/model`、`/api/settings/user`、`/api/gmail-accounts`、`/api/kols/ids`、`/api/drafts/archive|restore|delete`。
- `desktop_shell/index.html` 新增全量全选、账号入口、设置内 Gmail 配置、已存档 Tab、草稿删除/存档按钮。
- 当前真实 Gmail OAuth 仍未实现，只保存多浏览器授权占位配置；真实授权和发送仍需后续明确安全方案。
- 本轮后必须重启本地 Agent 服务，旧 8766 进程不会自动加载新增 Python 接口。
