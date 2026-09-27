import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field, HttpUrl

from app.models.provenance import PublicDataset


class RawSnapshot(BaseModel):
    adapter: str
    source_url: HttpUrl
    accessed_at: date
    version: str
    format: str
    payload: str
    checksum_sha256: str
    requests: list[str] = Field(default_factory=list)
    extraction: str

    def verify(self):
        digest = hashlib.sha256(self.payload.encode("utf-8")).hexdigest()
        if digest != self.checksum_sha256:
            raise ValueError("Raw snapshot checksum mismatch")


class SourceAdapter(Protocol):
    name: str
    def fetch(self) -> RawSnapshot: ...
    def normalize(self, raw: RawSnapshot) -> PublicDataset: ...


def raw_snapshot(adapter: str, source_url: str, payload: str, format: str,
                 extraction: str, requests: list[str] | None = None) -> RawSnapshot:
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return RawSnapshot(adapter=adapter, source_url=source_url, payload=payload,
        accessed_at=date.today(), version=digest[:12], format=format,
        checksum_sha256=digest, requests=requests or [source_url], extraction=extraction)


def save_json(path: Path, value: BaseModel | dict):
    """Replace only after complete serialization; failed imports preserve the cache."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = value.model_dump_json(indent=2) if isinstance(value, BaseModel) else json.dumps(value, indent=2, allow_nan=False)
    temporary.write_text(payload + "\n", encoding="utf-8")
    temporary.replace(path)


def read_raw(path: Path) -> RawSnapshot:
    raw = RawSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    raw.verify()
    return raw
