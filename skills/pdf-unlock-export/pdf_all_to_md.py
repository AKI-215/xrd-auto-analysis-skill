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
