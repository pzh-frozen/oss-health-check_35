# oss-health-check · 开源项目健康度检查器

一条命令，给一个仓库做「开源体检」：README、LICENSE、社区文档、工程实践逐项打分，
输出可解释的评分卡与改进清单。零第三方运行时依赖。

## 特性

- 13 项检查，覆盖文档、社区、工程、法务四个维度；
- 加权评分（0-100），等级从「风险 D」到「优秀 A」；
- 终端评分卡按分类展示每项的状态、得分与说明；
- 只使用 Python 标准库，安装后即可离线运行。

## 快速开始

需要 Python 3.11 及以上版本。

```bash
git clone https://github.com/pzh-frozen/oss-health-check_35.git
cd oss-health-check_35
python -m pip install -e .

oshc scan .        # 扫描当前目录
oshc checks        # 查看全部检查项与权重
```

## 许可证

本项目基于 [MIT License](LICENSE) 发布。
