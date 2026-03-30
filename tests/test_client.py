import httpx
import pytest
import respx

from paperless_ai_tagger.client import PaperlessClient


@pytest.fixture
def client():
    c = PaperlessClient("http://localhost:8000", "test-token")
    yield c
    c.close()


@respx.mock
def test_load_taxonomy(client):
    respx.get("http://localhost:8000/api/tags/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": 1, "name": "invoice"}], "next": None}
        )
    )
    respx.get("http://localhost:8000/api/correspondents/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": 1, "name": "Acme Corp"}], "next": None}
        )
    )
    respx.get("http://localhost:8000/api/document_types/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": 1, "name": "Invoice"}], "next": None}
        )
    )

    client.load_taxonomy()
    assert "invoice" in client.tags
    assert "acme corp" in client.correspondents
    assert "invoice" in client.document_types


@respx.mock
def test_ensure_tag_existing(client):
    respx.get("http://localhost:8000/api/tags/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": 1, "name": "invoice"}], "next": None}
        )
    )
    respx.get("http://localhost:8000/api/correspondents/").mock(
        return_value=httpx.Response(200, json={"results": [], "next": None})
    )
    respx.get("http://localhost:8000/api/document_types/").mock(
        return_value=httpx.Response(200, json={"results": [], "next": None})
    )

    client.load_taxonomy()
    tag = client.ensure_tag("invoice")
    assert tag.id == 1
    assert tag.name == "invoice"


@respx.mock
def test_ensure_tag_creates_new(client):
    respx.get("http://localhost:8000/api/tags/").mock(
        return_value=httpx.Response(200, json={"results": [], "next": None})
    )
    respx.get("http://localhost:8000/api/correspondents/").mock(
        return_value=httpx.Response(200, json={"results": [], "next": None})
    )
    respx.get("http://localhost:8000/api/document_types/").mock(
        return_value=httpx.Response(200, json={"results": [], "next": None})
    )
    respx.post("http://localhost:8000/api/tags/").mock(
        return_value=httpx.Response(200, json={"id": 42, "name": "new-tag"})
    )

    client.load_taxonomy()
    tag = client.ensure_tag("new-tag")
    assert tag.id == 42


@respx.mock
def test_get_document(client):
    respx.get("http://localhost:8000/api/documents/1/").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "title": "Test Doc",
                "content": "Hello world",
                "tags": [1, 2],
                "correspondent": 3,
                "document_type": 4,
            },
        )
    )

    doc = client.get_document(1)
    assert doc.id == 1
    assert doc.title == "Test Doc"
    assert doc.tags == [1, 2]
