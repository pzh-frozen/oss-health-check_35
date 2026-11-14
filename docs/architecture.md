# 架构说明

## 设计目标

| 目标 | 具体约束 |
| --- | --- |
| 零运行时依赖 | 只用 Python 标准库；开发依赖仅限 pytest / pytest-cov |
| 可解释 | 每项检查都要回答「看到了什么」与「怎么改」，禁止只返回布尔值 |
| 可扩展 | 新增检查项只改 `checks.py` 与注册表，不改评分与渲染 |
| 可测试 | 检查函数为纯函数（输入目录、输出结论），不依赖网络与全局状态 |

## 模块划分

```text
src/oshc/
├── models.py      # Status / CheckSpec / CheckResult：不可变的数据契约
├── checks.py      # 13 个检查函数 + SPECS 注册表 + run_checks 调度
├── scoring.py     # 加权求和、等级判定、分类小计
├── report.py      # 终端 / JSON / Markdown 三种渲染
├── config.py      # .oshc.toml 解析与权重覆盖
└── cli.py         # 参数解析、退出码、组装上述模块
```

依赖方向是单向的：

```text
cli → config → checks → models
 ↓                ↓
report → scoring ─┘
```

`report` 只依赖 `scoring` 产出的 `ScoreReport` 与 `models` 中的结果对象，
不读文件、不做判定，因此可以用构造出来的假数据直接测渲染逻辑。

## 一次扫描的数据流

1. `cli` 解析参数，`Path.resolve()` 得到扫描根目录，非法路径直接返回退出码 2；
2. `config` 可选地加载 `.oshc.toml`，把权重覆盖应用到 `SPECS` 上，得到本次的检查项列表；
3. `checks.run_checks` 逐项调用检查函数，跳过被忽略的项并标记为 `SKIP`；
4. `scoring.score_results` 过滤掉 `SKIP`，按权重折算总分、等级与四个分类小计；
5. `report` 按输出格式渲染；若指定 `--markdown`，额外写文件；
6. `cli` 比较总分与阈值，决定返回 0 还是 1。

## 关键设计决策

### 为什么状态不是布尔值

真实项目里大量处于「有但不达标」的中间态：README 存在但只有三行、测试目录存在但只有
一个空测试。布尔值会把这些情况判成「通过」，评分就失去区分度。引入 `WARN`（折算 0.5）
后，评分卡能更贴近维护者的实际感受，也给改进留出中间台阶。

### 为什么跳过项不计入分母

如果忽略一项就扣分，用户会倾向于「补一个空文件」来骗过检查，而不是真正忽略。
跳过项不计分但要显式列出，既尊重「不适用」，又保留透明度。

### 为什么权重默认之和为 100

不是为了凑整数，而是让「实得分 / 总权重」直接等于百分制分数，用户心算即可验证，
减少对评分黑箱的怀疑。自定义权重后仍按比例归一化，不要求用户自己凑到 100。

### 为什么检查函数只接收 `Path`

`check_xxx(root: Path)` 的签名让每个检查都可以用 `tmp_path` 构造最小仓库来测试，
无需 mock 文件系统。代价是每个函数要自己处理路径大小写与缺失文件，这部分开销
集中收敛在 `_find_any`、`_find_glob`、`_read_text` 三个工具函数里。

## 如何新增一个检查项

```python
def check_security_policy(root: Path) -> CheckOutcome:
    found = _find_any(root, {"security.md", "security.txt"})
    if found is None:
        return Status.WARN, "未找到 SECURITY.md", "写清漏洞报告渠道与响应时限。"
    return Status.PASS, found.name, ""
```

然后在 `SPECS` 中登记元数据、在 `CHECKS` 中登记函数、补三种状态的测试。
如果新项改变了权重总和，记得同步 README 的检查项表格与 CI 的阈值。

## 测试策略

- `tests/test_checks.py`：每个检查函数覆盖「缺失 / 中间态 / 达标」；
- `tests/test_scoring.py`：阈值边界、权重折算、跳过项、建议排序；
- `tests/test_cli.py`：端到端跑 `main(argv)`，断言退出码与 stdout / stderr；
- 配置解析单独覆盖非法 id、非法权重、越界阈值等错误分支。

CI 在 3.11 / 3.12 / 3.13 三个版本上跑同一套测试，并用工具自检本仓库，
把「评分卡」本身也纳入质量门禁。

## 已知局限

- 只支持本地目录，扫描远程仓库需要先 clone（v0.4 计划支持 `--repo owner/name`）；
- 检查偏「文件是否存在」，对 README 内容质量的判断较粗；
- 渲染层未做彩色输出，终端观感依赖等宽字体；
- 单人维护，响应时间受课业安排影响。
