import logging

import httpx

from paperless_ai_tagger.models import Correspondent, Document, DocumentType, Tag

logger = logging.getLogger(__name__)


class PaperlessClient:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.http = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Token {api_token}"},
            timeout=30.0,
        )
        self._tags: dict[str, Tag] = {}
        self._correspondents: dict[str, Correspondent] = {}
        self._document_types: dict[str, DocumentType] = {}

    def close(self):
        self.http.close()

    def _paginate(self, url: str) -> list[dict]:
        results = []
        while url:
            resp = self.http.get(url)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("results", []))
            url = data.get("next")
        return results

    def load_taxonomy(self):
        logger.info("Loading tags, correspondents, and document types from Paperless")
        for item in self._paginate("/api/tags/"):
            self._tags[item["name"].lower()] = Tag(id=item["id"], name=item["name"])
        for item in self._paginate("/api/correspondents/"):
            self._correspondents[item["name"].lower()] = Correspondent(
                id=item["id"], name=item["name"]
            )
        for item in self._paginate("/api/document_types/"):
            self._document_types[item["name"].lower()] = DocumentType(
                id=item["id"], name=item["name"]
            )
        logger.info(
            "Found %d tags, %d correspondents, %d document types",
            len(self._tags),
            len(self._correspondents),
            len(self._document_types),
        )

    @property
    def tags(self) -> dict[str, Tag]:
        return dict(self._tags)

    @property
    def correspondents(self) -> dict[str, Correspondent]:
        return dict(self._correspondents)

    @property
    def document_types(self) -> dict[str, DocumentType]:
        return dict(self._document_types)

    def ensure_tag(self, name: str) -> Tag:
        key = name.lower()
        if key in self._tags:
            return self._tags[key]
        logger.info("Creating new tag: %s", name)
        resp = self.http.post("/api/tags/", json={"name": name})
        resp.raise_for_status()
        data = resp.json()
        tag = Tag(id=data["id"], name=data["name"])
        self._tags[key] = tag
        return tag

    def ensure_correspondent(self, name: str) -> Correspondent:
        key = name.lower()
        if key in self._correspondents:
            return self._correspondents[key]
        logger.info("Creating new correspondent: %s", name)
        resp = self.http.post("/api/correspondents/", json={"name": name})
        resp.raise_for_status()
        data = resp.json()
        corr = Correspondent(id=data["id"], name=data["name"])
        self._correspondents[key] = corr
        return corr

    def ensure_document_type(self, name: str) -> DocumentType:
        key = name.lower()
        if key in self._document_types:
            return self._document_types[key]
        logger.info("Creating new document type: %s", name)
        resp = self.http.post("/api/document_types/", json={"name": name})
        resp.raise_for_status()
        data = resp.json()
        dt = DocumentType(id=data["id"], name=data["name"])
        self._document_types[key] = dt
        return dt

    def get_processed_tag_id(self, tag_name: str) -> int | None:
        key = tag_name.lower()
        tag = self._tags.get(key)
        return tag.id if tag else None

    def get_unprocessed_documents(self, processed_tag_id: int, limit: int = 0) -> list[Document]:
        url = f"/api/documents/?tags__id__none={processed_tag_id}&ordering=created"
        if limit:
            url += f"&page_size={limit}"
        results = self._paginate(url) if not limit else []
        if limit:
            resp = self.http.get(url)
            resp.raise_for_status()
            results = resp.json().get("results", [])
        return [
            Document(
                id=doc["id"],
                title=doc["title"],
                content=doc.get("content", ""),
                tags=doc.get("tags", []),
                correspondent=doc.get("correspondent"),
                document_type=doc.get("document_type"),
            )
            for doc in results
        ]

    def get_document(self, document_id: int) -> Document:
        resp = self.http.get(f"/api/documents/{document_id}/")
        resp.raise_for_status()
        doc = resp.json()
        return Document(
            id=doc["id"],
            title=doc["title"],
            content=doc.get("content", ""),
            tags=doc.get("tags", []),
            correspondent=doc.get("correspondent"),
            document_type=doc.get("document_type"),
        )

    def update_document(self, document_id: int, payload: dict):
        resp = self.http.patch(f"/api/documents/{document_id}/", json=payload)
        resp.raise_for_status()
        return resp.json()
