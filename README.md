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

## skills/ 目录中的独立技能

除了仓库顶层这套 XRD 自动分析脚本外，仓库现在还包含两个可直接复用的 Claude skill：

### 1. `skills/xrd-anays/`

这是一个更完整的 **XRD 通用判定 skill**，包含：
- `SKILL.md`：交互式判相说明
- `data/`：候选相种子表与别名表
- `references/`：判定流程、卡片模板、Python/绘图使用说明
- `templates/`：search-match Python 模板与通用 XRD 绘图脚本
- `Structures/`、`Structures_cif/`：本地结构参考资产

适合：
- 先收集样品体系、主要元素、少量元素、不可能元素
- 再做候选相预筛或峰匹配收敛
- 输出 CIF 风格的候选相卡片
- 结合本地结构资产做进一步对照

### 2. `skills/pdf-unlock-export/`

这是一个 **PDF 解锁与 Markdown 导出 skill**，包含：
- `SKILL.md`：工作流说明
- `unlock_pdf.py`：先解锁受保护 PDF
- `pdf_all_to_md.py`：导出 Markdown、整页截图与内嵌图片

适合：
- 论文或报告 PDF 无法直接读取
- 需要先导出为 Markdown 包，再进入总结、汇报、知识整理流程

## 说明

这个仓库目前同时保留了：
- 顶层的 XRD 自动分析脚本与结构库
- `skills/` 目录中的可复用 Claude skills

这样既能直接当脚本仓库使用，也能把对应 skill 拷贝进 `~/.claude/skills/` 使用。若后续还要继续整理，可以再补：

- 更明确的依赖声明
- 每个 skill 单独的 README
- 更轻量的 share 版目录
- 发布用的目录裁剪脚本
