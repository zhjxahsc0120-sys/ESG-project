# GitHub 协作执行规则

你在 ESG-project 中担任实现代理。每次开发前必须先阅读根目录 `AGENTS.md`，并以用户指定的 GitHub Issue 作为唯一需求来源；不得从旧聊天记录猜测或扩展需求。

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
