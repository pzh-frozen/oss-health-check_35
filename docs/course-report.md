# 《开源文化运动》期末考核 · 项目说明与要求对照

本文档用于说明本项目如何逐条满足期末考核要求，并给出可直接核查的证据（文件、提交、分支）。
仓库地址：<https://github.com/pzh-frozen/oss-health-check_35>

## 一、项目基本信息

| 项目 | 内容 |
| --- | --- |
| 课程 | 开源文化运动 |
| 项目名称 | oss-health-check（开源项目健康度检查器） |
| 仓库名 | `oss-health-check_35`（项目名 + 学号后两位 35） |
| 开源许可证 | MIT（GitHub 已自动识别为 `MIT License`） |
| 主要语言 | Python 3.11+，零第三方运行时依赖 |
| 当前版本 | v0.3.0（附注标签 `v0.3.0`） |
| 代码规模 | 8 个源文件、3 个测试文件、35 个测试用例 |

## 二、考核要求对照表

| 要求 | 完成情况 | 证据 |
| --- | --- | --- |
| （1）在 GitHub 上建立自己的项目，项目名称为「项目名称_学号后两位」 | 已建立公开仓库 `pzh-frozen/oss-health-check_35`，默认分支 `main`，20 余个提交 | 仓库首页；`git log --oneline` |
| （2）选择合适的许可证，写好 README 与各种项目文档 | MIT 许可证；README 含特性、安装、用法、输出示例、检查项表、评分规则、项目结构、路线图；另有贡献指南、行为准则、安全策略、变更日志、issue/PR 模板、CI 配置 | [LICENSE](../LICENSE)、[README](../README.md)、[CONTRIBUTING](../CONTRIBUTING.md)、[CODE_OF_CONDUCT](../CODE_OF_CONDUCT.md)、[SECURITY](../SECURITY.md)、[CHANGELOG](../CHANGELOG.md) |
| （3）体现分支管理：创建分支、合并分支、解决冲突 | 先后创建 7 个功能/文档分支，全部通过 `git merge --no-ff` 合入 `main`，并解决了一次真实的 README 合并冲突 | `git log --graph --oneline --all`；[docs/git-workflow.md](git-workflow.md) |
| （4）邀请同学进行 issue 讨论、star、watch | issue / PR 模板与讨论区入口已就绪；邀请同学参与的具体步骤见本文第四节 | `.github/ISSUE_TEMPLATE/`、`.github/PULL_REQUEST_TEMPLATE.md` |
| （5）根据华为「五看三定」对项目进行分析 | 完成约 4400 个汉字的战略分析（含表格与代码块约 8400 字符），覆盖五看（行业/趋势、市场/客户、竞争、自己、机会）与三定（战略控制点、目标、策略），并给出路线图、风险表与季度 OKR | [docs/strategy-analysis.md](strategy-analysis.md) |
| 字数 | 不限 | — |

## 三、分支管理与冲突解决记录

### 3.1 分支一览

| 分支 | 目的 | 合并提交 |
| --- | --- | --- |
| `chore/community-docs` | 补齐贡献指南、行为准则、安全策略 | `a880476` |
| `ci/actions` | 添加 GitHub Actions 流水线、issue 与 PR 模板 | `07e62e5` |
| `docs/strategy` | 架构说明、常见问题、五看三定战略分析 | `fd81b4f` |
| `docs/readme-roadmap` | 更新 README 路线图（v0.2.0 标记已发布、补充 v0.3.0） | `32dfbff` |
| `docs/readme-release` | 补充 v0.3.0 发布说明（与上一条修改同一段，产生冲突） | `5f3fdd4` |
| `docs/git-workflow` | 记录分支模型与冲突解决过程 | `28d7a12` |
| `docs/course-report` | 本文档：考核要求对照与统计校准 | `47966a5` |

所有合并均使用 `--no-ff`，保留分支上下文，便于用 `git log --graph` 复盘。

### 3.2 一次真实冲突

两条文档分支同时修改了 README 的「路线图」段落：一条要把 v0.2.0 标记为已发布，
另一条要补充 v0.3.0 的发布说明，且都改到相邻的同一块内容，Git 无法自动合并：

```text
Auto-merging README.md
CONFLICT (content): Merge conflict in README.md
Automatic merge failed; fix conflicts and then commit the result.
```

解决方式不是"二选一"，而是逐行判断、融合双方信息：保留「已发布」的状态标记，
同时保留 v0.3.0 的配置化描述；提交 `5f3fdd4` 记录解决结果。完整过程（含冲突片段、
命令、经验总结）见 [docs/git-workflow.md](git-workflow.md)。

### 3.3 复现命令

```bash
git clone git@github.com:pzh-frozen/oss-health-check_35.git
cd oss-health-check_35
git log --graph --oneline --all --decorate
git show 5f3fdd4 --stat
```

## 四、邀请同学参与 issue 讨论

仓库已配置：

- `.github/ISSUE_TEMPLATE/bug_report.yml`：缺陷报告（版本、系统、复现步骤、期望/实际结果）
- `.github/ISSUE_TEMPLATE/feature_request.yml`：功能建议（问题、方案、替代方案、范围）
- `.github/ISSUE_TEMPLATE/config.yml`：关闭空白 issue，引导安全漏洞走私下渠道、使用问题走 Discussions
- `.github/PULL_REQUEST_TEMPLATE.md`：变更说明、关联 issue、自测方式、自查清单

建议按以下步骤邀请同学：

1. **加协作者**：仓库 → Settings → Collaborators → Add people，邀请同学 GitHub 账号，
   权限选 `Read`（只读即可参与 issue 讨论）。
2. **让同学 star / watch**：在仓库首页点 Star；点 Watch → All Activity 或 Custom → Issues。
3. **发起讨论**：在 Issues 中新建条目，例如：
   - 「评分权重是否合理：README 占 15 分是否过高？」
   - 「是否应该增加 CODEOWNERS / 贡献者公约检查项？」
   - 「在 Windows 下报告输出对齐有问题，求复现」
4. **使用 PR 模板**：让同学从 issue 出发提一个文档修正 PR，走一遍评审流程。

`.github/ISSUE_TEMPLATE/config.yml` 已经配置了 Discussions 入口，便于把「用法咨询」
与「缺陷报告」分开，这也是开源社区常见的治理实践。

## 五、五看三定分析摘要

完整分析见 [docs/strategy-analysis.md](strategy-analysis.md)，核心结论：

- **五看**：开源已从开发方式变为软件供应链基础设施，合规（CRA、SBOM）与度量（CHAOSS、
  OpenSSF Scorecard）成熟；通用市场被大厂占据，但「中文 + 教学 + 可解释」的细分市场空白；
  自身优势是零依赖、可解释、可配置，短板是单人维护与检查深度。
- **三定**：战略控制点选「中文教学场景的开源健康度标准 + 可解释评分卡」，而非"检查项数量"；
  北极星指标为「每月被扫描的独立仓库数」；策略上以教学闭环为先、生态集成（GitHub Action）
  为辅，明确不做 Web UI、不做企业级合规报告、不做功能数量竞赛。

## 六、质量自证

```text
$ python -m pytest -q
...................................                                      [100%]

$ python -m oshc scan . --fail-under 80
总分 100.0 / 100    等级 优秀（A）    通过 13 · 警告 0 · 缺失 0 · 跳过 0
```

CI（GitHub Actions）在 3.11 / 3.12 / 3.13 三个版本上运行同一套测试，并用本工具自检仓库，
把评分卡本身也纳入质量门禁。
