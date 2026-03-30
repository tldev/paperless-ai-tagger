SYSTEM_PROMPT = """\
You are a document classification system for a personal document management system.

Given the OCR text of a document, classify it by providing:
1. A concise, descriptive title (e.g. "2024 Federal Tax Return" not "tax.pdf")
2. Relevant tags from the existing tag list (prefer existing; suggest new only when necessary)
3. The correspondent (person or organization the document is from/about)
4. The document type

Existing tags: {tag_list}
Existing correspondents: {correspondent_list}
Existing document types: {document_type_list}

Rules:
- Prefer existing tags, correspondents, and document types over creating new ones
- Only suggest new ones when nothing in the existing lists is a reasonable match
- Tags should be lowercase and use hyphens (e.g. "tax-return", "medical-bill")
- Title should be human-readable and specific (include dates, amounts, names when relevant)
- If the document is too unclear to classify confidently, set confidence to "low"
- Respond with ONLY a JSON object. No markdown, no explanation, no code fences.
{custom_prompt}
Document OCR text:
---
{content}
---"""

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "A concise, descriptive title for the document",
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of tag names (use existing tags when possible)",
        },
        "correspondent": {
            "type": "string",
            "description": "The person or organization the document is from",
        },
        "document_type": {
            "type": "string",
            "description": "The type of document (e.g. Invoice, Receipt, Letter, Contract)",
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "How confident you are in this classification",
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of why you chose these classifications",
        },
    },
    "required": ["title", "tags", "correspondent", "document_type", "confidence", "reasoning"],
}


def build_prompt(
    content: str,
    tags: list[str],
    correspondents: list[str],
    document_types: list[str],
    custom_prompt: str = "",
    max_content_length: int = 50000,
) -> str:
    truncated = content[:max_content_length]
    if len(content) > max_content_length:
        truncated += "\n\n[Content truncated]"

    custom_section = f"\n{custom_prompt}\n" if custom_prompt else "\n"

    return SYSTEM_PROMPT.format(
        tag_list=", ".join(sorted(tags)) if tags else "(none yet)",
        correspondent_list=", ".join(sorted(correspondents)) if correspondents else "(none yet)",
        document_type_list=", ".join(sorted(document_types)) if document_types else "(none yet)",
        custom_prompt=custom_section,
        content=truncated,
    )
