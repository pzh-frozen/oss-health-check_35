"""加权评分：把检查结果折算成 0-100 的总分与等级。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .models import CheckResult, Status

# 等级阈值从高到低排列，命中第一个满足条件的分段。
_LEVELS = (
    (85.0, "优秀", "A"),
    (70.0, "良好", "B"),
    (55.0, "待改进", "C"),
    (0.0, "风险", "D"),
)


@dataclass
class CategoryScore:
    """某一分类（文档 / 社区 / 工程 / 法务）的小计。"""

    name: str
    earned: float
    total: float

    @property
    def ratio(self) -> float:
        return 0.0 if self.total == 0 else self.earned / self.total


@dataclass
class ScoreReport:
    """一次完整扫描的汇总结果。"""

    root: str
    results: List[CheckResult]
    score: float
    level: str
    grade: str
    categories: List[CategoryScore] = field(default_factory=list)

    @property
    def counts(self) -> Dict[str, int]:
        counts = {status.value: 0 for status in Status}
        for result in self.results:
            counts[result.status.value] += 1
        return counts

    @property
    def suggestions(self) -> List[CheckResult]:
        """需要用户采取行动的检查项，按权重从高到低排序。"""
        actionable = [r for r in self.results if r.status in (Status.FAIL, Status.WARN)]
        return sorted(actionable, key=lambda r: (-r.spec.weight, r.spec.check_id))


def level_for(score: float) -> tuple[str, str]:
    """根据总分返回 ``(等级名称, 等级字母)``。"""
    for threshold, name, grade in _LEVELS:
        if score >= threshold:
            return name, grade
    return "风险", "D"


def score_results(root: str, results: List[CheckResult]) -> ScoreReport:
    """计算总分、等级与分类小计。

    被跳过的检查项不计入分母，避免"忽略某项反而扣分"的直觉冲突。
    """
    counted = [r for r in results if r.status is not Status.SKIP]
    total_weight = sum(r.spec.weight for r in counted)
    earned = sum(r.earned for r in counted)

    score = 0.0 if total_weight == 0 else round(earned / total_weight * 100, 1)
    level, grade = level_for(score)

    categories: Dict[str, CategoryScore] = {}
    for result in counted:
        bucket = categories.setdefault(
            result.spec.category, CategoryScore(result.spec.category, 0.0, 0.0)
        )
        bucket.earned += result.earned
        bucket.total += result.spec.weight

    ordered = [categories[name] for name in ("文档", "社区", "工程", "法务") if name in categories]
    ordered.extend(name for name in categories if name not in {"文档", "社区", "工程", "法务"})
    for bucket in ordered:
        bucket.earned = round(bucket.earned, 2)

    return ScoreReport(
        root=root,
        results=results,
        score=score,
        level=level,
        grade=grade,
        categories=ordered,
    )
