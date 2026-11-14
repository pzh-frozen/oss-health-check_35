# Git 工作流：分支模型、合并策略与冲突解决

本文记录本仓库实际使用的 Git 工作流，包括一次真实的合并冲突及其解决过程。
仓库历史可以直接用 `git log --graph --oneline --all` 复现本文描述的结构。

## 分支模型

采用简化的 Git Flow：`main` 常驻可发布状态，所有改动经由短命分支合入。

```text
main ──●────────●─────────●────────●────────●──
        \      /          \      /         /
         ●──●─             ●──●           ●──●
     feature/…          docs/…         ci/…
```

| 分支类型 | 命名 | 说明 |
| --- | --- | --- |
| 功能 | `feature/<主题>` | 新增能力，例如 `feature/config-file` |
| 修复 | `fix/<主题>` | 缺陷修复，例如 `fix/windows-path` |
| 文档 | `docs/<主题>` | 只改文档，例如 `docs/strategy` |
| 工程 | `chore/<主题>` | 构建、CI、依赖，例如 `chore/community-docs` |

规则：

1. 分支从最新 `main` 切出，生命周期尽量不超过两周；
2. 一个分支只做一件事，便于评审与回滚；
3. 合并后删除远端分支，保持分支列表干净；
4. `main` 上不直接提交（紧急修复也走 `fix/` 分支）。

## 提交信息

采用 Conventional Commits：

```text
feat(checks): 新增 SECURITY.md 检查项
fix(cli): 修正 --fail-under 与配置文件阈值的优先级
docs: 补充五看三定战略分析
ci: 在 3.11 / 3.12 / 3.13 上跑测试矩阵
```

提交正文写「为什么」，代码本身已经说明了「是什么」。

## 合并策略

- **功能分支使用 merge commit**（`git merge --no-ff`），保留分支上下文，
  便于用 `git log --graph` 复盘「这个功能是什么时候、经过哪些提交进来的」；
- **不压缩提交**：评审时按 commit 阅读，合并后仍保留推理过程；
- **合并前必须**：CI 全绿、本地 `oshc scan . --fail-under 80` 通过、至少一位评审者 approve。

```bash
git switch -c feature/config-file
# ... 开发与提交 ...
git switch main
git merge --no-ff feature/config-file -m "merge: 合入 .oshc.toml 配置支持"
git branch -d feature/config-file
```

## 一次真实的冲突：README 路线图被两个分支同时修改

### 场景

`.oshc.toml` 配置功能完成后，两个文档分支几乎同时修改 README 的「路线图」段落：

- `docs/readme-roadmap`：把已完成的 v0.2.0 条目更新为「已发布」，并补充 v0.3.0 条目；
- `docs/readme-release`：在路线图中加入 v0.3.0 的发布说明，并调整后续版本计划。

两条分支都改到了同一段连续的行，Git 无法自动判断应该保留哪一版。

### 复现步骤

```bash
git switch main
git merge --no-ff docs/readme-roadmap -m "merge: 更新路线图"   # 先合入第一条
git merge --no-ff docs/readme-release                          # 第二条产生冲突
```

Git 输出：

```text
Auto-merging README.md
CONFLICT (content): Merge conflict in README.md
Automatic merge failed; fix conflicts and then commit the result.
```

### 冲突长什么样

```text
## 路线图

<<<<<<< HEAD
- [x] v0.2.0：JSON / Markdown 输出、`--fail-under` 质量门禁（已发布）
- [x] v0.3.0：`.oshc.toml` 配置（自定义权重、忽略项、阈值）
=======
- [x] v0.2.0：JSON / Markdown 输出、`--fail-under` 质量门禁（已发布）
- [x] v0.3.0：配置化评分，支持按课程场景调整权重
>>>>>>> docs/readme-release
```

### 解决思路

冲突的根源不是「谁对谁错」，而是两条分支都在描述同一个版本的完成状态，
只是措辞不同。解决时逐行判断，而不是简单选一边：

1. 两条分支都承认 v0.2.0 已发布，保留 `HEAD` 的表述；
2. v0.3.0 的描述融合两者：既保留「配置化」的技术描述，也保留「按课程场景调整权重」
   的价值描述；
3. 检查上下文（上方「文档」表格、下方未完成条目）是否仍然连贯；
4. `git add README.md` 后提交合并：

```bash
git add README.md
git commit -m "merge: 合并路线图与发布说明，统一 v0.3.0 描述"
```

### 解决后的结果

```markdown
- [x] v0.2.0：JSON / Markdown 输出、`--fail-under` 质量门禁（已发布）
- [x] v0.3.0：配置化评分（`.oshc.toml`），支持按课程场景调整权重
```

### 经验

- **冲突不是事故，是沟通信号**：两条分支改同一处，说明这块内容被两边同时需要，
  往往意味着文档结构可以拆细（例如把「路线图」与「发布说明」分开）；
- **先合入的那条分支不要急着重写**：保留它的表述作为基准，再合并另一条，冲突范围最小；
- **合并提交要写清解决方式**：后来的人看 `git log` 时需要知道为什么这样合并；
- **冲突解决后必须重新跑测试**：文档冲突通常不影响代码，但代码冲突一定要重跑
  `pytest` 与 `oshc scan .`。

## 发布流程

1. 更新 `CHANGELOG.md`，把 Unreleased 内容归入新版本并标注日期；
2. 同步 `pyproject.toml` 与 `src/oshc/__init__.py` 中的版本号；
3. 提交 `chore(release): vX.Y.Z`；
4. 打标签并推送：

```bash
git tag -a v0.3.0 -m "v0.3.0：配置化评分"
git push origin main --tags
```

5. 在 GitHub Releases 中粘贴 CHANGELOG 对应段落。

## 常用命令速查

```bash
git log --graph --oneline --all --decorate   # 查看分支拓扑
git switch -c feature/xxx                    # 新建并切换分支
git merge --no-ff feature/xxx                # 保留上下文的合并
git merge --abort                            # 放弃本次合并
git diff --name-only --diff-filter=U         # 列出冲突文件
git checkout --ours path / --theirs path     # 取某一侧版本（谨慎使用）
git branch -d feature/xxx                    # 删除已合并分支
git tag -a v0.3.0 -m "..."                   # 打附注标签
```
