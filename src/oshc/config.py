"""读取 ``.oshc.toml`` 配置：自定义权重、忽略检查项、CI 阈值。

配置示例::

    [weights]
    tests = 20
    readme = 10

    [ignore]
    checks = ["security_policy"]

    [report]
    fail_under = 80
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

from .checks import SPECS


@dataclass
class Config:
    """项目级配置。"""

    weights: Dict[str, int] = field(default_factory=dict)
    ignore: Set[str] = field(default_factory=set)
    fail_under: int | None = None


def find_config(root: Path) -> Path | None:
    """查找被扫描仓库根目录下的 ``.oshc.toml``。

    只认目标仓库自己的配置，不回退到当前工作目录——否则用一个项目的权重去评分
    另一个项目，结果会难以解释。需要跨目录复用时请显式指定 ``--config``。
    """
    candidate = root / ".oshc.toml"
    return candidate if candidate.is_file() else None


def load_config(path: Path) -> Config:
    """解析 TOML 配置并做基本校验。

    Raises:
        ValueError: 文件不是合法 TOML，或引用了不存在的检查项 id。
    """
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:  # pragma: no cover - 依赖具体语法错误信息
        raise ValueError(f"配置文件不是合法的 TOML：{path}（{exc}）") from exc

    known = {spec.check_id for spec in SPECS}
    config = Config()

    weights = raw.get("weights", {})
    if not isinstance(weights, dict):
        raise ValueError("[weights] 必须是键值表")
    for check_id, weight in weights.items():
        if check_id not in known:
            raise ValueError(f"未知的检查项 id：{check_id}（可用：{', '.join(sorted(known))}）")
        if not isinstance(weight, int) or weight <= 0:
            raise ValueError(f"权重必须是正整数：{check_id} = {weight!r}")
        config.weights[check_id] = weight

    ignore = raw.get("ignore", {})
    if isinstance(ignore, dict):
        for check_id in ignore.get("checks", []):
            if check_id not in known:
                raise ValueError(f"未知的检查项 id：{check_id}")
            config.ignore.add(check_id)

    report = raw.get("report", {})
    if isinstance(report, dict) and "fail_under" in report:
        threshold = report["fail_under"]
        if not isinstance(threshold, int) or not 0 <= threshold <= 100:
            raise ValueError("fail_under 必须是 0-100 的整数")
        config.fail_under = threshold

    return config


def apply_weights(config: Config) -> list:
    """把配置里的权重覆盖应用到默认检查项上。"""
    return [
        spec.with_weight(config.weights.get(spec.check_id, spec.weight)) for spec in SPECS
    ]
