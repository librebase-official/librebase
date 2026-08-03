"""Render Librebase GTM markdown docs to PDF (reportlab)."""
from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer

brand = Path(__file__).resolve().parents[1] / "docs" / "brand"
out_dir = brand / "gtm-pdfs"
out_dir.mkdir(parents=True, exist_ok=True)

export = brand / "majico-export"
for name in [
    "librebase-brand-profile.pdf",
    "librebase-master-document.pdf",
    "librebase-brand-guidelines.pdf",
]:
    src = export / name
    if src.exists():
        dest = out_dir / name
        dest.write_bytes(src.read_bytes())
        print(f"copied {name} ({dest.stat().st_size} bytes)")

styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6
    )
)
styles.add(
    ParagraphStyle(
        name="H1c",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=10,
        spaceBefore=4,
    )
)
styles.add(
    ParagraphStyle(
        name="H2c",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceAfter=8,
        spaceBefore=10,
    )
)
styles.add(
    ParagraphStyle(
        name="H3c",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        spaceAfter=6,
        spaceBefore=8,
    )
)
styles.add(
    ParagraphStyle(
        name="GtmBullet",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        leftIndent=14,
        spaceAfter=3,
    )
)
styles.add(
    ParagraphStyle(
        name="GtmCode",
        parent=styles["Code"],
        fontSize=8,
        leading=10,
        spaceAfter=4,
    )
)


def md_to_flowables(text: str):
    flow = []
    in_code = False
    code_buf: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("```"):
            if in_code:
                flow.append(Preformatted("\n".join(code_buf), styles["GtmCode"]))
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_buf.append(line)
            continue
        if not line.strip():
            flow.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            flow.append(Paragraph(html.escape(line[2:].strip()), styles["H1c"]))
        elif line.startswith("## "):
            flow.append(Paragraph(html.escape(line[3:].strip()), styles["H2c"]))
        elif line.startswith("### "):
            flow.append(Paragraph(html.escape(line[4:].strip()), styles["H3c"]))
        elif re.match(r"^[-*] ", line):
            flow.append(
                Paragraph("• " + html.escape(line[2:].strip()), styles["GtmBullet"])
            )
        elif re.match(r"^\|", line):
            flow.append(Preformatted(line, styles["GtmCode"]))
        else:
            t = html.escape(line)
            t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
            t = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", t)
            flow.append(Paragraph(t, styles["Body"]))
    if code_buf:
        flow.append(Preformatted("\n".join(code_buf), styles["GtmCode"]))
    return flow


for src_name, pdf_name in [
    ("ICP-GTM.md", "librebase-icp-gtm.pdf"),
    ("gtm-blueprint.md", "librebase-gtm-blueprint.pdf"),
]:
    src = brand / src_name
    if not src.exists():
        print(f"missing {src}")
        continue
    pdf_path = out_dir / pdf_name
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=src_name,
        author="Librebase / Majico GTM export",
    )
    doc.build(md_to_flowables(src.read_text(encoding="utf-8")))
    print(f"wrote {pdf_path.name} ({pdf_path.stat().st_size} bytes)")

print("done")
