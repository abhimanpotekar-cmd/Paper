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



    # structured response to be used by model->

class BlockClassification(BaseModel):
    blockID:str = Field(
        description = "The existing ID assigned by the document reader. Preserve it exactly; do not generate a new ID."
    )
    semanticRole:Literal["title", "author_details", "abstract", "keywords", "introduction", "related_work", "methodology", "results", "discussion",
                        "conclusion", "acknowledgements", "references","other","unknown"] = Field(
        description = "The purpose this block serves in the paper. Use other for understood content outside the supported categories, and unknown when its purpose cannot be determined."
    )

class PaperInterpretation(BaseModel):
    title:None|str = Field(
        default = None,
        description= "The paper’s title as identified from the source content. Use None if it cannot be identified."
    )
    listOfAuthors: List[Author] = Field(
        description="The authors of the paper, preserving their original order."
    )
    blockClassification : List[BlockClassification] = Field(
        description="One classification for every source block, preserving source order and using each existing block ID exactly once."
    )
    interpretationWarnings:List[Tuple[str | None, str]] = Field(
        description="Interpretation problems or ambiguities. Each tuple contains the affected block ID, or None for a general warning, followed by the warning message. Use an empty list when there are no warnings."
    )


class TemplateRule(BaseModel):
    rule_id: str = Field(description="Unique rule ID used to link supporting evidence.")
    basis: Literal["explicit", "inferred", "unspecified"] = Field(
        description="Whether the rule is explicitly stated, inferred, or unspecified."
    )

class MetadataRule(TemplateRule):
    field_name: str = Field(description="Destination field, such as title, authors, affiliations or emails.")
    requirement: Literal["required", "optional", "prohibited", "unspecified"] = Field(
        description="The destination template's requirement status for this field."
    )

class SectionRule(TemplateRule):
    name: str = Field(description="Section name shown or required by the destination template.")
    destination: str | None = Field(
        default=None,
        description="Existing template block ID or placeholder identifying the insertion location. None if unresolved."
    )
    requirement: Literal["required", "optional", "prohibited", "example", "unspecified"] = Field(
        description="Whether the section is required, optional, prohibited, only an example, or unspecified."
    )

class ContentRequirement(TemplateRule):
    target: str = Field(description="Metadata or section rule ID this constraint applies to.")
    constraint: str = Field(description="What is constrained, such as word count, figure count or page count.")
    limit_type: Literal["minimum", "maximum", "exact"] = Field(
        description="Whether the value establishes a minimum, maximum or exact quantity."
    )
    value: float = Field(ge=0, description="The numeric limit supported by the template or guidelines.")
    unit: str = Field(description="Measurement unit, such as words, figures or pages.")

class LocationStyleRule(TemplateRule):
    location: str = Field(description="Existing template block ID, placeholder or style ID identifying the location.")
    font_size: float | None = Field(
        default=None, gt=0, description="Font size in points. None when not established."
    )
    font_family: str | None = Field(
        default=None, description="Font family supported by the extracted template information, or None."
    )
    word_style: str | None = Field(
        default=None, description="Existing Word style identifier to apply, or None when unresolved."
    )

class RuleEvidence(BaseModel):
    rule_id: str = Field(description="The existing rule ID supported by this evidence.")
    location: str = Field(description="Source document and block or style identifier where the evidence occurs.")
    evidence: str = Field(
        description="Exact supporting instruction text or extracted formatting value. Do not invent evidence."
    )

class UnresolvedQuestion(BaseModel):
    location: str | None = Field(
        default=None, description="Affected template location, or None for a general question."
    )
    rule_id: str | None = Field(
        default=None, description="Affected rule ID, or None when no rule has been established."
    )
    question: str = Field(description="The ambiguity or missing information that requires resolution.")

class TemplateInterpretation(BaseModel):
    Metadata: List[MetadataRule] = Field(
        description="Metadata-field rules derived from the destination template and supplied guidelines."
    )
    orderedSection: List[SectionRule] = Field(
        description="Destination sections in template order. Distinguish examples from mandatory sections."
    )
    requirements: List[ContentRequirement] = Field(
        description="Supported numeric constraints. Do not derive limits merely from sample content."
    )
    location_and_style: List[LocationStyleRule] = Field(
        description="Formatting rules linked to identifiable template locations."
    )
    evidence: List[RuleEvidence] = Field(
        default_factory=list, description="Supporting evidence linked to existing rule IDs."
    )
    unresolved_questions: List[UnresolvedQuestion] = Field(
        default_factory=list, description="Unresolved questions. Empty when none were identified."
    )