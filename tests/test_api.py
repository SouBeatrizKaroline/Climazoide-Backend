from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["api_version"] == "0.3.1"
    assert response.json()["model_contract_version"] == "1.2"


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
    assert payload["execution"]["kaggle_notebook_ready"] is True
    assert payload["execution"]["gcp_artifact_export_optional"] is True
    assert payload["execution"]["entrypoint"] == "python kaggle_notebook.py"
    assert len(payload["candidate_models"]) == 6
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


def test_research_catalog_maps_every_remote_branch_without_promoting_metrics() -> None:
    response = client.get("/v1/research/branches")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_repository_modified"] is False
    assert payload["latest_branch"] == "feature/melhorar-pls-lstm-daiane"
    assert len(payload["branches"]) == 8
    assert payload["promotion_policy"]["production_metrics"] is False
    assert any(
        branch["name"] == "vermelho" and "correção de vazamento temporal" in branch["work"]
        for branch in payload["branches"]
    )


def test_submission_download_is_blocked_until_a_validated_artifact_exists() -> None:
    status = client.get("/v1/submission/status")
    assert status.status_code == 200
    assert status.json()["ready"] is False
    assert status.json()["example_is_submittable"] is False
    assert status.json()["partial_available"] is True
    assert status.json()["partial_is_complete"] is False
    assert status.json()["partial_rows"] == 78_561
    assert status.json()["expected_rows"] == 1_885_464
    assert client.get("/v1/submission/download").status_code == 409


def test_submission_example_is_clearly_named_as_not_valid() -> None:
    response = client.get("/v1/submission/example.csv")
    assert response.status_code == 200
    assert "not-valid" in response.headers["content-disposition"]
    assert response.text.startswith("id,tp_mm_day\n")


def test_research_partial_is_downloadable_in_the_public_format() -> None:
    response = client.get("/v1/submission/partial.csv")
    assert response.status_code == 200
    assert "climazoide-partial.csv" in response.headers["content-disposition"]
    header, first_row, *_ = response.text.splitlines()
    assert header == "id,tp_mm_day"
    assert len(first_row.split(",")) == 2
