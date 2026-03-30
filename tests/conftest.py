import pytest

from paperless_ai_tagger.config import Settings
from paperless_ai_tagger.models import Classification, Document


@pytest.fixture
def settings():
    return Settings(
        paperless_url="http://localhost:8000",
        paperless_api_token="test-token",
        claude_model="sonnet",
    )


@pytest.fixture
def sample_document():
    return Document(
        id=1,
        title="scan_20240115.pdf",
        content=(
            "INVOICE\nFrom: Acme Corp\nDate: January 15, 2024\n"
            "Amount: $150.00\nFor: Consulting services"
        ),
        tags=[],
        correspondent=None,
        document_type=None,
    )


@pytest.fixture
def sample_classification():
    return Classification(
        title="2024 Acme Corp Consulting Invoice - $150",
        tags=["invoice", "acme-corp"],
        correspondent="Acme Corp",
        document_type="Invoice",
        confidence="high",
        reasoning="Clear invoice with identifiable sender and amount",
    )
