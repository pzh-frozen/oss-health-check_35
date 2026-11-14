# 变更日志

本文件记录项目的所有重要变更，格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划中

- 检查项插件化：通过 Python entry points 动态加载第三方检查。
- GitHub Action 封装，自动在 PR 中评论评分卡。

## [0.3.0] - 2026-04-18

### 新增

- `.oshc.toml` 配置文件：支持自定义检查项权重、忽略指定检查项、设置 CI 阈值。
- `--config` / `--no-config` 参数，可显式指定或跳过配置文件。
- `--markdown FILE` 输出，便于把评分卡贴进 issue、PR 或作业材料。
- 权重校验：未知检查项 id、非正整数权重、越界阈值都会给出明确报错。

### 变更

- 跳过项不再计入评分分母，报告中同时列出跳过明细，避免用忽略刷分。

## [0.2.0] - 2026-03-29

### 新增

- `--json` 输出，字段包含总分、等级、分类小计与逐项结论。
- `--fail-under N` 质量门禁：低于阈值时以退出码 1 结束，可直接接入 CI。
- 分类小计（文档 / 社区 / 工程 / 法务），快速定位短板。
- GitHub Actions 流水线：多版本矩阵跑测试，并对本仓库自检评分。

### 修复

- 修正 Windows 下路径分隔符导致 PR 模板路径显示异常的问题。

## [0.1.0] - 2026-03-08

### 新增

- 首个可用版本：13 个检查项与加权评分模型。
- 终端评分卡：状态标记、得分、明细与按权重排序的改进建议。
- `oshc checks` 子命令，列出全部检查项、权重与判定说明。
- 单元测试与端到端测试共 20 个用例。

[Unreleased]: https://github.com/pzh-frozen/oss-health-check_35/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/pzh-frozen/oss-health-check_35/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/pzh-frozen/oss-health-check_35/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pzh-frozen/oss-health-check_35/releases/tag/v0.1.0
