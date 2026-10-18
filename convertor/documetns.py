from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from .schemas import ContentBlock, SourcePaper


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

