"""核心数据模型：检查项定义、检查结果与状态枚举。

设计原则：
1. 检查项（``CheckSpec``）是**不可变**的声明式元数据，权重、分类、说明都在这里定义；
2. 检查结果（``CheckResult``）只描述"看到什么 + 建议做什么"，不负责渲染；
3. 状态（``Status``）自带符号、中文标签与折算系数，避免评分逻辑散落在各处。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    """单个检查项的结论。"""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"

    @property
    def symbol(self) -> str:
        """终端里使用的单字符标记。"""
        return {
            Status.PASS: "PASS",
            Status.WARN: "WARN",
            Status.FAIL: "FAIL",
            Status.SKIP: "SKIP",
        }[self]

    @property
    def label(self) -> str:
        """报告中使用的中文标签。"""
        return {
            Status.PASS: "通过",
            Status.WARN: "警告",
            Status.FAIL: "缺失",
            Status.SKIP: "跳过",
        }[self]

    @property
    def factor(self) -> float:
        """计入得分时的折算系数：通过得满分，警告得一半，缺失不得分。"""
        return {
            Status.PASS: 1.0,
            Status.WARN: 0.5,
            Status.FAIL: 0.0,
            Status.SKIP: 0.0,
        }[self]


@dataclass(frozen=True)
class CheckSpec:
    """一个检查项的静态定义。"""

    check_id: str
    title: str
    category: str
    weight: int
    description: str

    def with_weight(self, weight: int) -> "CheckSpec":
        """返回替换权重后的副本（用于用户自定义权重）。"""
        return CheckSpec(
            check_id=self.check_id,
            title=self.title,
            category=self.category,
            weight=weight,
            description=self.description,
        )


@dataclass
class CheckResult:
    """一个检查项在某次扫描中的实际结论。"""

    spec: CheckSpec
    status: Status
    detail: str
    suggestion: str = ""

    @property
    def earned(self) -> float:
        """本项实际得分。"""
        return round(self.spec.weight * self.status.factor, 4)
