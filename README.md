# XRD Auto Analysis Skill Package

这是一个面向材料分析场景的 XRD skill 包，已经整理为标准 skill 风格目录，重点用于：

- 读取 XRD 原始数据
- 自动提峰
- 输出峰质量表
- 与候选相参考峰做置信度比较
- 生成用于汇报的谱图

## 当前包含的主要模块

- `SKILL.md`：skill 主入口说明
- `xrd-auto-analysis-技能说明.md`：用户侧技能说明
- `xrd-auto-analysis-内部说明.md`：内部维护说明
- `scripts/xrd_peak_quality_checker.py`：峰质量评估脚本
- `scripts/xrd_confidence_matcher.py`：候选相比对脚本
- `plot_xrd_generic.py`：通用作图脚本
- `configs/reference_peaks_template.csv`：参考峰模板
- `Structures/`、`Structures_cif/`：本地结构参考资产

## 推荐使用流程

1. 读取原始 TXT / CSV 数据。
2. 使用 `scripts/xrd_peak_quality_checker.py` 生成带质量标签的峰表。
3. 使用 `scripts/xrd_confidence_matcher.py` 结合参考峰模板做候选相比对。
4. 需要汇报图时，使用 `plot_xrd_generic.py` 输出单谱图、叠图或 overlay 图。

## 示例命令

### 1. 峰质量提取

```bash
python scripts/xrd_peak_quality_checker.py --input 316Ti-2.txt --output output_xrd/316Ti-2_peaks_quality.csv
```

### 2. 候选相比对

```bash
python scripts/xrd_confidence_matcher.py --exp-peaks output_xrd/316Ti-2_peaks_quality.csv --ref-peaks configs/reference_peaks_template.csv --output output_xrd/316Ti-2_confidence_report.json
```

### 3. 单谱图

```bash
python plot_xrd_generic.py single 316Ti-2.txt output_xrd/316Ti-2_single.png --label 316Ti-2
```

### 4. Overlay 图

```bash
python plot_xrd_generic.py overlay 316Ti-2.txt output_xrd/316Ti-2_overlay.png --label 316Ti-2 --ref "Austenite_fcc=43.5,50.7,74.6"
```

## 说明

这个目录目前做的是 skill 风格规范化，不会删除你现有的样品数据、输出图或结构库。若后续要进一步变成可直接放进 `~/.claude/skills/` 的独立包，还可以继续拆分：

- `examples/`
- `references/`
- 更明确的依赖声明
- 更轻量的 share 版目录
