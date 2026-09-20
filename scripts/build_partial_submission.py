"""Build a real partial submission from available model predictions and official IDs."""

from __future__ import annotations

import argparse
import csv
import math
import os
from pathlib import Path

EXPECTED_COLUMNS = ["id", "tp_mm_day"]


def build_partial_submission(
    official_ids: Path, candidate_predictions: Path, output: Path
) -> int:
    if official_ids.resolve() == candidate_predictions.resolve():
        raise ValueError("O arquivo de IDs de exemplo não pode ser usado como previsões.")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_suffix(output.suffix + ".tmp")
    rows_written = 0
    try:
        with (
            official_ids.open(newline="", encoding="utf-8-sig") as official_file,
            candidate_predictions.open(newline="", encoding="utf-8-sig") as predictions_file,
            temporary_output.open("w", newline="", encoding="utf-8") as output_file,
        ):
            official_reader = csv.reader(official_file)
            predictions_reader = csv.reader(predictions_file)
            if next(official_reader, []) != EXPECTED_COLUMNS:
                raise ValueError("O arquivo oficial deve conter id,tp_mm_day nessa ordem.")
            if next(predictions_reader, []) != EXPECTED_COLUMNS:
                raise ValueError("As previsões candidatas devem conter id,tp_mm_day.")

            writer = csv.writer(output_file, lineterminator="\n")
            writer.writerow(EXPECTED_COLUMNS)
            expected = next(official_reader, None)
            for line_number, prediction in enumerate(predictions_reader, start=2):
                if len(prediction) != 2:
                    raise ValueError(f"Previsão candidata malformada na linha {line_number}.")
                while expected is not None and expected[0] != prediction[0]:
                    expected = next(official_reader, None)
                if expected is None:
                    raise ValueError(
                        f"ID não oficial ou fora da ordem na linha {line_number}: {prediction[0]}"
                    )
                try:
                    value = float(prediction[1])
                except ValueError:
                    value = math.nan
                if math.isfinite(value) and value >= 0:
                    writer.writerow([expected[0], prediction[1]])
                    rows_written += 1
                expected = next(official_reader, None)

        if rows_written == 0:
            raise ValueError("Nenhuma previsão válida para IDs oficiais; parcial não gerado.")
        os.replace(temporary_output, output)
        return rows_written
    finally:
        temporary_output.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Monta um CSV parcial com as previsões válidas disponíveis, sem inventar valores."
        )
    )
    parser.add_argument("official_ids", type=Path)
    parser.add_argument("candidate_predictions", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/submission-partial.csv"),
    )
    args = parser.parse_args()
    count = build_partial_submission(args.official_ids, args.candidate_predictions, args.output)
    print(f"CSV parcial criado com {count:,} previsões válidas de IDs oficiais: {args.output}")


if __name__ == "__main__":
    main()
