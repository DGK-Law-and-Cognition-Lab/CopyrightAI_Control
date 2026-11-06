"""Turn a Markdown memorandum or preregistration into a Word file set in Times New Roman.

Pandoc converts the Markdown (a single line break is kept as a line break); python-docx then sets every style, table cell and run
to Times New Roman, 12 pt body text, one-inch margins, and page numbers in the footer.

Usage:
    python3 md_to_docx.py INPUT.md [OUTPUT.docx]

Needs pandoc (3.x) on the PATH and python-docx.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

FONT = "Times New Roman"
BODY_PT = 12
HEADING_PT = {1: 14, 2: 13, 3: 12, 4: 12}


def set_font(target, size=None, bold=None):
    """Set the font on a style or run, including the East Asian slot Word falls back to."""
    target.font.name = FONT
    if size is not None:
        target.font.size = Pt(size)
    if bold is not None:
        target.font.bold = bold
    rpr = target.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for slot in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(slot), FONT)


def add_page_number(section):
    """Centered page number in the footer, as a Word PAGE field."""
    paragraph = section.footer.paragraphs[0] if section.footer.paragraphs else section.footer.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            element = OxmlElement("w:fldChar")
            element.set(qn("w:fldCharType"), kind)
        else:
            element = OxmlElement("w:instrText")
            element.set(qn("xml:space"), "preserve")
            element.text = text
        run._r.append(element)
    set_font(run, BODY_PT - 2)


def borders(table):
    """Thin single borders on every table, which pandoc's default table style lacks."""
    tbl_pr = table._tbl.tblPr
    existing = tbl_pr.find(qn("w:tblBorders"))
    if existing is not None:
        tbl_pr.remove(existing)
    edges = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), "808080")
        edges.append(element)
    tbl_pr.append(edges)


def convert(source, target):
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.docx"
        subprocess.run(["pandoc", str(source), "-f", "gfm+hard_line_breaks", "-t", "docx", "-o", str(raw)], check=True)
        doc = Document(str(raw))

    for style in doc.styles:
        if style.type != 1:  # paragraph and character styles only
            if hasattr(style, "font"):
                set_font(style)
            continue
        level = None
        if style.name.startswith("Heading "):
            try:
                level = int(style.name.split()[-1])
            except ValueError:
                level = None
        if level:
            set_font(style, HEADING_PT.get(level, BODY_PT), bold=True)
            style.font.italic = False
            style.font.color.rgb = None
            style.paragraph_format.space_before = Pt(12 if level <= 2 else 8)
            style.paragraph_format.space_after = Pt(4)
            style.paragraph_format.keep_with_next = True
        elif style.name == "Title":
            set_font(style, 16, bold=True)
            style.font.color.rgb = None
        else:
            set_font(style, BODY_PT)
            if style.name in ("Normal", "Body Text", "First Paragraph", "Compact"):
                style.paragraph_format.space_after = Pt(6)
                style.paragraph_format.line_spacing = 1.15

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            set_font(run)
    for table in doc.tables:
        borders(table)
        for i, row in enumerate(table.rows):
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(2)
                    paragraph.paragraph_format.line_spacing = 1.0
                    for run in paragraph.runs:
                        set_font(run, BODY_PT - 1, bold=True if i == 0 else None)

    for section in doc.sections:
        section.left_margin = section.right_margin = Inches(1)
        section.top_margin = section.bottom_margin = Inches(1)
        add_page_number(section)

    doc.save(str(target))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) == 3 else src.with_suffix(".docx")
    convert(src, dst)
    print(dst)
