"""报告渲染：终端文本、JSON、Markdown 三种形态。

渲染层不访问文件系统、不做检查，只消费 ``ScoreReport``，便于单测与替换。
"""

from __future__ import annotations

import json
import unicodedata
from typing import Iterable, List

from .models import CheckResult, Status
from .scoring import ScoreReport

_CATEGORY_ORDER = ("文档", "社区", "工程", "法务")


def _width(text: str) -> int:
    """估算终端显示宽度：东亚宽字符按 2 列计算。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int, align: str = "left") -> str:
    padding = " " * max(0, width - _width(text))
    if align == "right":
        return padding + text
    return text + padding


def _row(cells: Iterable[str], widths: List[int], aligns: List[str]) -> str:
    parts = [_pad(str(cell), width, align) for cell, width, align in zip(cells, widths, aligns)]
    return "  ".join(parts).rstrip()


def _check_rows(results: List[CheckResult]) -> List[str]:
    rows: List[str] = []
    widths = [5, 7]
    aligns = ["left", "right"]
    ids = [r.spec.title for r in results]
    title_width = max([_width("检查项"), *(_width(t) for t in ids)]) if ids else 8
    widths.append(title_width)
    aligns.append("left")

    for result in results:
        rows.append(
            _row(
                [
                    result.status.symbol,
                    f"{result.earned:g}/{result.spec.weight}",
                    result.spec.title,
                ],
                widths,
                aligns,
            )
        )
    return rows


def render_text(report: ScoreReport, version: str = "") -> str:
    """渲染人类可读的终端报告。"""
    counts = report.counts
    lines: List[str] = []
    header = f"oss-health-check {version}".strip()
    lines.append(header)
    lines.append(f"扫描目录：{report.root}")
    lines.append("")
    lines.append(
        f"总分 {report.score:5.1f} / 100    等级 {report.level}（{report.grade}）    "
        f"通过 {counts['pass']} · 警告 {counts['warn']} · 缺失 {counts['fail']} · "
        f"跳过 {counts['skip']}"
    )
    lines.append("")

    for category in _CATEGORY_ORDER:
        bucket = next((c for c in report.categories if c.name == category), None)
        if bucket is None:
            continue
        lines.append(f"[{category}]  {bucket.earned:g}/{bucket.total:g}  ({bucket.ratio * 100:.0f}%)")
        for result in (r for r in report.results if r.spec.category == category):
            status_cell = result.status.symbol
            score_cell = f"{result.earned:g}/{result.spec.weight}"
            lines.append(
                "  "
                + _row([status_cell, score_cell, result.spec.title], [5, 7, 24], ["left", "right", "left"])
                + "  "
                + result.detail
            )
        lines.append("")

    if report.suggestions:
        lines.append(f"改进建议（{len(report.suggestions)} 项，按权重排序）：")
        for index, result in enumerate(report.suggestions, start=1):
            lines.append(f"  {index}. [{result.spec.title}] {result.suggestion}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(report: ScoreReport) -> str:
    """渲染机器可读的 JSON（供 CI 与二次开发消费）。"""
    payload = {
        "root": report.root,
        "score": report.score,
        "level": report.level,
        "grade": report.grade,
        "counts": report.counts,
        "categories": [
            {
                "name": c.name,
                "earned": round(c.earned, 2),
                "total": round(c.total, 2),
                "ratio": round(c.ratio, 3),
            }
            for c in report.categories
        ],
        "checks": [
            {
                "id": r.spec.check_id,
                "title": r.spec.title,
                "category": r.spec.category,
                "weight": r.spec.weight,
                "status": r.status.value,
                "earned": round(r.earned, 2),
                "detail": r.detail,
                "suggestion": r.suggestion,
            }
            for r in report.results
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def render_markdown(report: ScoreReport) -> str:
    """渲染 Markdown 报告，方便写进 issue、PR 或作业材料。"""
    counts = report.counts
    lines = [
        "# 开源项目健康度报告",
        "",
        f"- **扫描目录**：`{report.root}`",
        f"- **总分**：{report.score} / 100",
        f"- **等级**：{report.level}（{report.grade}）",
        f"- **统计**：通过 {counts['pass']} · 警告 {counts['warn']} · "
        f"缺失 {counts['fail']} · 跳过 {counts['skip']}",
        "",
        "## 检查明细",
        "",
        "| 检查项 | 分类 | 权重 | 状态 | 得分 | 说明 |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for result in report.results:
        status = {"pass": "通过", "warn": "警告", "fail": "缺失", "skip": "跳过"}[result.status.value]
        detail = result.detail.replace("|", "\\|")
        lines.append(
            f"| {result.spec.title} | {result.spec.category} | {result.spec.weight} | "
            f"{status} | {result.earned:g} | {detail} |"
        )

    lines.extend(["", "## 分类得分", "", "| 分类 | 得分 | 满分 | 达成率 |", "| --- | ---: | ---: | ---: |"])
    for bucket in report.categories:
        lines.append(
            f"| {bucket.name} | {bucket.earned:g} | {bucket.total:g} | {bucket.ratio * 100:.0f}% |"
        )

    if report.suggestions:
        lines.extend(["", "## 改进建议", ""])
        for index, result in enumerate(report.suggestions, start=1):
            lines.append(f"{index}. **{result.spec.title}**：{result.suggestion}")

    return "\n".join(lines) + "\n"
