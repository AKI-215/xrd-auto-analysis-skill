---
name: pdf-unlock-export
description: >
  处理受保护或难提取的 PDF：先用 pikepdf 解锁，再用 PyMuPDF 导出整页截图、可提取文字和内嵌图片，最终生成便于阅读与后续整理的 Markdown 包。
  触发："解锁 PDF"、"PDF 转 Markdown"、"导出论文截图"、"把 PDF 变成 md"、"unlock pdf"、"pdf to markdown"。
  不适用：需要 OCR 才能识别的纯扫描件最终识别质量优化、复杂表格语义重建、受 DRM 严格限制且无授权的文档。
---

# PDF Unlock Export：解锁 PDF 并导出 Markdown 工作流

你现在扮演的是**PDF 内容整理助手**。目标不是只把 PDF 打开，而是把它变成后续可引用、可读、可抽取的材料包。

---

## 核心用途

适合这些场景：
- PDF 被简单加密，Claude 直接 Read 失败
- 需要导出整页截图，保留图表、公式、版式
- 需要导出可提取文字，便于后续总结
- 需要把 PDF 内嵌图片拆出来单独看
- 需要把论文或报告整理成 Markdown 包再喂给后续工作流

---

## 默认工作流

```text
1. 确认 PDF 路径
2. 用 pikepdf 解锁
3. 用 PyMuPDF 导出 Markdown + pages/ + images/
4. 检查导出结果
5. 再继续做总结、PPT、卡片或知识整理
```

---

## 硬规则

### 1. 先确认授权场景
只处理用户明确提供、并授权当前任务使用的 PDF。

### 2. 优先保留中间产物
默认保留：
- `paper_unlocked.pdf`
- `paper_export/*.md`
- `paper_export/pages/*.png`
- `paper_export/images/*`

不要处理完就删。

### 3. OCR 不是第一步
如果 PDF 只是受保护，但文本层仍存在，先走：
- `unlock_pdf.py`
- `pdf_all_to_md.py`

只有在 Markdown 中大量出现“本页没有可提取文字，可能是扫描页，需要 OCR。”时，才进入 OCR。

### 4. 不要手写长命令替代脚本
优先落地成脚本并复用，不要每次临时拼一大串 one-liner。

---

## 推荐脚本

### unlock_pdf.py

```python
from pathlib import Path
import pikepdf

input_pdf = Path("paper.pdf")
output_pdf = Path("paper_unlocked.pdf")

password = ""

with pikepdf.open(input_pdf, password=password) as pdf:
    pdf.save(output_pdf)

print("已生成:", output_pdf)
```

### pdf_all_to_md.py

```python
from pathlib import Path
import fitz

PDF_PATH = Path("paper_unlocked.pdf")
OUT_DIR = Path("paper_export")
IMG_DIR = OUT_DIR / "images"
PAGE_DIR = OUT_DIR / "pages"

OUT_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)
PAGE_DIR.mkdir(exist_ok=True)

doc = fitz.open(PDF_PATH)
md = []
md.append(f"# {PDF_PATH.stem}\n")

for page_index, page in enumerate(doc, start=1):
    md.append(f"\n\n---\n\n# Page {page_index}\n")

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    page_img = PAGE_DIR / f"page_{page_index:03d}.png"
    pix.save(page_img)
    md.append(f"\n![Page {page_index} screenshot](pages/{page_img.name})\n")

    text = page.get_text("text").strip()
    if text:
        md.append("\n## Extracted Text\n")
        md.append(text)
    else:
        md.append("\n## Extracted Text\n")
        md.append("> 本页没有可提取文字，可能是扫描页，需要 OCR。\n")

    images = page.get_images(full=True)
    if images:
        md.append("\n\n## Extracted Images\n")
        for img_num, img in enumerate(images, start=1):
            xref = img[0]
            base = doc.extract_image(xref)
            image_bytes = base["image"]
            ext = base["ext"]

            image_name = f"page_{page_index:03d}_img_{img_num:02d}.{ext}"
            image_path = IMG_DIR / image_name
            image_path.write_bytes(image_bytes)
            md.append(f"\n![Page {page_index} image {img_num}](images/{image_name})\n")

out_md = OUT_DIR / f"{PDF_PATH.stem}.md"
out_md.write_text("\n".join(md), encoding="utf-8")

print("已导出:")
print(out_md)
print(IMG_DIR)
print(PAGE_DIR)
```

---

## OCR 进入条件

当出现以下任一情况时，再考虑 OCR：
- 大部分页面没有可提取文字
- 页面主要是扫描图像
- 需要全文检索，但 text layer 基本缺失

可选命令：

```bash
ocrmypdf -l eng --deskew --rotate-pages paper_unlocked.pdf paper_ocr.pdf
```

如果是中文或中英混排，语言参数要按实际情况调整，不要默认只用 `eng`。

---

## 输出物解释

- `paper_unlocked.pdf`：可继续读取的解锁版 PDF
- `paper_export/*.md`：整合截图、文字、内嵌图片的 Markdown 主文件
- `paper_export/pages/*.png`：每页整页截图
- `paper_export/images/*`：PDF 内嵌图像

后续如果要做 PPT、摘要、知识卡、事实卡，优先从 Markdown 和整页截图继续。

---

## 依赖

```bash
python -m pip install pikepdf pymupdf
```

如果要 OCR：
- 还需要安装 `ocrmypdf`
- 并确保其依赖（如 Tesseract）可用

---

## 不做什么

- 不在未授权前提下绕过受保护文档
- 不承诺 OCR 一定高质量，特别是复杂扫描论文
- 不把“导出成功”误说成“语义结构已经干净可用”
- 不跳过中间产物直接删文件
