import csv
import json
import math
from itertools import zip_longest
from pathlib import Path

SUBMISSION_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "submission.csv"
OFFICIAL_IDS_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "sample_submission.csv"
MODEL_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "model_manifest.json"
PARTIAL_PATH = (
    Path(__file__).resolve().parents[2]
    / "artifacts"
    / "climazoide-partial.csv"
)

EXAMPLE_CSV = """id,tp_mm_day
2025_01_-30.00_-53.00,3.812
2025_01_-30.00_-52.75,4.507
2025_01_-30.00_-52.50,5.226
"""


def submission_status() -> dict:
    ready, expected_rows, validation_reasons = _validate_submission()
    partial_available = PARTIAL_PATH.is_file()
    return {
        "ready": ready,
        "filename": "submission.csv" if ready else None,
        "columns": ["id", "tp_mm_day"],
        "expected_rows": expected_rows,
        "id_contract": (
            "IDs, meses, coordenadas e ordem devem ser preservados do arquivo oficial de teste"
        ),
        "temporal_contract": "Para prever M+1, usar somente dados disponíveis até M.",
        "example_available": True,
        "example_is_submittable": False,
        "partial_available": partial_available,
        "partial_filename": PARTIAL_PATH.name if partial_available else None,
        "partial_rows": 78_561,
        "partial_month": "2019-02",
        "partial_origin_month": "2019-01",
        "partial_model": "PLS lagged + LSTM",
        "partial_is_complete": False,
        "partial_notice": (
            "Recorte experimental de validação com um mês. Valores negativos foram "
            "limitados a zero. Não representa a entrega completa do projeto."
        ),
        "blocking_reasons": [] if ready else validation_reasons,
    }


def _validate_submission() -> tuple[bool, int | None, list[str]]:
    model_blockers = _model_blockers()
    if not OFFICIAL_IDS_PATH.is_file():
        return False, None, [
            "o arquivo oficial de IDs do conjunto de teste ainda não foi disponibilizado",
            "o CSV deve conter somente os IDs e meses pedidos, na ordem oficial",
            "a validação de cobertura e valores ainda não foi concluída",
            *model_blockers,
        ]
    if not SUBMISSION_PATH.is_file():
        try:
            with OFFICIAL_IDS_PATH.open(newline="", encoding="utf-8-sig") as source:
                reader = csv.reader(source)
                header = next(reader, [])
                expected_rows = sum(1 for _ in reader)
            if header != ["id", "tp_mm_day"]:
                return False, expected_rows, [
                    "o arquivo oficial de teste não tem as colunas esperadas"
                ]
        except (OSError, csv.Error):
            return False, None, ["não foi possível ler o arquivo oficial de IDs do teste"]
        return False, expected_rows, [
            "o CSV de previsões para os IDs oficiais ainda não foi gerado",
            *model_blockers,
        ]

    try:
        with (
            OFFICIAL_IDS_PATH.open(newline="", encoding="utf-8-sig") as source,
            SUBMISSION_PATH.open(newline="", encoding="utf-8-sig") as output,
        ):
            source_reader = csv.reader(source)
            output_reader = csv.reader(output)
            if next(source_reader, []) != ["id", "tp_mm_day"]:
                return False, None, ["o arquivo oficial de teste não tem as colunas esperadas"]
            if next(output_reader, []) != ["id", "tp_mm_day"]:
                return False, None, ["o CSV gerado não tem exatamente as colunas id,tp_mm_day"]
            expected_rows = 0
            first_issue = None
            for row_number, (expected, actual) in enumerate(
                zip_longest(source_reader, output_reader), start=1
            ):
                if expected is not None:
                    expected_rows += 1
                if expected is None or actual is None:
                    first_issue = first_issue or (
                        "o CSV gerado tem quantidade de linhas diferente do teste oficial"
                    )
                    continue
                if len(expected) != 2 or len(actual) != 2 or actual[0] != expected[0]:
                    first_issue = first_issue or f"ID ou ordem divergente na linha {row_number + 1}"
                    continue
                try:
                    prediction = float(actual[1])
                except ValueError:
                    first_issue = first_issue or f"previsão inválida na linha {row_number + 1}"
                    continue
                if not math.isfinite(prediction) or prediction < 0:
                    first_issue = first_issue or (
                        f"previsão ausente, não finita ou negativa na linha {row_number + 1}"
                    )
            if expected_rows == 0:
                return False, 0, ["o arquivo oficial de IDs do teste está vazio"]
            if first_issue:
                return False, expected_rows, [first_issue]
            if model_blockers:
                return False, expected_rows, model_blockers
    except (OSError, csv.Error, ValueError):
        return False, None, ["não foi possível conferir o CSV completo contra os IDs oficiais"]
    return True, expected_rows, []


def _model_blockers() -> list[str]:
    try:
        manifest = json.loads(MODEL_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["não há manifesto auditável de um modelo aprovado para submissão"]
    blockers = []
    if manifest.get("status") != "validated_for_submission":
        blockers.append("o modelo ainda não foi retreinado e validado para o período solicitado")
    if manifest.get("artifacts", {}).get("inference_artifact_available") is not True:
        blockers.append("o artefato reproduzível de inferência ainda não foi publicado")
    if manifest.get("submission_validation", {}).get("passed") is not True:
        blockers.append("a validação científica e temporal da previsão ainda está pendente")
    return blockers
