import pytest

from paperless_ai_tagger.config import Settings


def test_default_settings(monkeypatch):
    monkeypatch.setenv("PAPERLESS_URL", "http://localhost:8000")
    monkeypatch.setenv("PAPERLESS_API_TOKEN", "test-token")
    s = Settings()
    assert s.paperless_url == "http://localhost:8000"
    assert s.claude_model == "sonnet"
    assert s.mode == "merge"
    assert s.processed_tag == "processed-by-ai"
    assert s.dry_run is False
    assert s.batch_size == 10


def test_overwrite_mode(monkeypatch):
    monkeypatch.setenv("PAPERLESS_URL", "http://localhost:8000")
    monkeypatch.setenv("PAPERLESS_API_TOKEN", "test-token")
    monkeypatch.setenv("MODE", "overwrite")
    s = Settings()
    assert s.mode == "overwrite"


def test_required_fields():
    with pytest.raises(Exception):
        Settings(paperless_url=None, paperless_api_token=None)
