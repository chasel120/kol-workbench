# KOL 管理工作台

本项目是一个本地桌面 Web 版 KOL 管理工作台，用于导入 KOL 数据、提取邮箱、生成 Gmail 草稿、回传回复、沉淀本地会话，并预留 Supabase 业务数据同步。

## 启动

双击：

```bat
start_kol_workbench.bat
```

或命令行启动：

```bash
python -m backend.server
```

默认访问：

```text
http://127.0.0.1:8766
```

## 当前能力

- FastMoss `.xlsx` / `.csv` 数据导入
- KOL 信息标准化
- 邮箱、主页、国家、类目、粉丝、销量等字段提取
- 本地评分和优先级
- Gmail 首触达草稿生成
- 人工确认发送记录
- 回复手动回传
- 二次跟进草稿生成
- SQLite 本地保存
- Supabase 业务摘要同步预留

## 数据边界

本地保存：

- Agent 会话
- 任务过程
- Prompt / 模型上下文
- 未审核 AI 草稿正文
- 原始邮件正文
- 原始上传文件
- Gmail token / API Key

Supabase 可同步：

- KOL 标准档案
- KOL 联系方式
- Campaign / 目标关系
- 触达摘要
- 回复意向摘要
- 审核任务摘要
- 业务审计日志

## Supabase 配置

当前版本不会默认连接 Supabase。若要测试同步，请在启动前设置：

```powershell
$env:SUPABASE_URL="https://xxxx.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="..."
python -m backend.server
```

注意：`SUPABASE_SERVICE_ROLE_KEY` 只能放在本地后端环境变量或系统凭据库，不能写入前端。

## 安全说明

当前版本不会真实发送 Gmail。点击“人工确认发送”只会记录本地发送动作，`external_sent=false`。真实 Gmail 发送应在后续版本中通过 Google OAuth + Gmail API 实现，并保留人工确认。
