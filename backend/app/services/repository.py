"""Local and Firestore snapshot stores share a read interface.

Firestore is explicit opt-in; a misconfigured cloud store never silently switches
to synthetic data. Local demo data is the credential-free default.
"""
from typing import Protocol

from app.core.config import ROOT, Settings
from app.core.geography import COUNTRY_BY_ID
from app.models.network import Snapshot
from app.simulation.generator import generate_snapshot


class NetworkRepository(Protocol):
    mode: str
    def snapshot(self) -> Snapshot: ...
    def country_snapshot(self, country_id: str) -> Snapshot: ...


class LocalRepository:
    mode = "local"

    def __init__(self):
        path = ROOT / "data/generated/network.json"
        self._snapshot = Snapshot.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else generate_snapshot()
        self._countries = {"IN": self._snapshot}

    def snapshot(self) -> Snapshot:
        return self._snapshot

    def country_snapshot(self, country_id: str) -> Snapshot:
        if country_id not in COUNTRY_BY_ID:
            raise ValueError("Unsupported country")
        if country_id not in self._countries:
            path = ROOT / "data/generated/nodes" / country_id / "network.json"
            data = Snapshot.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else generate_snapshot(country_id=country_id)
            if data.country != country_id:
                raise ValueError("Snapshot is stored under the wrong country node")
            self._countries[country_id] = data
        return self._countries[country_id]


class FirestoreRepository:
    mode = "firestore"

    def __init__(self, project: str):
        if not project:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required for Firestore storage")
        from google.cloud import firestore
        self.client = firestore.Client(project=project)

    def snapshot(self) -> Snapshot:
        return self.country_snapshot("IN")

    def country_snapshot(self, country_id: str) -> Snapshot:
        if country_id not in COUNTRY_BY_ID:
            raise ValueError("Unsupported country")
        parent = self.client.collection("country_nodes").document(country_id)
        metadata = parent.collection("metadata").document("network").get()
        if metadata.exists:
            payload = metadata.to_dict()
            for collection in ("regions", "districts", "facilities", "alerts"):
                payload[collection] = [doc.to_dict() for doc in parent.collection(collection).stream()]
            result = Snapshot.model_validate(payload)
            if result.country != country_id:
                raise ValueError("Firestore country partition mismatch")
            return result
        if country_id != "IN":
            raise RuntimeError("Firestore country node has not been seeded")
        # Preserve the Phase 1 India-only collection layout as a read fallback.
        metadata = self.client.collection("network_metadata").document("india").get()
        if not metadata.exists:
            raise RuntimeError("Firestore India dataset is not seeded")
        payload = metadata.to_dict()
        for collection in ("regions", "districts", "facilities", "alerts"):
            payload[collection] = [doc.to_dict() for doc in self.client.collection(collection).stream()]
        return Snapshot.model_validate(payload)


def create_repository(settings: Settings) -> NetworkRepository:
    if settings.storage == "local":
        return LocalRepository()
    if settings.storage == "firestore":
        return FirestoreRepository(settings.project)
    raise ValueError("HEALTHNEXUS_STORAGE must be local or firestore")
