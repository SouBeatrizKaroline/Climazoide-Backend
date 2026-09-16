from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["api_version"] == "0.2.0"
    assert response.json()["model_contract_version"] == "1.1"


def test_dashboard_does_not_serve_simulated_predictions() -> None:
    response = client.get("/v1/dashboard/summary")
    assert response.status_code == 503
    assert "retreino" in response.json()["detail"]


def test_catalog_separates_required_and_extra_sources() -> None:
    response = client.get("/v1/integrations/catalog")
    catalog = response.json()
    assert any(item["requirement"] == "required" for item in catalog)
    assert any(item["region"] == "national" for item in catalog)


def test_manifest_requires_retraining_and_has_no_active_metrics() -> None:
    response = client.get("/v1/model/manifest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "requires_retraining"
    assert "retreino obrigatório" in payload["evaluation_scope"]
    assert payload["metrics"] is None
    assert payload["artifacts"]["submission_available"] is False
    assert len(payload["candidate_models"]) == 4
    assert any(
        item["id"] == "convlstm" and item["status"] == "ready_for_training"
        for item in payload["candidate_models"]
    )
    assert any(item["ref"] == "vermelho" for item in payload["reviewed_sources"])
    assert any(
        item["id"] == "temporal_contract" and item["status"] == "passed"
        for item in payload["readiness"]
    )
    assert not any(
        item["status"] == "passed" for item in payload["readiness"]
        if item["id"] in {"retraining", "submission", "leaderboard"}
    )


def test_live_locations_are_real_coordinates() -> None:
    response = client.get("/v1/live/locations")
    assert response.status_code == 200
    locations = response.json()
    assert len(locations) == 13
    assert len({item["code"] for item in locations}) == 13
    assert any(item["id"] == "brasilia" and item["latitude"] < 0 for item in locations)
