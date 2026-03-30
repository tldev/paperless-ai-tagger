from paperless_ai_tagger.prompt import build_prompt


def test_build_prompt_with_tags():
    result = build_prompt(
        content="Test document content",
        tags=["invoice", "receipt"],
        correspondents=["Acme Corp"],
        document_types=["Invoice"],
    )
    assert "invoice, receipt" in result
    assert "Acme Corp" in result
    assert "Invoice" in result
    assert "Test document content" in result


def test_build_prompt_empty_taxonomy():
    result = build_prompt(
        content="Test content",
        tags=[],
        correspondents=[],
        document_types=[],
    )
    assert "(none yet)" in result


def test_build_prompt_truncation():
    long_content = "x" * 60000
    result = build_prompt(
        content=long_content,
        tags=[],
        correspondents=[],
        document_types=[],
        max_content_length=100,
    )
    assert "[Content truncated]" in result
    assert len(result) < 60000


def test_build_prompt_custom_prompt():
    result = build_prompt(
        content="Test",
        tags=[],
        correspondents=[],
        document_types=[],
        custom_prompt="Always tag medical documents with 'medical'",
    )
    assert "Always tag medical documents with 'medical'" in result
