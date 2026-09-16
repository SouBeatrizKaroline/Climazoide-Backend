"""Valida uma submissão grande em streaming, sem carregar 1,8 milhão de linhas na memória."""

from __future__ import annotations

import argparse
import csv
import math
from itertools import zip_longest
from pathlib import Path

EXPECTED_COLUMNS = ["id", "tp_mm_day"]


def validate_submission(sample_path: Path, candidate_path: Path) -> int:
    with sample_path.open(encoding="utf-8", newline="") as sample_file, candidate_path.open(
        encoding="utf-8", newline=""
    ) as candidate_file:
        sample = csv.DictReader(sample_file)
        candidate = csv.DictReader(candidate_file)
        if sample.fieldnames != EXPECTED_COLUMNS or candidate.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                "Os dois CSVs devem ter exatamente as colunas id,tp_mm_day nessa ordem."
            )

        count = 0
        for line_number, pair in enumerate(zip_longest(sample, candidate), start=2):
            expected, received = pair
            if expected is None or received is None:
                raise ValueError(f"Quantidade de linhas divergente perto da linha {line_number}.")
            if expected["id"] != received["id"]:
                raise ValueError(
                    f"ID ou ordem divergente na linha {line_number}: {received['id']!r}."
                )
            try:
                value = float(received["tp_mm_day"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Previsão inválida na linha {line_number}.") from exc
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Previsão deve ser finita e não negativa na linha {line_number}.")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida contrato e ordem da submissão Kaggle.")
    parser.add_argument("sample", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    rows = validate_submission(args.sample, args.candidate)
    print(f"Submissão válida: {rows:,} linhas, IDs e ordem preservados.")


if __name__ == "__main__":
    main()
