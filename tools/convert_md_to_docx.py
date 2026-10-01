from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
import re

MD_PATH = 'docs/CRAG_Interview_Master_Document.md'
DOCX_PATH = 'docs/CRAG_Interview_Master_Document.docx'

def add_code_paragraph(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Courier New')
    run.font.size = Pt(9)


def convert():
    doc = Document()
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code = False
    code_lines = []

    for line in lines:
        stripped = line.rstrip('\n')
        if stripped.startswith('```'):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                # end of code block
                add_code_paragraph(doc, '\n'.join(code_lines))
                in_code = False
            continue

        if in_code:
            code_lines.append(stripped)
            continue

        # headings
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            # docx heading levels go 0..4, but we'll cap at 4
            doc.add_heading(text, level=min(level-1, 4))
            continue

        # bullet list
        if re.match(r'^\s*[-*]\s+.+', stripped):
            text = re.sub(r'^\s*[-*]\s+', '', stripped)
            doc.add_paragraph(text, style='List Bullet')
            continue

        # empty line
        if stripped.strip() == '':
            doc.add_paragraph('')
            continue

        # normal paragraph
        doc.add_paragraph(stripped)

    doc.save(DOCX_PATH)
    print(f"Saved DOCX to {DOCX_PATH}")

if __name__ == '__main__':
    convert()
