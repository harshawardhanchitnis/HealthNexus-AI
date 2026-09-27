from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.network import Status
from app.services.summary import summarize
from app.simulation.generator import generate_snapshot, inventory_status


@pytest.fixture(scope="module")
def snapshot():
    return generate_snapshot(42, date(2026, 9, 27))


@pytest.fixture(scope="module")
def client(snapshot):
    class Repository:
        mode = "test"
        def snapshot(self):
            return snapshot
    with TestClient(create_app(Repository())) as client:
        yield client


def test_india_coverage_and_reproducibility(snapshot):
    assert len(snapshot.regions) == 36
    assert sum(r.kind == "state" for r in snapshot.regions) == 28
    assert sum(r.kind == "union_territory" for r in snapshot.regions) == 8
    assert {f.state_id for f in snapshot.facilities} == {r.id for r in snapshot.regions}
    assert snapshot == generate_snapshot(42, date(2026, 9, 27))
    assert len({f.id for f in snapshot.facilities}) == len(snapshot.facilities)


def test_operational_conservation(snapshot):
    for f in snapshot.facilities:
        assert f.beds.total == f.beds.available + f.beds.occupied + f.beds.reserved
        assert f.staff.doctors_present + f.staff.nurses_present <= f.staff.present <= f.staff.scheduled
        assert f.footfall_today == f.history[-1].footfall
        assert len(f.history) == 28
        for i in f.inventory:
            assert i.current_stock == i.opening_stock + i.units_received - i.units_consumed
            assert i.days_of_cover == round(i.current_stock / i.average_daily_consumption, 1)
            assert i.safety_stock >= i.average_daily_consumption * 7


@pytest.mark.parametrize("days,status", [(0, Status.CRITICAL), (2.9, Status.CRITICAL),
    (3, Status.AT_RISK), (6.9, Status.AT_RISK), (7, Status.WATCH), (10, Status.HEALTHY)])
def test_inventory_thresholds(days, status):
    assert inventory_status(days) == status


def test_rollup_matches_state_totals(client):
    overview = client.get("/api/overview").json()
    assert overview["summary"]["facilities"] == sum(r["facilities"] for r in overview["regions"])
    assert overview["summary"]["patient_footfall"] == overview["history"][-1]["footfall"]
    assert sum(overview["summary"]["status_counts"].values()) == overview["summary"]["facilities"]
    assert sum(r["occupied_beds"] for r in overview["regions"]) == overview["summary"]["occupied_beds"]


def test_filtering_and_drilldown(client):
    states = client.get("/api/regions").json()
    pune = next(d for d in states["districts"] if d["name"] == "Pune")
    result = client.get("/api/facilities", params={"state_id": "MH", "district_id": pune["id"]}).json()
    assert result["total"] == 3
    assert all(f["state_id"] == "MH" and f["district_id"] == pune["id"] for f in result["items"])
    detail = client.get(f'/api/facilities/{result["items"][0]["id"]}').json()
    assert len(detail["facility"]["inventory"]) == 5
    assert client.get("/api/overview?state_id=KA&district_id=MH-PUNE").status_code == 404
    assert client.get("/api/facilities/nonexistent").status_code == 404
    assert client.get("/api/facilities?limit=0").status_code == 422
    assert client.get("/api/facilities?status=invalid").status_code == 422
    assert client.get("/api/facilities?search=does-not-exist").json()["total"] == 0


def test_alerts_and_inventory_are_scoped(client):
    alerts = client.get("/api/alerts?state_id=MH").json()["items"]
    assert all(a["state_id"] == "MH" for a in alerts)
    items = client.get("/api/inventory?state_id=MH&district_id=MH-PUNE").json()["items"]
    assert all(i["facilities"] == 3 for i in items)
    critical = client.get("/api/alerts?severity=CRITICAL").json()["items"]
    assert critical and all(a["severity"] == "CRITICAL" for a in critical)


def test_empty_rollup_is_safe():
    result = summarize([])
    assert result["medicine_availability"] == result["bed_utilisation"] == result["staff_availability"] == 0


def test_health_and_storage_failure(client):
    assert client.get("/api/health").json()["country"] == "IN"
    class BrokenRepository:
        mode = "firestore"
        def snapshot(self):
            raise RuntimeError("private storage detail")
    with TestClient(create_app(BrokenRepository())) as broken:
        response = broken.get("/api/overview")
        assert response.status_code == 503
        assert "private storage detail" not in response.text

