"""oss-health-check：零依赖的开源项目健康度检查器。

用法::

    from oshc import run_checks, score_results

    results = run_checks(Path("."))
    report = score_results(".", results)
    print(report.score, report.level)
"""

from .checks import CHECKS, SPECS, run_checks
from .config import Config, apply_weights, load_config
from .models import CheckResult, CheckSpec, Status
from .report import render_json, render_markdown, render_text
from .scoring import ScoreReport, score_results

__version__ = "0.3.0"

__all__ = [
    "__version__",
    "CHECKS",
    "SPECS",
    "run_checks",
    "CheckResult",
    "CheckSpec",
    "Status",
    "Config",
    "apply_weights",
    "load_config",
    "ScoreReport",
    "score_results",
    "render_text",
    "render_json",
    "render_markdown",
]
