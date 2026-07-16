# GitHub 协作执行规则

你在 ESG-project 中担任实现代理。每次开发前必须先阅读根目录 `AGENTS.md`，并以用户指定的 GitHub Issue 作为唯一需求来源；不得从旧聊天记录猜测或扩展需求。

## 自动化任务处理流程

### 一、优先处理需要修改的 Pull Request

1. 检查由 `trae/` 或 `remote-agent` 分支创建的未关闭 PR。
2. 如果 PR 中存在 Codex 新提出且尚未处理的审查意见，并且审查意见晚于当前分支最新提交：
   - 阅读 PR、关联 Issue、根目录 AGENTS.md 和 `.trae/rules/` 下的项目规则。
   - 只修复 Codex 明确指出的问题。
   - 执行 Issue 和 AGENTS.md 规定的验证。
   - 将修改提交并推送到原分支。
   - 更新 PR 完成报告。
3. 不要创建重复 PR，不要重复处理已经解决的审查意见。

### 二、没有待修改 PR 时，领取新的 Issue

1. 查找标题以 `[AI任务]` 开头、执行代理为 TRAE、尚无关联 PR 的开放 Issue。
2. 每次只领取编号最小的一个 Issue。
3. 从最新 `main` 创建：`trae/<issue-number>-<short-name>`
4. 严格按照 Issue 范围实现，不得自行扩展需求。
5. 至少执行：
   - `npm ci`
   - `npm run check`
   - `npm run build`
6. 涉及 Python 时执行：
   - `python -m compileall -q server`
7. 验证通过后提交并推送分支。
8. 创建以 `main` 为目标的 PR，完整填写仓库 PR 模板，并使用：`Closes #<issue-number>`

### 三、安全限制

- 禁止直接修改或推送 `main`。
- 禁止自动合并 PR。
- 禁止强制推送。
- 禁止执行破坏性数据库或文件操作。
- 禁止提交密码、Token、API Key、`.env`、真实用户数据、上传文件、缓存、构建产物和依赖目录。
- 发现敏感信息、需求冲突、无法验证或需要高风险操作时停止，在 Issue 或 PR 中说明。
- 如果没有新 Issue 或待处理审查意见，只返回 NO_ACTION，不修改任何文件。

## 开始任务

1. 获取远程最新状态。
2. 从最新 `main` 创建 `trae/<issue-number>-<short-name>` 分支。
3. 确认 Issue 的目标、范围、非范围、验收标准和验证命令。
4. 信息不足或互相冲突时停止实现，在 Issue 中说明需要确认的内容。

## 实现约束

- 只修改 Issue 明确要求的范围。
- 不直接提交或推送 `main`。
- 不顺带进行无关重构、依赖大版本升级或数据库破坏性操作。
- 不删除测试、不降低类型检查、不吞掉错误来绕过失败。
- 不提交密码、Token、API Key、`.env`、真实用户数据、上传文件、缓存、构建产物或依赖目录。
- 发现敏感信息时立即停止，不复制其内容。

## 验证与交付

至少执行 Issue 与 `AGENTS.md` 规定的验证。前端通常包括：

```bash
npm ci
npm run check
npm run build
```

涉及 Python 时执行：

```bash
python -m compileall -q server
```

完成后：

1. 提交并推送当前任务分支。
2. 创建以 `main` 为目标的 Pull Request。
3. 完整填写仓库 PR 模板；PR 正文就是完成报告。
4. 关联 Issue，例如 `Closes #12`。
5. 等待 CI 与 Codex Review。
6. 在同一分支处理审查意见，直至 CI 通过且无阻塞意见。