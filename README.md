# oss-health-check · 开源项目健康度检查器

[![CI](https://github.com/pzh-frozen/oss-health-check_35/actions/workflows/ci.yml/badge.svg)](https://github.com/pzh-frozen/oss-health-check_35/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen.svg)](tests/)

> 一条命令，给一个仓库做「开源体检」：README、LICENSE、社区文档、工程实践逐项打分，
> 输出可解释的评分卡与改进清单。**零第三方运行时依赖**，装完即用。

很多项目在开源时踩的坑并不是代码不行，而是「别人看不懂、不敢用、不敢提 PR」：
没有许可证、README 写不清安装方式、没有 issue 模板、CI 从不跑。`oshc` 把这些
容易被忽视的「开源基础设施」变成 13 个可量化的检查项，让改进有明确的下一步。

## 特性

- **13 项检查、4 个维度**：文档、社区、工程、法务，权重可自定义，总分 0-100。
- **可解释**：每项检查都给出「看到了什么」与「具体怎么改」，而不是只丢一个分数。
- **零依赖**：仅使用 Python 标准库，`pip install` 之后即可离线运行。
- **三种输出**：终端评分卡、JSON（CI 消费）、Markdown（贴进 issue / 作业）。
- **可做质量门禁**：`--fail-under 80` 低于阈值时返回非零退出码，直接卡住 PR。
- **可配置**：`.oshc.toml` 调整权重、忽略不适用检查项、设定 CI 阈值。

## 快速开始

需要 Python 3.11 及以上版本。

```bash
git clone https://github.com/pzh-frozen/oss-health-check_35.git
cd oss-health-check_35
python -m pip install -e .
```

安装后即可使用 `oshc` 命令（也可以 `python -m oshc` 直接运行）：

```bash
oshc scan .                 # 扫描当前目录
oshc scan /path/to/repo     # 扫描指定仓库
oshc checks                 # 查看全部检查项与权重
```

一次典型输出：

```text
oss-health-check 0.3.0
扫描目录：C:\work\my-project

总分  86.4 / 100    等级 优秀（A）    通过 9 · 警告 3 · 缺失 1 · 跳过 0

[文档]  24/28  (86%)
  PASS  15/15  项目说明 README          README.md · 约 2140 字符 · 命中章节 4/4
  PASS   5/5   变更日志                CHANGELOG.md
  WARN   4/8   项目文档                docs/ 仅有 1 篇文档
...

改进建议（4 项，按权重排序）：
  1. [项目文档] 至少补齐架构说明与常见问题两类文档。
```

## 使用

### 输出机器可读结果

```bash
oshc scan . --json > health.json
```

JSON 中包含总分、等级、分类小计与每个检查项的 `status`、`detail`、`suggestion`，
方便二次开发或接入看板。

### 生成 Markdown 报告

```bash
oshc scan . --markdown docs/health-report.md
```

### 作为 CI 质量门禁

```bash
oshc scan . --fail-under 80
```

总分低于阈值时退出码为 `1`，高于或等于时为 `0`，参数错误为 `2`。

### 自定义权重与忽略项

在仓库根目录新建 `.oshc.toml`：

```toml
[weights]
tests = 20
readme = 10

[ignore]
checks = ["security_policy"]

[report]
fail_under = 80
```

命令行参数优先于配置文件：`--fail-under` > 配置文件 > 不设阈值。

## 检查项与权重

| ID | 检查项 | 维度 | 权重 | 判定标准 |
| --- | --- | --- | ---: | --- |
| `readme` | 项目说明 README | 文档 | 15 | 存在且正文 ≥ 800 字符，命中安装、使用、许可证、贡献 4 类章节中的 3 类 |
| `license` | 开源许可证 | 法务 | 15 | 存在 LICENSE，且能识别出 MIT / Apache-2.0 / GPL 等常见许可证 |
| `contributing` | 贡献指南 | 社区 | 10 | 存在 CONTRIBUTING.md 且内容不少于 200 字符 |
| `code_of_conduct` | 行为准则 | 社区 | 5 | 存在 CODE_OF_CONDUCT.md |
| `changelog` | 变更日志 | 文档 | 5 | 存在 CHANGELOG.md，且包含版本号 |
| `issue_template` | Issue 模板 | 社区 | 5 | `.github/ISSUE_TEMPLATE/` 下至少一个模板 |
| `pr_template` | PR 模板 | 社区 | 5 | 存在 PULL_REQUEST_TEMPLATE.md |
| `ci` | 持续集成 | 工程 | 10 | 存在 GitHub Actions / GitLab CI / Travis 等流水线配置 |
| `tests` | 自动化测试 | 工程 | 12 | 存在 tests/ 目录且至少 2 个测试文件 |
| `docs` | 项目文档 | 文档 | 8 | docs/ 下至少 2 篇 Markdown 文档 |
| `gitignore` | 忽略规则 | 工程 | 3 | `.gitignore` 至少 3 条有效规则 |
| `dependency_manifest` | 依赖清单 | 工程 | 4 | 存在 pyproject.toml / package.json 等清单 |
| `security_policy` | 安全策略 | 法务 | 3 | 存在 SECURITY.md |

## 评分规则

- 单项得分 = 权重 × 状态系数：`通过` 1.0、`警告` 0.5、`缺失` 0、`跳过` 不计入分母。
- 总分 = 实得分 / 参与计算的总权重 × 100，保留一位小数。
- 等级：`≥ 85 优秀 A`、`≥ 70 良好 B`、`≥ 55 待改进 C`、其余为 `风险 D`。

> 设计取舍：跳过项不扣分，是因为「这项不适用于本仓库」不应被当作缺陷；
> 但跳过的项会在报告中明确列出，避免用忽略来刷分。

## 项目结构

```text
oss-health-check_35/
├── src/oshc/           # 核心代码：检查项、评分、渲染、CLI
├── tests/              # 35 个单元与端到端测试
├── docs/               # 架构说明、分支工作流、五看三定战略分析
├── .github/            # CI 流水线、issue / PR 模板
├── CHANGELOG.md        # 版本变更记录
├── CONTRIBUTING.md     # 贡献指南
└── pyproject.toml
```

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | 模块划分、数据流、如何新增一个检查项 |
| [docs/strategy-analysis.md](docs/strategy-analysis.md) | 华为「五看三定」战略分析：行业、客户、竞争、自身、机会与落地策略 |
| [docs/faq.md](docs/faq.md) | 常见问题与排查思路 |
| [CHANGELOG.md](CHANGELOG.md) | 版本历史 |

## 路线图

- [x] v0.1.0：13 项检查 + 加权评分 + 终端报告
- [x] v0.2.0：JSON / Markdown 输出、`--fail-under` 质量门禁（已发布）
- [x] v0.3.0：`.oshc.toml` 配置（自定义权重、忽略项、阈值）
- [ ] v0.4.0：检查项插件化（entry points 动态加载）
- [ ] v0.5.0：GitHub Action 封装，自动给 PR 评论评分卡
- [ ] v0.6.0：README 章节质量检测（是否给出可复制的示例命令）

## 参与贡献

欢迎任何形式的贡献：报告问题、补充文档、新增检查项、翻译 README。
开始之前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)；安全问题请按
[SECURITY.md](SECURITY.md) 私下联系维护者，不要公开提交 issue。

首次贡献可以从 [good first issue](https://github.com/pzh-frozen/oss-health-check_35/labels/good%20first%20issue) 开始。

## 许可证

本项目基于 [MIT License](LICENSE) 发布，可自由用于商业项目，请保留版权声明。
