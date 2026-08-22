# KOL 管理工作台 Agent 规则

## 项目定位

本项目是一个本地桌面 Web 形态的「KOL 管理工作台」。第一阶段面向单机使用，后续预留多人协作版本演进空间。

核心目标是帮助 BD/运营人员完成 KOL 数据导入、线索管理、触达草稿、Gmail 多账号方案讨论、回复回传、AI 跟进建议、人工审核和本地数据沉淀。

## 工作规则

1. 后续开发前必须先读取本文件。
2. 后续开发前必须读取 `.agent_cache/project-upgrade/task_plan.md`。
3. 后续开发前必须读取 `.agent_cache/project-upgrade/findings.md`。
4. 后续开发前必须读取 `.agent_cache/project-upgrade/progress.md`。
5. 后续开发前必须读取 `.agent_cache/project-upgrade/handoff.md`。
6. 因本项目属于 Web/运营工具，后续开发前还必须读取 `.agent_cache/project-upgrade/web_blueprint.md`。
7. 因本项目采用 Model + Harness = Agent 的调度思路，后续开发前还必须读取 `.agent_cache/project-upgrade/agent_harness_architecture.md`。
8. 因本项目使用 Supabase 保存重要 KOL 业务数据，后续开发前还必须读取 `.agent_cache/project-upgrade/supabase_data_architecture.md`。

## 当前阶段约束

- 当前只建立项目规划、规则和交接文件，不写业务代码。
- 允许在后续阶段覆盖现有旧 demo 文件，但覆盖前应说明范围。
- Gmail 方案需要先讨论安全设计，不得直接实现真实自动发送。
- 不保存 Gmail 密码、2FA 验证码、OAuth token 或模型 API Key 到桌面 Shell 代码。
- Agent 会话处理、模型上下文、提示词、草稿生成过程和原始邮件正文必须默认保存在本地，不上传 Supabase。
- 本地桌面 Web 为第一优先级，多人协作只做架构预留。

## 安全边界

高风险操作必须先向用户确认：

- 删除或覆盖现有业务文件。
- 真实调用 Gmail、Google OAuth 或其它外部账号服务。
- 保存密钥、token、cookie、邮箱密码或浏览器登录态。
- 联网安装依赖。
- 启动长期后台服务。
- 部署到公网或对外发布。

## 设计原则

- 首页服务高频业务动作，低频配置收进设置或工具弹窗。
- 本地数据优先保存在项目目录或用户明确指定目录。
- AI 生成的对外内容默认进入人工审核，不自动发送。
- 多账号 Gmail 方案以安全授权、队列、限流和审计为核心。
- UI 应偏后台/运营工具风格，信息密度适中，避免营销页和空泛展示。

## 文件维护要求

每个开发阶段结束时，后续 Agent 必须更新：

- `.agent_cache/project-upgrade/progress.md`
- `.agent_cache/project-upgrade/findings.md`
- `.agent_cache/project-upgrade/handoff.md`
- `.agent_cache/project-upgrade/agent_harness_architecture.md`
- `.agent_cache/project-upgrade/supabase_data_architecture.md`

当范围、架构、页面结构或关键用户流程变化时，必须同步更新：

- `.agent_cache/project-upgrade/task_plan.md`
- `.agent_cache/project-upgrade/web_blueprint.md`
- `.agent_cache/project-upgrade/agent_harness_architecture.md`
- `.agent_cache/project-upgrade/supabase_data_architecture.md`
