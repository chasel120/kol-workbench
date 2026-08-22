# KOL 管理工作台

这是一个本地 Agent 工作台，不是传统的“前端 + 后端”业务系统。

产品形态：

- `desktop_shell/`：本地桌面操作界面，只负责展示和人工确认。
- `agent_runtime/`：本地 Agent 运行时，负责导入、清洗、分析、生成草稿、回复判断、同步队列和安全边界。
- Supabase：用户提供的 KOL 业务数据库，保存需要沉淀和未来协作共享的业务事实。
- 本地运行态数据库：只保存 Agent 会话、模型上下文、草稿正文、原始回复、任务事件和隐私数据。

## 启动

双击：

```bat
start_kol_workbench.bat
```

或命令行启动：

```bash
python -m agent_runtime.server
```

默认访问：

```text
http://127.0.0.1:8766
```

这里的本机 HTTP 只是一条本地控制通道，用来让桌面界面调用本地 Agent，不代表产品采用传统前后端架构。

运行注意：

- 请通过 `start_kol_workbench.bat` 或 `python -m agent_runtime.server` 启动。
- 启动后不要关闭命令行窗口，关闭窗口会停止本地 Agent。
- 浏览器请访问 `http://127.0.0.1:8766`。
- 不建议直接双击打开 `desktop_shell/index.html` 或旧的 `kol-bd-workbench-demo.html`，否则容易出现 Agent 未连接。

## 当前能力

- FastMoss `.xlsx` / `.csv` 数据导入
- KOL 信息标准化
- 邮箱、主页、国家、类目、粉丝、销量等字段提取
- 本地评分和优先级计算
- Gmail 首触达草稿生成
- 人工确认发送记录
- 回复手动回传
- 二次跟进草稿生成
- 本地 Agent 会话与运行态保存
- Supabase 业务数据同步预留

## 数据边界

Supabase 保存：

- KOL 标准档案
- KOL 联系方式
- Campaign / 目标关系
- 触达状态摘要
- 回复意向摘要
- 审核任务摘要
- 业务审计日志

本地保存，默认不上传：

- Agent 会话
- 任务过程
- Prompt / 模型上下文
- 未审核 AI 草稿正文
- 原始邮件正文
- 原始上传文件
- Gmail token / API Key

## Supabase 配置

当前版本不会默认连接 Supabase。若要测试同步，请在启动前设置：

```powershell
$env:SUPABASE_URL="https://xxxx.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="..."
python -m agent_runtime.server
```

注意：`SUPABASE_SERVICE_ROLE_KEY` 只能放在本地 Agent 运行时环境变量或系统凭据库，不能写入桌面界面代码。

## 安全说明

当前版本不会真实发送 Gmail。点击“人工确认发送”只会记录本地发送动作，`external_sent=false`。真实 Gmail 发送应在后续版本中通过 Google OAuth + Gmail API 实现，并保留人工确认。
