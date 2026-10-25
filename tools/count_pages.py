"""Count collected pages: python tools/count_pages.py"""

import os

from pypdf import PdfReader

CODE = (
    ".py", ".java", ".go", ".c", ".h", ".js", ".ts",
    ".scala", ".rs", ".kt", ".yaml", ".yml"
)

pdf_pages = 0
html = 0
code = 0
broken = 0

for folder, _, files in os.walk("data/raw"):
    for f in files:
        p = os.path.join(folder, f)
        low = f.lower()

        if low.endswith(".pdf"):
            try:
                n = len(PdfReader(p).pages)
                pdf_pages += n
                print(f"{n:5d} pages  {p}")
            except Exception as e:
                broken += 1
                print(f"BROKEN  {p}  {e}")

        elif low.endswith((".html", ".htm")):
            html += 1
            print(f"    1 page   {p}")

        elif low.endswith(CODE):
            code += 1
            print(f"    1 file   {p}")

print()
print(
    f"PDF pages: {pdf_pages} | HTML pages: {html} "
    f"| code files: {code} | broken files: {broken}"
)
print(f"TOTAL pages for DATASET.md: {pdf_pages + html}")