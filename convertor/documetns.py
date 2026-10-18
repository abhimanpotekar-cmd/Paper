from .schemas import ContentBlock, SourcePaper
from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn


def read_paper(paper_path: str) -> SourcePaper:
    """Extract ordered content and report limitations instead of guessing."""
    path = Path(paper_path)

    if not path.is_file():
        raise FileNotFoundError(f"Paper file not found: {path}")
    if path.suffix.lower() != ".docx":
        raise ValueError("This reader currently supports .docx files only.")

    try:
        doc = Document(str(path))
    except Exception as exc:
        raise ValueError(f"Could not open the Word document: {path}") from exc

    blocks: list[ContentBlock] = []
    warnings: list[tuple[str | None, str]] = []
    title = ""

    for item in doc.iter_inner_content():
        block_id = f"block_{len(blocks) + 1:03d}"

        if isinstance(item, Paragraph):
            text = item.text
            style_name = (item.style.name or "").casefold() if item.style else ""
            block_type = "paragraph"

            if style_name == "title":
                block_type = "heading"
                if text.strip() and not title:
                    title = text.strip()
                elif text.strip():
                    warnings.append((
                        block_id,
                        "Another Title-style paragraph was found; the first "
                        "non-empty one remains the paper title.",
                    ))
            elif style_name.startswith("heading"):
                block_type = "heading"

            # Images and equations are embedded XML, not ordinary paragraph text.
            if item._p.xpath(".//w:drawing | .//w:pict"):
                warnings.append((
                    block_id,
                    "A drawing or image was detected but not extracted. "
                    "Only the paragraph's available text is preserved.",
                ))

            if item._p.xpath(".//m:oMath"):
                if not text.strip():
                    block_type = "equation"
                warnings.append((
                    block_id,
                    "A Word equation was detected but its mathematical "
                    "content was not extracted.",
                ))

        elif isinstance(item, Table):
            block_type = "table"
            text = "\n".join(
                "\t".join(cell.text for cell in row.cells)
                for row in item.rows
            )
            warnings.append((
                block_id,
                "Table text was flattened using tabs and newlines. "
                "Cell structure, merged cells and formatting are not preserved.",
            ))

            if item._tbl.xpath(".//w:tbl"):
                warnings.append((block_id, "Nested tables were not extracted."))
            if item._tbl.xpath(".//w:drawing | .//w:pict | .//m:oMath"):
                warnings.append((
                    block_id,
                    "An image, drawing or equation inside this table "
                    "was not extracted.",
                ))
        else:
            continue

        # Keep empty paragraphs too: some contain non-text objects.
        blocks.append(ContentBlock(
            uniqueID=block_id,
            blockType=block_type,
            text=text,
            optionalAssetPath=None,
        ))

    if not title:
        warnings.append((
            None,
            "No non-empty Title-style paragraph was identified. The title "
            "is an empty string pending review or later LLM interpretation.",
        ))

    warnings.append((
        None,
        "Authors, emails and affiliations have not been identified. "
        "Their body text remains in the extracted blocks for later interpretation.",
    ))

    if not blocks:
        warnings.append((None, "No top-level paragraphs or tables were extracted."))

    # Construct the complete model last so its ID validator checks every block.
    return SourcePaper(
        title=title,
        listOfAuthors=[],
        listOfContentBlocks=blocks,
        extractionWarnings=warnings,
    )



def font_details(font):
    return {
        "name": font.name,
        "size_pt": font.size.pt if font.size else None,
        "bold": font.bold,
        "italic": font.italic
    }

def read_template(template_path: str) -> dict:
    path = Path(template_path)
    if not path.is_file():
        raise FileNotFoundError(f"Template not found: {path}")
    if path.suffix.lower() != ".docx":
        raise ValueError("The template must be a .docx file.")

    doc = Document(str(path))
    blocks, warnings, styles = [], [], {}
    section_number = 1

    for number, item in enumerate(doc.iter_inner_content(), 1):
        block_id = f"template_{number:03d}"

        if isinstance(item, Paragraph):
            # Keep style definitions and their inheritance relationships.
            paragraph_styles = [item.style] + [run.style for run in item.runs]
            for style in paragraph_styles:
                while style is not None and style.style_id not in styles:
                    styles[style.style_id] = {
                        "name": style.name,
                        "base_style": style.base_style.style_id if style.base_style else None,
                        "font": font_details(style.font)
                    }
                    style = style.base_style

            blocks.append({
                "id": block_id,
                "type": "paragraph",
                "section": section_number,
                "text": item.text,
                "style_id": item.style.style_id if item.style else None,
                "runs": [
                    {
                        "text": run.text,
                        "style_id": run.style.style_id if run.style else None,
                        "font": font_details(run.font)
                    }
                    for run in item.runs
                ]
            })

            if item._p.xpath(".//w:drawing | .//w:pict | .//m:oMath"):
                warnings.append((
                    block_id,
                    "Embedded images, drawings or equations were not extracted."
                ))
            if item._p.xpath("./w:pPr/w:sectPr"):
                section_number += 1

        elif isinstance(item, Table):
            blocks.append({
                "id": block_id,
                "type": "table",
                "section": section_number,
                "rows": [[cell.text for cell in row.cells] for row in item.rows]
            })
            warnings.append((
                block_id,
                "Table cell text only; formatting, merged structure and embedded objects were not extracted."
            ))

    sections = []
    for number, section in enumerate(doc.sections, 1):
        columns = section._sectPr.find(qn("w:cols"))
        layout = {}
        for name in [
            "page_width", "page_height", "top_margin",
            "bottom_margin", "left_margin", "right_margin"
        ]:
            value = getattr(section, name)
            layout[name + "_cm"] = value.cm if value is not None else None
        layout["section"] = number
        layout["column_count"] = (
            int(columns.get(qn("w:num"), "1")) if columns is not None else 1
        )
        sections.append(layout)

    warnings.append((
        None,
        "Headers, footers, text boxes, theme defaults, paragraph spacing, "
        "hyperlink formatting and individual column widths are not inspected."
    ))
    return {
        "blocks": blocks,
        "styles": styles,
        "sections": sections,
        "warnings": warnings
    }

