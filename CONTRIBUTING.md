# 贡献指南

感谢你有兴趣改进 `oss-health-check`。本文档说明如何搭建环境、提交改动以及我们对
代码与文档的基本要求。即使是修正一个错别字，也欢迎直接提交 PR。

## 行为准则

参与本项目即表示你同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。讨论中请对事不对人，
不同意见很正常，用证据和场景说话即可。

## 第一次贡献

1. 在 [Issues](https://github.com/pzh-frozen/oss-health-check_35/issues) 中搜索是否已有相同问题；
2. 找到标记为 `good first issue` 的任务，直接留言「我来处理」；
3. Fork 仓库，按下面的流程提交 PR；
4. 如果拿不准方案，先在 issue 里描述思路，避免写完被大改。

## 开发环境

```bash
git clone https://github.com/pzh-frozen/oss-health-check_35.git
cd oss-health-check_35
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

要求 Python 3.11 及以上（项目使用 `tomllib` 解析配置）。

## 本地检查

提交前请在本地跑通以下命令，CI 会执行同样的检查：

```bash
python -m pytest -q              # 全部测试
python -m oshc scan . --fail-under 80   # 用工具自检本仓库
```

## 分支模型

| 分支 | 用途 | 生命周期 |
| --- | --- | --- |
| `main` | 始终可发布，CI 必须全绿 | 长期 |
| `feature/<主题>` | 新功能，例如 `feature/plugin-system` | 合并后删除 |
| `fix/<主题>` | 缺陷修复，例如 `fix/windows-path` | 合并后删除 |
| `docs/<主题>` | 纯文档改动 | 合并后删除 |

命名使用小写字母与连字符，避免中文与空格。分支尽量短命，一个分支只做一件事，
减少合并冲突的概率。详细约定见 [docs/git-workflow.md](docs/git-workflow.md)。

## 提交信息规范

采用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)：

```text
<type>(<scope>): <简短描述>

正文说明动机与取舍，必要时补充复现步骤。
```

常用 type：`feat`、`fix`、`docs`、`test`、`refactor`、`chore`、`ci`。
示例：

```text
feat(checks): 新增 SECURITY.md 检查项

安全策略缺失时给 WARN 而不是 FAIL，因为多数个人项目仍在补齐阶段。
```

## 新增一个检查项

1. 在 `src/oshc/checks.py` 中实现 `check_xxx(root: Path) -> tuple[Status, str, str]`；
2. 在 `SPECS` 与 `CHECKS` 中注册 id、标题、分类与权重，并保证全部权重之和仍为 100；
3. 在 `tests/test_checks.py` 中覆盖「缺失 / 警告 / 通过」三种情况；
4. 更新 README 的检查项表格与 `CHANGELOG.md` 的 Unreleased 段；
5. 如果新检查会影响本仓库自检分数，同时调整 CI 中的 `--fail-under` 阈值。

## 代码风格

- 遵循 PEP 8，函数必须带类型标注与简短的 docstring（说明「为什么」而非复述代码）；
- 单个函数不超过 60 行，超过时考虑拆成辅助函数；
- 对外行为的变化必须有测试与 CHANGELOG 条目；
- 不引入第三方运行时依赖——这是项目的核心卖点之一，新增依赖需要在 issue 中说明理由。

## PR 流程

1. 从最新 `main` 切出分支；
2. 提交前跑通本地检查；
3. 在 PR 描述中填写变更说明、关联 issue、验证方式，并勾选自查清单；
4. 至少一位维护者 approve 后，由维护者使用 **Create a merge commit** 合并，保留分支上下文；
5. 合并后删除远端分支。

评审中可能会要求拆分过大 PR。请不要在评审期间 force push 到已有 review 的分支，
追加 commit 更利于对照阅读。
