from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["api_version"] == "0.3.2"
    assert response.json()["model_contract_version"] == "1.3"


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
    assert payload["execution"]["notebook_execution_ready"] is True
    assert payload["execution"]["cloud_artifact_export_optional"] is True
    assert payload["execution"]["entrypoint"] == "documentado no README"
    assert len(payload["candidate_models"]) == 6
    assert any(
        item["id"] == "convlstm" and item["status"] == "not_implemented"
        for item in payload["candidate_models"]
    )
    assert any(item["ref"] == "vermelho" for item in payload["reviewed_sources"])
    assert any(
        item["id"] == "temporal_contract" and item["status"] == "pending"
        for item in payload["readiness"]
    )
    assert not any(
        item["status"] == "passed" for item in payload["readiness"]
        if item["id"] in {"retraining", "submission", "official_score"}
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
    assert payload["technical_audit"]["status"] == "critical"
    assert payload["technical_audit"]["latest_branch_temporal_alignment"] == "not_compliant"
    assert any(
        branch["name"] == "vermelho"
        and "correção do deslocamento atmosférico presente nesta branch" in branch["work"]
        for branch in payload["branches"]
    )


def test_submission_download_is_blocked_until_a_validated_artifact_exists() -> None:
    status = client.get("/v1/submission/status")
    assert status.status_code == 200
    assert status.json()["ready"] is False
    assert status.json()["example_is_submittable"] is False
    assert status.json()["partial_available"] is False
    assert status.json()["partial_is_complete"] is False
    assert status.json()["partial_rows"] == 0
    assert "arquivo oficial de IDs" in status.json()["partial_notice"]
    assert status.json()["expected_rows"] is None
    assert client.get("/v1/submission/download").status_code == 409


def test_submission_manifest_without_temporal_audit_cannot_be_promoted(
    tmp_path, monkeypatch
) -> None:
    from app.services import submission_delivery

    manifest = tmp_path / "model_manifest.json"
    monkeypatch.setattr(submission_delivery, "MODEL_MANIFEST_PATH", manifest)
    manifest.write_text(
        '{"status":"validated_for_submission",'
        '"artifacts":{"inference_artifact_available":true},'
        '"submission_validation":{"passed":true}}'
    )

    blockers = submission_delivery._model_blockers()
    assert any("auditoria temporal/científica" in blocker for blocker in blockers)
    assert any("comprovação automatizada" in blocker for blocker in blockers)


def test_submission_requires_the_official_test_ids_and_matching_order(
    tmp_path, monkeypatch
) -> None:
    from app.services import submission_delivery

    official = tmp_path / "sample_submission.csv"
    prediction = tmp_path / "submission.csv"
    manifest = tmp_path / "model_manifest.json"
    monkeypatch.setattr(submission_delivery, "OFFICIAL_IDS_PATH", official)
    monkeypatch.setattr(submission_delivery, "SUBMISSION_PATH", prediction)
    monkeypatch.setattr(submission_delivery, "MODEL_MANIFEST_PATH", manifest)
    manifest.write_text(
        '{"status":"validated_for_submission",'
        '"scientific_audit":{"status":"passed"},'
        '"temporal_contract_check":{"passed":true},'
        '"artifacts":{"inference_artifact_available":true},'
        '"submission_validation":{"passed":true}}'
    )
    official.write_text("id,tp_mm_day\n2026_09_-30.00_-53.00,\n2026_09_-30.00_-52.75,\n")
    prediction.write_text(
        "id,tp_mm_day\n2026_09_-30.00_-53.00,1.25\n2026_09_-30.00_-52.75,0\n"
    )

    assert submission_delivery._validate_submission() == (True, 2, [])

    prediction.write_text(
        "id,tp_mm_day\n2026_09_-30.00_-52.75,1.25\n2026_09_-30.00_-53.00,0\n"
    )
    ready, rows, reasons = submission_delivery._validate_submission()
    assert ready is False
    assert rows == 2
    assert "ID ou ordem divergente" in reasons[0]


def test_submission_example_is_clearly_named_as_not_valid() -> None:
    response = client.get("/v1/submission/example.csv")
    assert response.status_code == 200
    assert "not-valid" in response.headers["content-disposition"]
    assert response.text.startswith("id,tp_mm_day\n")


def test_research_experiment_is_not_exposed_as_an_official_partial_submission() -> None:
    response = client.get("/v1/submission/partial.csv")
    assert response.status_code == 409
    assert "previsões oficiais parciais validadas" in response.json()["detail"]


def test_partial_submission_contains_only_valid_official_ids_in_original_order(
    tmp_path, monkeypatch
) -> None:
    from app.services import submission_delivery

    official = tmp_path / "sample_submission.csv"
    partial = tmp_path / "submission-partial.csv"
    manifest = tmp_path / "model_manifest.json"
    monkeypatch.setattr(submission_delivery, "OFFICIAL_IDS_PATH", official)
    monkeypatch.setattr(submission_delivery, "PARTIAL_PATH", partial)
    monkeypatch.setattr(submission_delivery, "MODEL_MANIFEST_PATH", manifest)
    manifest.write_text(
        '{"status":"validated_for_submission",'
        '"scientific_audit":{"status":"passed"},'
        '"temporal_contract_check":{"passed":true},'
        '"artifacts":{"inference_artifact_available":true},'
        '"submission_validation":{"passed":true}}'
    )
    official.write_text(
        "id,tp_mm_day\n2023_01_-60.00_-90.00,0\n"
        "2023_01_-60.00_-89.75,0\n2023_02_-60.00_-90.00,0\n"
    )
    partial.write_text(
        "id,tp_mm_day\n2023_01_-60.00_-90.00,1.2\n"
        "2023_02_-60.00_-90.00,2.3\n"
    )

    assert submission_delivery._validate_partial_submission() == (
        True,
        2,
        ["2023-01", "2023-02"],
        [],
    )
