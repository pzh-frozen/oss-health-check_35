"""评分与报告渲染的单元测试。"""

from __future__ import annotations

import json

from oshc.models import CheckResult, CheckSpec, Status
from oshc.report import render_json, render_markdown, render_text
from oshc.scoring import level_for, score_results


def _spec(check_id: str = "readme", weight: int = 10, category: str = "文档") -> CheckSpec:
    return CheckSpec(check_id, "标题", category, weight, "说明")


def test_level_thresholds() -> None:
    assert level_for(100) == ("优秀", "A")
    assert level_for(85) == ("优秀", "A")
    assert level_for(84.9) == ("良好", "B")
    assert level_for(70) == ("良好", "B")
    assert level_for(55) == ("待改进", "C")
    assert level_for(0) == ("风险", "D")


def test_full_score() -> None:
    results = [CheckResult(_spec("a", 60), Status.PASS, ""), CheckResult(_spec("b", 40), Status.PASS, "")]
    report = score_results(".", results)
    assert report.score == 100.0
    assert report.level == "优秀"


def test_warn_counts_half() -> None:
    results = [
        CheckResult(_spec("a", 50), Status.PASS, ""),
        CheckResult(_spec("b", 50), Status.WARN, ""),
    ]
    report = score_results(".", results)
    assert report.score == 75.0
    assert report.level == "良好"
    assert report.counts == {"pass": 1, "warn": 1, "fail": 0, "skip": 0}


def test_skip_excluded_from_denominator() -> None:
    results = [
        CheckResult(_spec("a", 50), Status.PASS, ""),
        CheckResult(_spec("b", 50), Status.SKIP, ""),
    ]
    report = score_results(".", results)
    assert report.score == 100.0
    assert report.categories[0].total == 50


def test_all_skipped_scores_zero() -> None:
    results = [CheckResult(_spec(), Status.SKIP, "")]
    report = score_results(".", results)
    assert report.score == 0.0
    assert report.level == "风险"


def test_suggestions_sorted_by_weight() -> None:
    results = [
        CheckResult(_spec("low", 3), Status.FAIL, "d", "补 low"),
        CheckResult(_spec("high", 15), Status.WARN, "d", "补 high"),
        CheckResult(_spec("ok", 10), Status.PASS, "d"),
    ]
    report = score_results(".", results)
    assert [s.spec.check_id for s in report.suggestions] == ["high", "low"]


def test_render_json_roundtrip() -> None:
    results = [CheckResult(_spec("readme", 15), Status.PASS, "README.md")]
    payload = json.loads(render_json(score_results(".", results)))
    assert payload["score"] == 100.0
    assert payload["checks"][0]["id"] == "readme"
    assert payload["categories"][0]["name"] == "文档"


def test_render_text_contains_summary() -> None:
    results = [CheckResult(_spec("readme", 15), Status.FAIL, "缺失", "新增 README")]
    text = render_text(score_results(".", results), version="0.3.0")
    assert "总分" in text
    assert "改进建议" in text
    assert "新增 README" in text


def test_render_markdown_has_tables() -> None:
    results = [CheckResult(_spec("readme", 15), Status.PASS, "README.md")]
    markdown = render_markdown(score_results(".", results))
    assert "| 检查项 | 分类 | 权重 | 状态 | 得分 | 说明 |" in markdown
    assert "## 分类得分" in markdown
