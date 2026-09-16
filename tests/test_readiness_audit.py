from pathlib import Path

from scripts.audit_readiness import audit_dataset
from scripts.download_competition import EXPECTED_FILES


def test_readiness_audit_lists_missing_official_files(tmp_path: Path) -> None:
    (tmp_path / "sample_submission.csv").write_text("id,tp_mm_day\n", encoding="utf-8")

    missing = audit_dataset(tmp_path)

    assert "sample_submission.csv" not in missing
    assert set(missing) == EXPECTED_FILES - {"sample_submission.csv"}
