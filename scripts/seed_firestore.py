"""Explicit opt-in upload of synthetic fixtures to an empty test project."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.repository import LocalRepository

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--confirm-synthetic-upload", action="store_true", required=True)
    args = parser.parse_args()
    from google.cloud import firestore
    client = firestore.Client(project=args.project)
    payload = json.loads(LocalRepository().snapshot().model_dump_json())
    records = []
    for collection in ("regions", "districts", "facilities", "alerts"):
        for document in payload.pop(collection):
            records.append((collection, document["id"], document))
    # Metadata is written last, so a fresh store cannot appear ready mid-upload.
    for start in range(0, len(records), 400):
        batch = client.batch()
        for collection, key, value in records[start:start + 400]:
            batch.set(client.collection(collection).document(key), value)
        batch.commit()
    client.collection("network_metadata").document("india").set(payload)
    print(f"Uploaded {len(records)} synthetic documents to test project {args.project}.")
