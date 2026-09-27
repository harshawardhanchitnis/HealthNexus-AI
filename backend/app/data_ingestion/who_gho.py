"""Verified WHO GHO OData adapter: bed and medical-doctor density.

Keeps two most recent non-null, unstratified observations per country/indicator.
Different countries and indicators can have different latest reference years.
"""
import json
from urllib.parse import urlparse

import httpx

from app.core.geography import ISO3_TO_ID
from app.data_ingestion.base import RawSnapshot, raw_snapshot
from app.models.provenance import Observation, Provenance, PublicDataset

BASE = "https://ghoapi.azureedge.net/api/"
INDICATORS = {"WHS6_102": "Hospital beds per 10,000 population", "HWF_0001": "Medical doctors per 10,000 population"}


class WHOGHOAdapter:
    name = "who_gho"
    version = "1.0"

    def fetch(self) -> RawSnapshot:
        rows, requests = [], []
        country_filter = " or ".join(f"SpatialDim eq '{iso}'" for iso in ISO3_TO_ID)
        with httpx.Client(timeout=45, follow_redirects=True) as client:
            for indicator in INDICATORS:
                url = str(httpx.URL(BASE + indicator, params={"$filter": f"({country_filter})", "$orderby": "TimeDim desc"}))
                seen, found = set(), []
                while url:
                    parsed = urlparse(url)
                    if parsed.scheme != "https" or parsed.netloc != "ghoapi.azureedge.net" or not parsed.path.startswith("/api/"):
                        raise ValueError("Untrusted WHO pagination URL")
                    if url in seen or len(seen) >= 20:
                        raise ValueError("WHO pagination loop or limit exceeded")
                    seen.add(url)
                    response = client.get(url)
                    response.raise_for_status()
                    payload = response.json()
                    found.extend(payload["value"])
                    requests.append(url)
                    url = payload.get("@odata.nextLink")
                for country in ISO3_TO_ID:
                    candidates = [r for r in found if r.get("SpatialDim") == country and
                        r.get("NumericValue") is not None and all(r.get(d) is None for d in ("Dim1", "Dim2", "Dim3"))]
                    candidates.sort(key=lambda r: r["TimeDim"], reverse=True)
                    if not candidates:
                        raise ValueError(f"WHO has no unstratified observations for {country}/{indicator}")
                    rows.extend(candidates[:2])
        return raw_snapshot(self.name, BASE, json.dumps({"value": rows}, ensure_ascii=False, sort_keys=True),
            "application/json", "Unchanged WHO records: two latest non-null unstratified years per indicator and configured country; no imputation.", requests)

    def normalize(self, raw: RawSnapshot) -> PublicDataset:
        raw.verify()
        if raw.adapter != self.name or str(raw.source_url) != BASE:
            raise ValueError("Wrong source for WHO adapter")
        provenance = Provenance(id="who-gho-brics", source_type="public_international",
            source_name="WHO Global Health Observatory — bed and doctor density",
            source_url="https://www.who.int/data/gho/info/gho-odata-api", accessed_at=raw.accessed_at,
            geography=["IN", "BR", "RU", "CN", "ZA"], is_synthetic=False,
            license="WHO data terms apply; attribution required; underlying third-party data may have additional terms. See source documentation.",
            methodology=raw.extraction, version=raw.version, checksum_sha256=raw.checksum_sha256)
        records, skipped = [], 0
        for row in json.loads(raw.payload)["value"]:
            if row.get("NumericValue") is None or any(row.get(d) is not None for d in ("Dim1", "Dim2", "Dim3")):
                skipped += 1
                continue
            iso, code = row["SpatialDim"], row["IndicatorCode"]
            if iso not in ISO3_TO_ID or code not in INDICATORS or row["SpatialDimType"] != "COUNTRY":
                raise ValueError("Unexpected WHO geography or indicator")
            year = row["TimeDim"]
            if year > raw.accessed_at.year:
                raise ValueError("WHO reference year is later than access date")
            country = ISO3_TO_ID[iso]
            records.append(Observation(id=f"who-{country}-{code}-{year}", country_id=country,
                indicator=code, label=INDICATORS[code], year=year, value=row["NumericValue"],
                unit="per_10000_population", provenance_id=provenance.id, source_record_id=str(row["Id"]),
                note=row.get("Comments") or "Country aggregate; definitions and coverage may differ."))
        return PublicDataset(adapter_version=self.version, provenance=provenance, records=records, skipped_records=skipped)
