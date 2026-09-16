from pathlib import Path

import pytest

from scripts.validate_submission import validate_submission


def write_csv(path: Path, rows: list[str]) -> None:
    path.write_text("id,tp_mm_day\n" + "\n".join(rows) + "\n", encoding="utf-8")


def test_submission_validator_preserves_ids_and_order(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    candidate = tmp_path / "candidate.csv"
    write_csv(sample, ["2023_01_-60.00_-90.00,0", "2023_01_-60.00_-89.75,0"])
    write_csv(candidate, ["2023_01_-60.00_-90.00,1.2", "2023_01_-60.00_-89.75,2.3"])
    assert validate_submission(sample, candidate) == 2


def test_submission_validator_rejects_reordered_ids(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    candidate = tmp_path / "candidate.csv"
    write_csv(sample, ["a,0", "b,0"])
    write_csv(candidate, ["b,1", "a,2"])
    with pytest.raises(ValueError, match="ordem divergente"):
        validate_submission(sample, candidate)
