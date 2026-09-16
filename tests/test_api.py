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
    assert payload["context"]["grid_points"] == 78561
    assert payload["context"]["submission_rows"] == 1885464


def test_dashboard_filters_month_and_region() -> None:
    response = client.get(
        "/v1/dashboard/summary", params={"target_month": "2023-07", "region": "amazonia"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["target_month"] == "Julho de 2023"
    assert payload["region"] == "amazonia"
    assert payload["context"]["origin_month"] == "2023-06"


def test_dashboard_rejects_month_outside_competition() -> None:
    response = client.get("/v1/dashboard/summary", params={"target_month": "2025-01"})
    assert response.status_code == 422


def test_catalog_separates_required_and_extra_sources() -> None:
    response = client.get("/v1/integrations/catalog")
    catalog = response.json()
    assert any(item["requirement"] == "required" for item in catalog)
    assert any(item["region"] == "national" for item in catalog)
