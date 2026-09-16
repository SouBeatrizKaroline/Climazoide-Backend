"""Audita arquivos locais antes de treinar ou enviar uma submissão ao Kaggle."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.download_competition import EXPECTED_FILES
from scripts.validate_submission import validate_submission

EXPECTED_ROWS = 1_885_464


def audit_dataset(data_dir: Path) -> list[str]:
    found = {item.name for item in data_dir.rglob("*") if item.is_file()}
    return sorted(EXPECTED_FILES - found)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Confere dataset oficial e, opcionalmente, uma submissão candidata."
    )
    parser.add_argument("data_dir", type=Path, help="Diretório com os 13 arquivos do Kaggle.")
    parser.add_argument("--submission", type=Path, help="CSV candidato a validar.")
    args = parser.parse_args()

    missing = audit_dataset(args.data_dir)
    if missing:
        raise SystemExit(f"NÃO PRONTO: arquivos oficiais ausentes: {', '.join(missing)}")

    print("OK: os 13 arquivos oficiais estão presentes.")
    if args.submission:
        sample = args.data_dir / "sample_submission.csv"
        rows = validate_submission(sample, args.submission)
        if rows != EXPECTED_ROWS:
            raise SystemExit(
                f"NÃO PRONTO: esperado {EXPECTED_ROWS:,} linhas; recebido {rows:,}."
            )
        print(f"OK: submissão preserva os IDs oficiais e possui {rows:,} linhas.")
    else:
        print("PENDENTE: nenhuma submissão candidata foi informada para validação.")


if __name__ == "__main__":
    main()
