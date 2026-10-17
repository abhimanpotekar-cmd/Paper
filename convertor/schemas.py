from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import List,Tuple ,Literal

class Author(BaseModel):
    # this is for a single author
    name:str = Field(
        description = "The author's name as mentioned in the paper"
    )
    email : None | str= Field(
        default=None,
        description = "The author's email as mentioned in the paper.If there is no email mentioned it will be None"
    )
    affiliation :None | str = Field(
        default = None,
        description = "The author’s affiliation as explicitly associated with them in the paper. Use None when no affiliation can be established."
    )

class ContentBlock(BaseModel):
    uniqueID:str = Field(
        description = "A non-empty identifier that uniquely identifies this block within the source paper."
        )
    blockType:Literal["heading","paragraph","table","figure","equation","reference"] = Field(
        description = "The content category of this block: heading, paragraph, table, figure, equation or reference."

    )
    text:str = Field(
        description = "Contains the actual text in a block."
    )

    optionalAssetPath:None | str= Field(
        default = None,
        description = "The path to a separate file associated with this block, such as an extracted image. Use None when no separate file is associated with it"
    )

class SourcePaper(BaseModel):
    title:str= Field(
        description = "The title of the paper."
    )
    listOfAuthors:List[Author] = Field(
        description = "The authors of the paper, preserving their original order"
    )
    listOfContentBlocks:List[ContentBlock] = Field(
        description = "The content blocks of the paper, preserving their original document order"
    )
    extractionWarnings:List[Tuple[str | None, str]] = Field(
        description = """Problems encountered during extraction. Each tuple contains the affected block’s
                        ID, or None for document-wide or unidentified-block problems, followed by the warning
                        message. Use an empty list when no problems were detected"""
    )

    @model_validator(mode="after")
    def check_unique_ids(self):
        seen_ids = set()
        for block in self.listOfContentBlocks:
            block_id = block.uniqueID.strip()

            # Reject empty or whitespace-only IDs
            if not block_id:
                raise ValidationError([{
                    "loc": ("listOfContentBlocks",),
                    "msg": "Empty or whitespace-only block ID detected",
                    "type": "value_error"
                }], SourcePaper)

            # Reject IDs with surrounding whitespace (normalize or fail)
            if block.uniqueID != block_id:
                raise ValidationError([{
                    "loc": ("listOfContentBlocks",),
                    "msg": f"Block ID '{block.uniqueID}' contains leading/trailing spaces",
                    "type": "value_error"
                }], SourcePaper)

            # Reject duplicates
            if block_id in seen_ids:
                raise ValidationError([{
                    "loc": ("listOfContentBlocks",),
                    "msg": f"Duplicate block ID '{block_id}' detected",
                    "type": "value_error"
                }], SourcePaper)

            seen_ids.add(block_id)

        return self