import csv
import json
import math
from itertools import zip_longest
from pathlib import Path

SUBMISSION_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "submission.csv"
OFFICIAL_IDS_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "sample_submission.csv"
MODEL_MANIFEST_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "model_manifest.json"
PARTIAL_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "submission-partial.csv"

EXAMPLE_CSV = """id,tp_mm_day
2025_01_-30.00_-53.00,3.812
2025_01_-30.00_-52.75,4.507
2025_01_-30.00_-52.50,5.226
"""


def submission_status() -> dict:
    ready, expected_rows, validation_reasons = _validate_submission()
    partial_available, partial_rows, partial_months, partial_reasons = (
        _validate_partial_submission()
    )
    if ready:
        partial_available, partial_rows, partial_months = False, 0, []
        partial_reasons = []
    partial_is_complete = bool(
        partial_available and expected_rows is not None and partial_rows == expected_rows
    )
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
        "partial_rows": partial_rows,
        "partial_target_months": partial_months,
        "partial_is_complete": partial_is_complete,
        "partial_notice": _partial_notice(
            partial_available, partial_rows, expected_rows, partial_months, partial_reasons
        ),
        "blocking_reasons": [] if ready else validation_reasons,
    }


def _partial_notice(
    available: bool,
    rows: int,
    expected_rows: int | None,
    months: list[str],
    reasons: list[str],
) -> str:
    if expected_rows is not None and rows == expected_rows and available:
        return "Todas as previsões dos IDs oficiais estão disponíveis; use o CSV completo."
    if not available:
        return reasons[0] if reasons else "Ainda não há previsões oficiais parciais validadas."
    target = ", ".join(months) if months else "meses não identificados"
    total = f" de {expected_rows:,} IDs oficiais" if expected_rows is not None else " IDs oficiais"
    return (
        f"{rows:,}{total}; meses-alvo presentes: {target}. "
        "Contém apenas previsões disponíveis, sem preencher IDs ausentes."
    )


def _validate_partial_submission() -> tuple[bool, int, list[str], list[str]]:
    if not OFFICIAL_IDS_PATH.is_file():
        return False, 0, [], ["aguardando o arquivo oficial de IDs do conjunto de teste"]
    model_blockers = _model_blockers()
    if model_blockers:
        return False, 0, [], model_blockers
    if not PARTIAL_PATH.is_file():
        return False, 0, [], ["ainda não há previsões oficiais parciais para baixar"]

    months: set[str] = set()
    rows = 0
    try:
        with (
            OFFICIAL_IDS_PATH.open(newline="", encoding="utf-8-sig") as source,
            PARTIAL_PATH.open(newline="", encoding="utf-8-sig") as partial,
        ):
            official_reader = csv.reader(source)
            partial_reader = csv.reader(partial)
            if next(official_reader, []) != ["id", "tp_mm_day"]:
                return False, 0, [], ["o arquivo oficial de IDs está inválido"]
            if next(partial_reader, []) != ["id", "tp_mm_day"]:
                return False, 0, [], ["o CSV parcial deve conter somente id,tp_mm_day"]

            expected = next(official_reader, None)
            for row_number, actual in enumerate(partial_reader, start=2):
                if len(actual) != 2:
                    return False, 0, [], [f"linha inválida no CSV parcial: {row_number}"]
                while expected is not None and len(expected) == 2 and expected[0] != actual[0]:
                    expected = next(official_reader, None)
                if expected is not None and len(expected) != 2:
                    return False, 0, [], ["o arquivo oficial de IDs contém uma linha inválida"]
                if expected is None:
                    return False, 0, [], ["ID parcial ausente no teste oficial ou fora da ordem"]
                try:
                    value = float(actual[1])
                except ValueError:
                    return False, 0, [], [f"previsão inválida no CSV parcial: linha {row_number}"]
                if not math.isfinite(value) or value < 0:
                    return False, 0, [], [f"previsão não válida no CSV parcial: linha {row_number}"]
                parts = actual[0].split("_")
                if len(parts) < 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
                    return False, 0, [], [f"mês-alvo inválido no ID parcial: linha {row_number}"]
                months.add(f"{parts[0]}-{parts[1]}")
                rows += 1
                expected = next(official_reader, None)
    except (OSError, csv.Error):
        return False, 0, [], ["não foi possível validar o CSV parcial contra os IDs oficiais"]

    if rows == 0:
        return False, 0, [], ["o CSV parcial não contém previsões"]
    return True, rows, sorted(months), []


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
    if manifest.get("scientific_audit", {}).get("status") != "passed":
        blockers.append("a auditoria temporal/científica ainda não foi aprovada")
    if manifest.get("temporal_contract_check", {}).get("passed") is not True:
        blockers.append("não há comprovação automatizada de features disponíveis até T−1")
    if manifest.get("artifacts", {}).get("inference_artifact_available") is not True:
        blockers.append("o artefato reproduzível de inferência ainda não foi publicado")
    if manifest.get("submission_validation", {}).get("passed") is not True:
        blockers.append("a validação científica e temporal da previsão ainda está pendente")
    return blockers
