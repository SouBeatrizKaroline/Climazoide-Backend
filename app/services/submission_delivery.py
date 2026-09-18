from pathlib import Path

SUBMISSION_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "submission.csv"

EXAMPLE_CSV = """id,tp_mm_day
2025_01_-30.00_-53.00,3.812
2025_01_-30.00_-52.75,4.507
2025_01_-30.00_-52.50,5.226
"""


def submission_status() -> dict:
    ready = SUBMISSION_PATH.is_file()
    return {
        "ready": ready,
        "filename": "submission.csv" if ready else None,
        "columns": ["id", "tp_mm_day"],
        "expected_rows": 1_885_464,
        "id_contract": "ano_mês_lat_lon, preservado do sample_submission.csv oficial",
        "temporal_contract": "Para prever M+1, usar somente dados disponíveis até M.",
        "example_available": True,
        "example_is_submittable": False,
        "blocking_reasons": [] if ready else [
            "sample_submission.csv oficial não está disponível no backend",
            "retreino sem vazamento temporal ainda está pendente",
            "pesos e transformadores finais não foram publicados",
            "o CSV completo ainda não passou pelo validador de IDs e ordem",
        ],
    }
