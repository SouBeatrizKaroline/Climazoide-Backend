from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_does_not_claim_unverified_metrics() -> None:
    response = client.get("/v1/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["precipitation"]["status"] == "demo"
    assert all(metric["status"] == "unavailable" for metric in payload["metrics"])


def test_catalog_separates_required_and_extra_sources() -> None:
    response = client.get("/v1/integrations/catalog")
    catalog = response.json()
    assert any(item["requirement"] == "required" for item in catalog)
    assert any(item["region"] == "national" for item in catalog)
