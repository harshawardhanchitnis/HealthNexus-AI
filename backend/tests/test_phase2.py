import json
import shutil
from datetime import date
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import ROOT
from app.core.geography import COUNTRY_BY_ID
from app.data_ingestion.base import read_raw, raw_snapshot
from app.data_ingestion.catalog import ADAPTERS, RAW_PATHS, datasets, import_source, latest_observations
from app.data_ingestion.india_hdi import IndiaHDIAdapter, URL
from app.data_ingestion.who_gho import WHOGHOAdapter
from app.main import create_app
from app.models.network import Beds, Snapshot, StockDay
from app.models.provenance import Observation, Provenance
from app.simulation.generator import generate_snapshot


@pytest.fixture(scope="module")
def nodes():
    return {code: generate_snapshot(42, date(2026, 9, 27), code) for code in COUNTRY_BY_ID}


@pytest.fixture(scope="module")
def client(nodes):
    class Repository:
        mode = "test"
        def snapshot(self):
            return nodes["IN"]
        def country_snapshot(self, country_id):
            return nodes[country_id]
    with TestClient(create_app(Repository())) as client:
        yield client


def test_official_india_parse_is_not_fabricated():
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["india_hdi"])
    result = IndiaHDIAdapter().normalize(raw)
    values = {r.indicator: r.value for r in result.records}
    assert len(result.records) == 13
    assert values["phc_count"] == 31882
    assert values["phc_doctors"] == 40583
    assert values["phc_nurses"] == 47932
    assert values["chc_count"] == 6359
    assert result.provenance.source_type == "official_public"
    assert not result.provenance.is_synthetic
    assert {r.year for r in result.records} == {2023}


def test_india_fetch_handles_duplicate_accessible_article(monkeypatch):
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["india_hdi"])
    html = "".join(f"<p><strong>{line}</strong></p>" for line in raw.payload.splitlines())
    response = httpx.Response(200, text=html + html, request=httpx.Request("GET", URL))
    monkeypatch.setattr("app.data_ingestion.india_hdi.httpx.get", lambda *a, **kw: response)
    assert len(IndiaHDIAdapter().normalize(IndiaHDIAdapter().fetch()).records) == 13


def test_who_parse_preserves_units_years_and_source_ids():
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["who_gho"])
    result = WHOGHOAdapter().normalize(raw)
    assert len(result.records) == 20
    assert {r.country_id for r in result.records} == set(COUNTRY_BY_ID)
    assert {r.unit for r in result.records} == {"per_10000_population"}
    assert {r.indicator for r in result.records} == {"WHS6_102", "HWF_0001"}
    assert all(r.source_record_id and r.year <= result.provenance.accessed_at.year for r in result.records)
    assert max(r.year for r in result.records if r.country_id == "ZA" and r.indicator == "WHS6_102") == 2010


def test_who_fetch_follows_pagination_and_keeps_country_subsets(monkeypatch):
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["who_gho"])
    rows = json.loads(raw.payload)["value"]
    original_client = httpx.Client
    calls = []
    def handler(request):
        calls.append(str(request.url))
        code = request.url.path.rsplit("/", 1)[-1]
        matching = [row for row in rows if row["IndicatorCode"] == code]
        if "page=2" in str(request.url):
            return httpx.Response(200, json={"value": matching[5:]})
        return httpx.Response(200, json={"value": matching[:5], "@odata.nextLink": f"https://ghoapi.azureedge.net/api/{code}?page=2"})
    monkeypatch.setattr("app.data_ingestion.who_gho.httpx.Client", lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    assert len(WHOGHOAdapter().normalize(WHOGHOAdapter().fetch()).records) == 20
    assert len(calls) == 4


def test_who_untrusted_pagination_rejected(monkeypatch):
    original_client = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"value": [], "@odata.nextLink": "https://untrusted.example/records"}))
    monkeypatch.setattr("app.data_ingestion.who_gho.httpx.Client", lambda **kwargs: original_client(transport=transport, **kwargs))
    with pytest.raises(ValueError, match="Untrusted"):
        WHOGHOAdapter().fetch()


@pytest.mark.parametrize("mutation", ["negative", "duplicate", "foreign", "nan"])
def test_invalid_who_observations_rejected(mutation):
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["who_gho"])
    payload = json.loads(raw.payload)
    if mutation == "negative": payload["value"][0]["NumericValue"] = -1
    if mutation == "duplicate": payload["value"].append(payload["value"][0])
    if mutation == "foreign": payload["value"][0]["SpatialDim"] = "USA"
    if mutation == "nan": payload["value"][0]["NumericValue"] = "NaN"
    changed = raw_snapshot(raw.adapter, str(raw.source_url), json.dumps(payload), raw.format, raw.extraction)
    with pytest.raises(ValueError): WHOGHOAdapter().normalize(changed)


def test_missing_values_are_skipped_not_zero_imputed():
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["who_gho"])
    payload = json.loads(raw.payload)
    payload["value"][0]["NumericValue"] = None
    changed = raw_snapshot(raw.adapter, str(raw.source_url), json.dumps(payload), raw.format, raw.extraction)
    result = WHOGHOAdapter().normalize(changed)
    assert len(result.records) == 19 and result.skipped_records == 1


def test_offline_import_and_tamper_detection(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "data/official", tmp_path / "data/official")
    def no_network(*args, **kwargs): raise AssertionError("Offline import attempted a download")
    for adapter in ADAPTERS.values(): monkeypatch.setattr(adapter, "fetch", no_network)
    for name in ADAPTERS: import_source(name, root=tmp_path)
    assert sum(len(data.records) for data in datasets(tmp_path)) == 33
    normalized = tmp_path / "data/normalized/india_hdi.json"
    altered = json.loads(normalized.read_text(encoding="utf-8"))
    altered["records"][0]["value"] += 1
    normalized.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"): datasets(tmp_path)
    raw = read_raw(ROOT / "data/official" / RAW_PATHS["india_hdi"])
    raw.payload += " tampered"
    with pytest.raises(ValueError, match="checksum"): raw.verify()


def test_failed_refresh_preserves_cache(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "data/official", tmp_path / "data/official")
    import_source("india_hdi", root=tmp_path)
    target = tmp_path / "data/normalized/india_hdi.json"
    before = target.read_bytes()
    malformed = raw_snapshot("india_hdi", URL, "missing fields", "text/plain", "bad")
    monkeypatch.setattr(IndiaHDIAdapter, "fetch", lambda self: malformed)
    with pytest.raises(ValueError): import_source("india_hdi", refresh=True, root=tmp_path)
    assert target.read_bytes() == before


@pytest.mark.parametrize("country", list(COUNTRY_BY_ID))
def test_country_nodes_are_separate_and_consistent(nodes, country):
    data = nodes[country]
    assert all(f.country_id == country for f in data.facilities)
    assert len(data.facilities) == (207 if country == "IN" else 6)
    assert len(data.regions) == (36 if country == "IN" else 2)
    if country != "IN": assert data.districts == [] and all(f.district_id is None for f in data.facilities)
    other_ids = {f.id for code, node in nodes.items() if code != country for f in node.facilities}
    assert not other_ids.intersection(f.id for f in data.facilities)
    official_ids = {row.id for dataset in datasets() for row in dataset.records}
    assert data.calibration["public_sources_available"] and not data.calibration["fallbacks"]
    for f in data.facilities:
        assert set(f.calibration_ids) <= official_ids
        assert data.provenance[f.provenance_id].is_synthetic
        for i, day in enumerate(f.history):
            assert day.occupied_beds == day.previous_occupied + day.admissions - day.discharges
            assert day.occupied_beds <= f.beds.total - f.beds.reserved
            assert day.footfall == sum(day.syndrome_counts.values())
            assert day.medicine_units == sum(item.ledger[i].consumed for item in f.inventory)
        for item in f.inventory:
            for a, b in zip(item.ledger, item.ledger[1:]): assert a.closing == b.opening
            assert all(d.consumed <= d.opening+d.received and d.requested == d.consumed+d.unmet_demand for d in item.ledger)
    assert any(d.unmet_demand > 0 for f in data.facilities for item in f.inventory for d in item.ledger)


def test_real_anchors_reach_generator(nodes):
    hdi = latest_observations("IN")
    assert nodes["IN"].calibration["doctors_by_type"][0] == hdi["phc_doctors"].value / hdi["phc_count"].value
    assert nodes["BR"].calibration["beds_per_10000"] == latest_observations("BR")["WHS6_102"].value
    assert nodes["BR"].facilities[0].beds.total != nodes["IN"].facilities[0].beds.total


def test_api_country_filtering_and_provenance(client):
    assert len(client.get("/api/countries").json()["items"]) == 5
    assert client.get("/api/overview").json()["summary"]["facilities"] == 207
    assert client.get("/api/overview?country_id=BR").json()["summary"]["facilities"] == 6
    assert client.get("/api/overview?country_id=BR&state_id=MH").status_code == 404
    assert client.get("/api/facilities/BR-SP-001?country_id=IN").status_code == 404
    assert client.get("/api/overview?country_id=XX").status_code == 422
    detail = client.get("/api/facilities/BR-SP-001?country_id=BR").json()
    assert detail["facility"]["synthetic"] is True
    assert detail["provenance"][detail["facility"]["provenance_id"]]["source_type"] == "synthetic"
    sources = client.get("/api/data-sources?country_id=BR").json()
    assert len(sources["records"]) == 4
    assert all(r["country_id"] == "BR" for r in sources["records"])


@pytest.mark.parametrize("mutation", ["coordinate", "country", "district", "provenance"])
def test_invalid_network_graph_rejected(nodes, mutation):
    payload = nodes["IN"].model_dump(mode="json")
    f = payload["facilities"][0]
    if mutation == "coordinate": f["latitude"] = 91
    if mutation == "country": f["country_id"] = "BR"
    if mutation == "district": f["district_id"] = "MH-PUNE"
    if mutation == "provenance": f["provenance_id"] = "nonexistent"
    with pytest.raises(ValidationError): Snapshot.model_validate(payload)


def test_legacy_schema_is_labelled_not_reclassified(nodes):
    payload = nodes["IN"].model_dump(mode="json")
    payload["schema_version"] = 1
    payload.pop("provenance"); payload.pop("calibration")
    def strip_ids(value):
        if isinstance(value, dict):
            value.pop("provenance_id", None)
            for child in value.values(): strip_ids(child)
        elif isinstance(value, list):
            for child in value: strip_ids(child)
    strip_ids(payload)
    legacy = Snapshot.model_validate(payload)
    assert legacy.calibration == {}
    assert legacy.provenance["synthetic-v1"].is_synthetic
    assert "Uncalibrated" in legacy.provenance["synthetic-v1"].methodology


def test_bounds_and_honest_source_classification():
    with pytest.raises(ValidationError):
        StockDay(date=date.today(), opening=3, received=0, requested=5, consumed=5, unmet_demand=0, closing=0)
    with pytest.raises(ValidationError): Beds(total=3, occupied=4, available=0, reserved=0)
    with pytest.raises(ValidationError):
        Observation(id="x", country_id="IN", indicator="x", label="x", year=2023, value=101, unit="percent", provenance_id="x", source_record_id="x")
    with pytest.raises(ValidationError):
        Provenance(id="x", source_type="official_public", source_name="x", accessed_at=date.today(), geography=["IN"], is_synthetic=True, methodology="x", version="x")
