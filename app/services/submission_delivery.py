from pathlib import Path

SUBMISSION_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "submission.csv"
PARTIAL_PATH = (
    Path(__file__).resolve().parents[2]
    / "artifacts"
    / "research-partial-not-submittable.csv"
)

EXAMPLE_CSV = """id,tp_mm_day
2025_01_-30.00_-53.00,3.812
2025_01_-30.00_-52.75,4.507
2025_01_-30.00_-52.50,5.226
"""


def submission_status() -> dict:
    ready = SUBMISSION_PATH.is_file()
    partial_available = PARTIAL_PATH.is_file()
    return {
        "ready": ready,
        "filename": "submission.csv" if ready else None,
        "columns": ["id", "tp_mm_day"],
        "expected_rows": 1_885_464,
        "id_contract": "ano_mês_lat_lon, preservado do sample_submission.csv oficial",
        "temporal_contract": "Para prever M+1, usar somente dados disponíveis até M.",
        "example_available": True,
        "example_is_submittable": False,
        "partial_available": partial_available,
        "partial_filename": PARTIAL_PATH.name if partial_available else None,
        "partial_rows": 78_561,
        "partial_month": "2019-02",
        "partial_origin_month": "2019-01",
        "partial_model": "PLS lagged + LSTM",
        "partial_source_branch": "vermelho",
        "partial_source_commit": "62b3626",
        "partial_is_submittable": False,
        "partial_notice": (
            "Recorte experimental de validação com um mês e colunas de proveniência. "
            "Valores negativos foram limitados a zero. Não corresponde ao período de "
            "teste do Kaggle e não deve ser enviado à competição."
        ),
        "blocking_reasons": [] if ready else [
            "sample_submission.csv oficial não está disponível no backend",
            "retreino sem vazamento temporal ainda está pendente",
            "pesos e transformadores finais não foram publicados",
            "o CSV completo ainda não passou pelo validador de IDs e ordem",
        ],
    }
