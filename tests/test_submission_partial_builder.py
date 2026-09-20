import pytest

from scripts.build_partial_submission import build_partial_submission


def test_builder_keeps_only_valid_predictions_for_official_ids_in_order(tmp_path) -> None:
    official = tmp_path / "sample_submission.csv"
    candidate = tmp_path / "model_predictions.csv"
    output = tmp_path / "submission-partial.csv"
    official.write_text(
        "id,tp_mm_day\n2023_01_-60.00_-90.00,0\n"
        "2023_01_-60.00_-89.75,0\n2023_02_-60.00_-90.00,0\n"
    )
    candidate.write_text(
        "id,tp_mm_day\n2023_01_-60.00_-90.00,1.2\n"
        "2023_01_-60.00_-89.75,NaN\n2023_02_-60.00_-90.00,2.3\n"
    )

    rows = build_partial_submission(official, candidate, output)

    assert rows == 2
    assert output.read_text() == (
        "id,tp_mm_day\n2023_01_-60.00_-90.00,1.2\n2023_02_-60.00_-90.00,2.3\n"
    )


def test_builder_rejects_ids_outside_the_official_template(tmp_path) -> None:
    official = tmp_path / "sample_submission.csv"
    candidate = tmp_path / "model_predictions.csv"
    output = tmp_path / "submission-partial.csv"
    official.write_text("id,tp_mm_day\n2023_01_-60.00_-90.00,0\n")
    candidate.write_text("id,tp_mm_day\n2024_01_-60.00_-90.00,1.2\n")

    with pytest.raises(ValueError, match="ID não oficial"):
        build_partial_submission(official, candidate, output)
