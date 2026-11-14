"""命令行入口：``oshc scan`` / ``oshc checks``。

退出码约定：
- ``0``：扫描完成且达到阈值（或未指定阈值）
- ``1``：总分低于 ``--fail-under`` 阈值，适合在 CI 中作为质量门禁
- ``2``：参数或路径错误
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .checks import SPECS, run_checks
from .config import apply_weights, find_config, load_config
from .report import render_json, render_markdown, render_text
from .scoring import score_results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oshc",
        description="oss-health-check：零依赖的开源项目健康度检查器",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="扫描一个本地仓库并输出评分卡")
    scan.add_argument("path", nargs="?", default=".", help="仓库根目录，默认当前目录")
    scan.add_argument("--json", action="store_true", help="以 JSON 输出，便于程序消费")
    scan.add_argument("--markdown", metavar="FILE", help="把 Markdown 报告写入指定文件")
    scan.add_argument(
        "--fail-under",
        type=int,
        metavar="N",
        help="总分低于 N 时以退出码 1 结束（CI 质量门禁）",
    )
    scan.add_argument("--config", type=Path, metavar="FILE", help="指定 .oshc.toml 配置文件")
    scan.add_argument("--no-config", action="store_true", help="忽略自动发现的配置文件")

    subparsers.add_parser("checks", help="列出全部检查项及其权重")
    return parser


def _print_checks() -> None:
    print(f"{'ID':<20}{'权重':>4}  {'分类':<4}  标题")
    print("-" * 72)
    for spec in SPECS:
        print(f"{spec.check_id:<20}{spec.weight:>4}  {spec.category:<4}  {spec.title}")
        print(f"{'':<26}{spec.description}")


def _load_config(args: argparse.Namespace, root: Path):
    if args.no_config:
        return None
    if args.config is not None:
        path = args.config
        if not path.is_file():
            raise ValueError(f"配置文件不存在：{path}")
        return load_config(path)
    discovered = find_config(root)
    return load_config(discovered) if discovered else None


def main(argv: Optional[List[str]] = None) -> int:
    """命令行主函数，返回退出码。"""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "checks":
        _print_checks()
        return 0

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"错误：目录不存在或不是目录 —— {root}", file=sys.stderr)
        return 2

    try:
        config = _load_config(args, root)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    specs = apply_weights(config) if config else SPECS
    ignored = config.ignore if config else set()
    results = run_checks(root, specs=specs, ignored=ignored)
    report = score_results(str(root), results)

    if args.json:
        print(render_json(report))
    else:
        print(render_text(report, version=__version__), end="")

    if args.markdown:
        target = Path(args.markdown)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_markdown(report), encoding="utf-8")
        print(f"Markdown 报告已写入：{target}")

    threshold = args.fail_under if args.fail_under is not None else (config.fail_under if config else None)
    if threshold is not None and report.score < threshold:
        print(
            f"未达标：总分 {report.score} 低于阈值 {threshold}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
