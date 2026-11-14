"""CLI、配置加载的端到端测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from oshc.cli import main
from oshc.config import apply_weights, load_config

MINIMAL = """# Demo

这是一个用于测试的项目，内容足够长以便通过 README 的最低长度要求。
""" + ("补充说明。" * 100)


def _build_repo(root: Path) -> None:
    (root / "README.md").write_text(MINIMAL + "\n## 安装\n\npip install demo\n\n## 使用\n\nprint(1)\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT License\n\nPermission is hereby granted, free of charge", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (root / ".gitignore").write_text("__pycache__/\n*.egg-info/\n.venv/\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "intro.md").write_text("# 介绍\n", encoding="utf-8")
    (root / "docs" / "faq.md").write_text("# 常见问题\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (tests / "test_b.py").write_text("def test_b():\n    assert True\n", encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("on: push\n", encoding="utf-8")


def test_scan_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _build_repo(tmp_path)
    assert main(["scan", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "总分" in out


def test_scan_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _build_repo(tmp_path)
    assert main(["scan", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) >= {"score", "level", "checks", "counts"}
    assert 0 <= payload["score"] <= 100


def test_scan_fail_under(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "README.md").write_text("# 空项目\n", encoding="utf-8")
    assert main(["scan", str(tmp_path), "--fail-under", "90"]) == 1
    assert "未达标" in capsys.readouterr().err


def test_scan_missing_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["scan", str(tmp_path / "missing")]) == 2
    assert "目录不存在" in capsys.readouterr().err


def test_scan_writes_markdown(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _build_repo(tmp_path)
    target = tmp_path / "report" / "health.md"
    assert main(["scan", str(tmp_path), "--markdown", str(target)]) == 0
    assert target.is_file()
    assert "# 开源项目健康度报告" in target.read_text(encoding="utf-8")


def test_checks_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["checks"]) == 0
    out = capsys.readouterr().out
    assert "readme" in out and "license" in out


def test_config_weights_applied(tmp_path: Path) -> None:
    config_file = tmp_path / ".oshc.toml"
    config_file.write_text("[weights]\nreadme = 40\n[ignore]\nchecks = [\"security_policy\"]\n", encoding="utf-8")
    config = load_config(config_file)
    specs = {spec.check_id: spec for spec in apply_weights(config)}
    assert specs["readme"].weight == 40
    assert config.ignore == {"security_policy"}


def test_config_rejects_unknown_check(tmp_path: Path) -> None:
    config_file = tmp_path / ".oshc.toml"
    config_file.write_text("[weights]\nnot_a_check = 5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="未知的检查项"):
        load_config(config_file)


def test_config_rejects_bad_threshold(tmp_path: Path) -> None:
    config_file = tmp_path / ".oshc.toml"
    config_file.write_text("[report]\nfail_under = 120\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fail_under"):
        load_config(config_file)


def test_config_used_by_scan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "README.md").write_text(MINIMAL, encoding="utf-8")
    config_file = tmp_path / "custom.toml"
    config_file.write_text("[report]\nfail_under = 99\n", encoding="utf-8")
    assert main(["scan", str(tmp_path), "--config", str(config_file)]) == 1
    assert "低于阈值" in capsys.readouterr().err
