from dataclasses import dataclass, field


@dataclass
class Tag:
    id: int
    name: str


@dataclass
class Correspondent:
    id: int
    name: str


@dataclass
class DocumentType:
    id: int
    name: str


@dataclass
class Document:
    id: int
    title: str
    content: str
    tags: list[int] = field(default_factory=list)
    correspondent: int | None = None
    document_type: int | None = None
    original_file_name: str = ""


@dataclass
class Classification:
    title: str
    tags: list[str]
    correspondent: str
    document_type: str
    confidence: str
    reasoning: str
