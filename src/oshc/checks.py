"""检查项注册表与具体实现。

每个检查函数签名统一为 ``f(root: Path) -> tuple[Status, detail, suggestion]``，
这样新增一个检查项只需要：写函数 → 注册 ``CheckSpec`` → 补一条测试。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from .models import CheckResult, CheckSpec, Status

CheckOutcome = Tuple[Status, str, str]
CheckFunc = Callable[[Path], CheckOutcome]

# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #

_VENDOR_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def _find_any(root: Path, names: set[str]) -> Path | None:
    """在仓库根目录下按文件名（不区分大小写）查找第一个匹配项。"""
    try:
        entries = list(root.iterdir())
    except OSError:
        return None
    for entry in sorted(entries, key=lambda p: p.name.lower()):
        if entry.is_file() and entry.name.lower() in names:
            return entry
    return None


def _find_glob(root: Path, pattern: str) -> List[Path]:
    """在仓库内递归查找，自动跳过第三方目录。"""
    matches: List[Path] = []
    for path in root.glob(pattern):
        if any(part in _VENDOR_DIRS for part in path.parts):
            continue
        matches.append(path)
    return matches


def _read_text(path: Path, limit: int = 200_000) -> str:
    """宽松读取文本文件：编码错误不抛异常，超长内容截断。"""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _visible_length(text: str) -> int:
    """统计有效字符数（去掉空白与 Markdown 记号），避免用行数误判。"""
    cleaned = re.sub(r"\s+", "", text)
    return len(cleaned)


def _has_heading(text: str, keywords: tuple[str, ...]) -> bool:
    """判断文档标题层级里是否出现某组关键词（中英文均算）。"""
    lowered = text.lower()
    for line in lowered.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        if any(keyword in stripped for keyword in keywords):
            return True
    return False


# --------------------------------------------------------------------------- #
# 检查实现
# --------------------------------------------------------------------------- #

_README_NAMES = {"readme.md", "readme.rst", "readme.txt", "readme", "readme.markdown"}
_SECTION_KEYWORDS = {
    "安装/快速开始": ("install", "安装", "quick start", "getting started", "快速开始", "开始使用"),
    "使用示例": ("usage", "使用", "用法", "example", "示例"),
    "许可证": ("license", "licence", "许可"),
    "贡献指南": ("contribut", "贡献"),
}


def check_readme(root: Path) -> CheckOutcome:
    readme = _find_any(root, _README_NAMES)
    if readme is None:
        return (
            Status.FAIL,
            "未找到 README 文件",
            "新增 README.md，至少说明项目是什么、怎么安装、怎么用、许可证与如何贡献。",
        )

    text = _read_text(readme)
    length = _visible_length(text)
    hit = [name for name, words in _SECTION_KEYWORDS.items() if _has_heading(text, words)]
    detail = f"{readme.name} · 约 {length} 字符 · 命中章节 {len(hit)}/{len(_SECTION_KEYWORDS)}"

    if length < 300:
        return (
            Status.FAIL,
            detail + "（内容过短）",
            "README 至少补充项目简介、安装、用法、许可证与贡献入口。",
        )
    if length < 800 or len(hit) < 3:
        missing = [name for name in _SECTION_KEYWORDS if name not in hit]
        return (
            Status.WARN,
            detail + (f" · 缺少：{'、'.join(missing)}" if missing else ""),
            "补齐 README 的安装、用法、许可证与贡献章节，并给出可复制的示例。",
        )
    return Status.PASS, detail, ""


def _detect_license(text: str) -> str | None:
    signatures = {
        "MIT": "permission is hereby granted, free of charge",
        "Apache-2.0": "apache license",
        "GPL-3.0": "gnu general public license",
        "LGPL-3.0": "gnu lesser general public license",
        "BSD-3-Clause": "redistribution and use in source and binary forms",
        "MPL-2.0": "mozilla public license",
        "Unlicense": "this is free and unencumbered software released into the public domain",
        "CC0-1.0": "cc0 1.0 universal",
    }
    lowered = text.lower()
    for name, signature in signatures.items():
        if signature in lowered:
            return name
    return None


def check_license(root: Path) -> CheckOutcome:
    license_file = _find_any(
        root, {"license", "license.md", "license.txt", "licence", "copying", "copying.md"}
    )
    if license_file is None:
        return (
            Status.FAIL,
            "未找到 LICENSE 文件",
            "选择一款 OSI 认可许可证（个人小工具常用 MIT，专利敏感场景用 Apache-2.0）并放在仓库根目录。",
        )

    spdx = _detect_license(_read_text(license_file))
    if spdx is None:
        return (
            Status.WARN,
            f"{license_file.name} 存在，但未能识别出常见许可证指纹",
            "确认许可证正文完整（不要只写版权行），或改用 SPDX 标准文本。",
        )
    return Status.PASS, f"{license_file.name} · 识别为 {spdx}", ""


def check_contributing(root: Path) -> CheckOutcome:
    found = _find_any(root, {"contributing.md", "contributing.rst", "contributing.txt"})
    if found is None:
        return (
            Status.FAIL,
            "未找到 CONTRIBUTING.md",
            "写清环境准备、分支模型、提交信息规范、PR 检查清单，降低外部贡献者的进入成本。",
        )
    if _visible_length(_read_text(found)) < 200:
        return Status.WARN, f"{found.name} 内容偏少", "补充分支命名、提交规范、代码风格与评审流程。"
    return Status.PASS, f"{found.name} · 约 {_visible_length(_read_text(found))} 字符", ""


def check_code_of_conduct(root: Path) -> CheckOutcome:
    found = _find_any(root, {"code_of_conduct.md", "code-of-conduct.md", "code_of_conduct.txt"})
    if found is None:
        return (
            Status.FAIL,
            "未找到 CODE_OF_CONDUCT.md",
            "采用 Contributor Covenant 2.1 等成熟行为准则，并写明举报渠道。",
        )
    return Status.PASS, found.name, ""


def check_changelog(root: Path) -> CheckOutcome:
    found = _find_any(root, {"changelog.md", "changelog", "changes.md", "history.md"})
    if found is None:
        return (
            Status.FAIL,
            "未找到 CHANGELOG.md",
            "按 Keep a Changelog 的格式记录每个版本的新增、变更与修复，方便使用者评估升级风险。",
        )
    text = _read_text(found)
    if not re.search(r"\bv?\d+\.\d+\.\d+\b", text):
        return Status.WARN, f"{found.name} 未发现版本号", "按版本倒序组织条目，标注日期与版本号。"
    return Status.PASS, found.name, ""


def check_issue_template(root: Path) -> CheckOutcome:
    candidates = _find_glob(root, ".github/ISSUE_TEMPLATE/*") + _find_glob(root, "ISSUE_TEMPLATE*")
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        return (
            Status.FAIL,
            "未找到 issue 模板",
            "在 .github/ISSUE_TEMPLATE/ 下添加缺陷报告与功能请求模板，减少来回追问的沟通成本。",
        )
    return Status.PASS, f"共 {len(candidates)} 个模板", ""


def check_pr_template(root: Path) -> CheckOutcome:
    candidates = [
        root / ".github" / "PULL_REQUEST_TEMPLATE.md",
        root / "PULL_REQUEST_TEMPLATE.md",
        root / "docs" / "PULL_REQUEST_TEMPLATE.md",
        root / ".github" / "pull_request_template.md",
    ]
    for path in candidates:
        if path.is_file():
            return Status.PASS, str(path.relative_to(root)).replace("\\", "/"), ""
    return (
        Status.FAIL,
        "未找到 PR 模板",
        "添加 PULL_REQUEST_TEMPLATE.md，列出变更说明、关联 issue、自测方式与检查清单。",
    )


def check_ci(root: Path) -> CheckOutcome:
    patterns = [
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        ".gitlab-ci.yml",
        ".travis.yml",
        "azure-pipelines.yml",
        ".circleci/config.yml",
        "Jenkinsfile",
    ]
    found: List[Path] = []
    for pattern in patterns:
        found.extend(p for p in _find_glob(root, pattern) if p.is_file())
    if not found:
        return (
            Status.FAIL,
            "未找到持续集成配置",
            "用 GitHub Actions 跑通测试与静态检查，并在 README 挂上构建状态徽章。",
        )
    return Status.PASS, f"{len(found)} 个流水线配置", ""


def check_tests(root: Path) -> CheckOutcome:
    test_dirs = [d for name in ("tests", "test", "spec", "__tests__") if (d := root / name).is_dir()]
    if not test_dirs:
        return (
            Status.FAIL,
            "未找到测试目录",
            "建立 tests/ 目录，至少覆盖核心逻辑的正例与边界情况，并接入 CI。",
        )
    test_files = [
        p
        for p in test_dirs[0].rglob("*")
        if p.is_file() and re.match(r"(test_.*\.py|.*_test\.(py|go|js|ts)|.*\.(spec|test)\.(js|ts))$", p.name)
    ]
    if len(test_files) < 2:
        return Status.WARN, f"仅 {len(test_files)} 个测试文件", "补充核心模块与 CLI 的测试，覆盖异常输入。"
    return Status.PASS, f"{len(test_files)} 个测试文件", ""


def check_docs(root: Path) -> CheckOutcome:
    doc_files: List[Path] = []
    for name in ("docs", "doc"):
        directory = root / name
        if directory.is_dir():
            doc_files.extend(p for p in directory.rglob("*.md") if p.is_file())
    if not doc_files:
        return (
            Status.FAIL,
            "未找到 docs/ 文档目录",
            "把架构说明、部署步骤、常见问题沉淀到 docs/，README 只保留入口。",
        )
    if len(doc_files) < 2:
        return Status.WARN, f"仅有 {len(doc_files)} 篇文档", "至少补齐架构说明与常见问题两类文档。"
    return Status.PASS, f"{len(doc_files)} 篇文档", ""


def check_gitignore(root: Path) -> CheckOutcome:
    path = root / ".gitignore"
    if not path.is_file():
        return (
            Status.FAIL,
            "未找到 .gitignore",
            "忽略虚拟环境、构建产物与本地配置，避免把私密信息或无关文件提交进仓库。",
        )
    lines = [ln.strip() for ln in _read_text(path).splitlines() if ln.strip() and not ln.startswith("#")]
    if len(lines) < 3:
        return Status.WARN, f"{len(lines)} 条忽略规则", "补充报告文件、缓存目录与编辑器配置等规则。"
    return Status.PASS, f"{len(lines)} 条忽略规则", ""


def check_dependency_manifest(root: Path) -> CheckOutcome:
    names = {
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "package.json",
        "cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "gemfile",
        "composer.json",
    }
    found = _find_any(root, names)
    if found is None:
        return (
            Status.FAIL,
            "未找到依赖清单",
            "提供 pyproject.toml / package.json 等清单，明确依赖版本，便于复现与漏洞扫描。",
        )
    return Status.PASS, found.name, ""


def check_security_policy(root: Path) -> CheckOutcome:
    found = _find_any(root, {"security.md", "security.txt"})
    if found is None:
        return (
            Status.WARN,
            "未找到 SECURITY.md",
            "写清漏洞报告渠道与响应时限，避免安全问题被当作普通 issue 公开讨论。",
        )
    return Status.PASS, found.name, ""


# --------------------------------------------------------------------------- #
# 注册表
# --------------------------------------------------------------------------- #

SPECS: List[CheckSpec] = [
    CheckSpec("readme", "项目说明 README", "文档", 15, "是否具备可用的 README 与关键章节"),
    CheckSpec("license", "开源许可证 LICENSE", "法务", 15, "是否声明 OSI 认可许可证"),
    CheckSpec("contributing", "贡献指南", "社区", 10, "是否说明如何参与贡献"),
    CheckSpec("code_of_conduct", "行为准则", "社区", 5, "是否声明社区行为准则"),
    CheckSpec("changelog", "变更日志", "文档", 5, "是否按版本记录变更"),
    CheckSpec("issue_template", "Issue 模板", "社区", 5, "是否提供结构化 issue 模板"),
    CheckSpec("pr_template", "PR 模板", "社区", 5, "是否提供 PR 自查清单"),
    CheckSpec("ci", "持续集成", "工程", 10, "是否配置自动化流水线"),
    CheckSpec("tests", "自动化测试", "工程", 12, "是否有可运行的测试集"),
    CheckSpec("docs", "项目文档", "文档", 8, "是否有 docs/ 深度文档"),
    CheckSpec("gitignore", "忽略规则", "工程", 3, "是否避免提交构建产物"),
    CheckSpec("dependency_manifest", "依赖清单", "工程", 4, "是否可复现依赖环境"),
    CheckSpec("security_policy", "安全策略", "法务", 3, "是否提供漏洞报告渠道"),
]

CHECKS: Dict[str, CheckFunc] = {
    "readme": check_readme,
    "license": check_license,
    "contributing": check_contributing,
    "code_of_conduct": check_code_of_conduct,
    "changelog": check_changelog,
    "issue_template": check_issue_template,
    "pr_template": check_pr_template,
    "ci": check_ci,
    "tests": check_tests,
    "docs": check_docs,
    "gitignore": check_gitignore,
    "dependency_manifest": check_dependency_manifest,
    "security_policy": check_security_policy,
}


def run_checks(
    root: Path,
    specs: List[CheckSpec] | None = None,
    ignored: set[str] | None = None,
) -> List[CheckResult]:
    """对 ``root`` 依次执行检查项。

    Args:
        root: 待检查的仓库根目录。
        specs: 覆盖用的检查项列表（可带自定义权重），为 ``None`` 时使用默认注册表。
        ignored: 需要跳过的检查项 id 集合。

    Returns:
        与 ``specs`` 顺序一致的检查结果列表。
    """
    if not root.is_dir():
        raise NotADirectoryError(f"不是有效的目录：{root}")

    specs = specs if specs is not None else SPECS
    ignored = ignored or set()
    results: List[CheckResult] = []

    for spec in specs:
        if spec.check_id in ignored:
            results.append(CheckResult(spec, Status.SKIP, "已在配置中忽略", ""))
            continue
        func = CHECKS[spec.check_id]
        status, detail, suggestion = func(root)
        results.append(CheckResult(spec, status, detail, suggestion))

    return results
