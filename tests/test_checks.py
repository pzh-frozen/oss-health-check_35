"""检查项与运行器的单元测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from oshc.checks import (
    SPECS,
    check_changelog,
    check_ci,
    check_contributing,
    check_docs,
    check_gitignore,
    check_issue_template,
    check_license,
    check_readme,
    check_tests,
    run_checks,
)
from oshc.models import Status

GOOD_README = """# Demo

Demo 是一个演示项目，用来验证 README 检查逻辑能否正确识别结构完整的项目说明书。

## 安装

```bash
pip install demo
```

安装完成后可以用 `demo --help` 查看全部命令，支持 Python 3.10 及以上版本。

## 使用

```python
import demo

demo.scan(".")
```

工具会输出一份评分卡，列出每项检查的结论、得分与改进建议。

输出支持三种形态：终端彩色表格用于日常自查，JSON 用于接入 CI 与二次开发，
Markdown 则可以直接贴进 issue、PR 描述或者课程作业。若只想关注某几个维度，
可以通过 `.oshc.toml` 调整权重，或者临时忽略不适用于当前仓库的检查项，
例如纯文档仓库可以跳过测试相关的评分项。

评分卡还会按文档、社区、工程、法务四个维度汇总，方便判断短板集中在哪一类工作上，
而不是只盯着一个总分。

## 许可证

MIT

## 贡献

欢迎提交 PR，详见 CONTRIBUTING.md。提交前请先创建 issue 说明动机，
并确保本地测试全部通过。我们遵循 Conventional Commits 规范，提交信息
需要带上 `feat:`、`fix:`、`docs:` 等前缀，方便自动生成变更日志。

评审流程分三步：先由维护者确认改动范围是否合适，再检查测试与文档是否同步更新，
最后等待 CI 全绿后合并。对于首次贡献者，我们会把 issue 标记为 good first issue，
并在讨论区里给出具体的修改建议，避免新人在不熟悉代码结构的情况下反复试错。

我们同样重视非代码贡献：补充文档示例、翻译 README、整理常见问题、录制使用演示，
这些工作对项目同样关键，也会被记录在 CHANGELOG 的贡献者名单中。如果发现文档里的
命令已经过期，欢迎直接提 PR 修正，不需要事先创建 issue。

## 常见问题

安装失败时先确认 Python 版本是否满足要求，再检查是否安装了旧版本的同名包。
如果只想快速试用，可以直接克隆仓库后运行 `python -m demo .`，无需安装。
"""


def test_readme_missing(tmp_path: Path) -> None:
    status, detail, suggestion = check_readme(tmp_path)
    assert status is Status.FAIL
    assert "README" in detail
    assert suggestion


def test_readme_too_short(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n\n一句话简介。\n", encoding="utf-8")
    status, _, _ = check_readme(tmp_path)
    assert status is Status.FAIL


def test_readme_warn_when_sections_missing(tmp_path: Path) -> None:
    body = "# Demo\n\n" + ("这是一个项目的介绍。" * 60) + "\n\n## 安装\n\npip install demo\n"
    (tmp_path / "README.md").write_text(body, encoding="utf-8")
    status, detail, _ = check_readme(tmp_path)
    assert status is Status.WARN
    assert "缺少" in detail


def test_readme_pass(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(GOOD_README, encoding="utf-8")
    status, detail, _ = check_readme(tmp_path)
    assert status is Status.PASS
    assert "4/4" in detail


def test_license_detects_mit(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text(
        "MIT License\n\nPermission is hereby granted, free of charge, to any person...",
        encoding="utf-8",
    )
    status, detail, _ = check_license(tmp_path)
    assert status is Status.PASS
    assert "MIT" in detail


def test_license_missing(tmp_path: Path) -> None:
    status, _, suggestion = check_license(tmp_path)
    assert status is Status.FAIL
    assert "Apache-2.0" in suggestion


def test_license_unrecognized(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("Copyright 2026, all rights reserved.", encoding="utf-8")
    status, _, suggestion = check_license(tmp_path)
    assert status is Status.WARN
    assert "SPDX" in suggestion


def test_contributing_pass_and_thin(tmp_path: Path) -> None:
    assert check_contributing(tmp_path)[0] is Status.FAIL
    (tmp_path / "CONTRIBUTING.md").write_text("贡献说明。" * 5, encoding="utf-8")
    assert check_contributing(tmp_path)[0] is Status.WARN
    (tmp_path / "CONTRIBUTING.md").write_text("贡献指南。" * 100, encoding="utf-8")
    assert check_contributing(tmp_path)[0] is Status.PASS


def test_changelog_requires_version(tmp_path: Path) -> None:
    assert check_changelog(tmp_path)[0] is Status.FAIL
    (tmp_path / "CHANGELOG.md").write_text("# 变更日志\n\n- 初始化\n", encoding="utf-8")
    assert check_changelog(tmp_path)[0] is Status.WARN
    (tmp_path / "CHANGELOG.md").write_text("## [0.1.0] - 2026-03-01\n\n- 初始化\n", encoding="utf-8")
    assert check_changelog(tmp_path)[0] is Status.PASS


def test_issue_template(tmp_path: Path) -> None:
    assert check_issue_template(tmp_path)[0] is Status.FAIL
    templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    (templates / "bug_report.yml").write_text("name: 缺陷\n", encoding="utf-8")
    status, detail, _ = check_issue_template(tmp_path)
    assert status is Status.PASS
    assert "1 个模板" in detail


def test_ci_detects_workflow(tmp_path: Path) -> None:
    assert check_ci(tmp_path)[0] is Status.FAIL
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("on: push\n", encoding="utf-8")
    assert check_ci(tmp_path)[0] is Status.PASS


def test_tests_dir_detection(tmp_path: Path) -> None:
    assert check_tests(tmp_path)[0] is Status.FAIL
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_one.py").write_text("def test_a(): pass\n", encoding="utf-8")
    assert check_tests(tmp_path)[0] is Status.WARN
    (tests / "test_two.py").write_text("def test_b(): pass\n", encoding="utf-8")
    assert check_tests(tmp_path)[0] is Status.PASS


def test_docs_requires_two_files(tmp_path: Path) -> None:
    assert check_docs(tmp_path)[0] is Status.FAIL
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "intro.md").write_text("# 介绍\n", encoding="utf-8")
    assert check_docs(tmp_path)[0] is Status.WARN
    (docs / "faq.md").write_text("# 常见问题\n", encoding="utf-8")
    assert check_docs(tmp_path)[0] is Status.PASS


def test_gitignore_rules_counted(tmp_path: Path) -> None:
    assert check_gitignore(tmp_path)[0] is Status.FAIL
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    assert check_gitignore(tmp_path)[0] is Status.WARN
    (tmp_path / ".gitignore").write_text("__pycache__/\n*.egg-info/\n.venv/\n", encoding="utf-8")
    assert check_gitignore(tmp_path)[0] is Status.PASS


def test_run_checks_marks_ignored_as_skip(tmp_path: Path) -> None:
    results = run_checks(tmp_path, ignored={"security_policy"})
    skipped = [r for r in results if r.spec.check_id == "security_policy"]
    assert skipped and skipped[0].status is Status.SKIP
    assert len(results) == len(SPECS)


def test_run_checks_rejects_non_directory(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    with pytest.raises(NotADirectoryError):
        run_checks(missing)
