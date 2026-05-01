from pathlib import Path
import pikepdf

input_pdf = Path("paper.pdf")
output_pdf = Path("paper_unlocked.pdf")

password = ""

with pikepdf.open(input_pdf, password=password) as pdf:
    pdf.save(output_pdf)

print("已生成:", output_pdf)
