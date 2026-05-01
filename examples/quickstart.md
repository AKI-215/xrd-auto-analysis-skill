# XRD Skill Quickstart

## 1. 峰质量提取

```bash
python scripts/xrd_peak_quality_checker.py --input 316Ti-2.txt --output output_xrd/316Ti-2_peaks_quality.csv
```

## 2. 候选相比对

```bash
python scripts/xrd_confidence_matcher.py --exp-peaks output_xrd/316Ti-2_peaks_quality.csv --ref-peaks configs/reference_peaks_template.csv --output output_xrd/316Ti-2_confidence_report.json
```

## 3. 单谱图

```bash
python plot_xrd_generic.py single 316Ti-2.txt output_xrd/316Ti-2_single.png --label 316Ti-2
```

## 4. Overlay 图

```bash
python plot_xrd_generic.py overlay 316Ti-2.txt output_xrd/316Ti-2_overlay.png --label 316Ti-2 --ref "Austenite_fcc=43.5,50.7,74.6"
```
