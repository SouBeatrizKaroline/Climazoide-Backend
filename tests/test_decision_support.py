from app.services.decision_support import options, scenario


def test_catalog_has_all_locations_and_months():
    payload = options()
    assert len(payload["locations"]) == 13
    assert len(payload["target_months"]) == 24


def test_scenario_is_separate_from_official_submission():
    payload = scenario("brasilia", "2024-12", "risk-areas")
    assert payload["official_submission_unchanged"] is True
    assert payload["is_current_forecast"] is False
    assert payload["scenario"]["predicted_mm_day"] >= 0
    assert "evacuação" in payload["guidance"]["limitation"]
    assert "2023–2024" in payload["provenance"]["notice"]


def test_invalid_sector_is_rejected():
    try:
        scenario("brasilia", "2024-12", "invalid")
    except ValueError as exc:
        assert "Setor" in str(exc)
    else:
        raise AssertionError("Setor inválido deveria ser rejeitado.")
