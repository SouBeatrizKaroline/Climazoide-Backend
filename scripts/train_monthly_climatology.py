"""Treina, valida e exporta o baseline mensal completo sem vazamento temporal.

O baseline usa somente a precipitação histórica observada até dezembro de 2022.
Para cada mês-alvo, a previsão é a climatologia espacial do mesmo mês do ano,
calculada exclusivamente no período de treino. Os IDs são copiados, sem
reconstrução, do ``sample_submission.csv`` oficial.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import xarray as xr

EXPECTED_ROWS = 1_885_464
GRID_ROWS = 301
GRID_COLUMNS = 261
GRID_POINTS = GRID_ROWS * GRID_COLUMNS


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _monthly_climatology(tp: xr.DataArray, end: str) -> np.ndarray:
    training = tp.sel(time=slice(None, end))
    values = training.groupby("time.month").mean("time", skipna=False).values
    if values.shape != (12, GRID_ROWS, GRID_COLUMNS):
        raise ValueError(f"Grade inesperada na climatologia: {values.shape}.")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("A climatologia contém valor ausente, infinito ou negativo.")
    return values.astype(np.float32, copy=False)


def temporal_validation(tp: xr.DataArray) -> dict[str, float | int | str]:
    """Valida em bloco futuro: ajusta até 2018 e mede 2019–2022."""
    climatology = _monthly_climatology(tp, "2018-12-01")
    holdout = tp.sel(time=slice("2019-01-01", "2022-12-01"))
    if holdout.sizes.get("time") != 48:
        raise ValueError("A janela de validação 2019–2022 não contém 48 meses.")

    squared_error = 0.0
    observations = 0
    for index, timestamp in enumerate(holdout.time.values):
        month_index = int(str(timestamp)[5:7]) - 1
        truth = holdout.isel(time=index).values.astype(np.float64, copy=False)
        prediction = climatology[month_index].astype(np.float64, copy=False)
        finite = np.isfinite(truth)
        squared_error += float(np.square(truth[finite] - prediction[finite]).sum())
        observations += int(finite.sum())

    return {
        "metric": "RMSE",
        "unit": "mm/dia",
        "value": math.sqrt(squared_error / observations),
        "training_period": "1940-01/2018-12",
        "validation_period": "2019-01/2022-12",
        "observations": observations,
    }


def _validate_official_contract(tp: xr.DataArray, test: xr.Dataset) -> None:
    if tp.dims != ("time", "lat", "lon"):
        raise ValueError(f"Dimensões inesperadas em treino_tp.nc: {tp.dims}.")
    if tp.shape != (996, GRID_ROWS, GRID_COLUMNS):
        raise ValueError(f"Forma inesperada em treino_tp.nc: {tp.shape}.")
    if test.sizes.get("time") != 24:
        raise ValueError("teste_features.nc deve conter os 24 meses-alvo.")
    if test.sizes.get("lat") != GRID_ROWS or test.sizes.get("lon") != GRID_COLUMNS:
        raise ValueError("A grade oficial deve ser 301 × 261.")
    if not np.array_equal(tp.lat.values, test.lat.values) or not np.array_equal(
        tp.lon.values, test.lon.values
    ):
        raise ValueError("As coordenadas de treino e teste não coincidem.")
    if np.isfinite(test["tp_alvo"].values).any():
        raise ValueError("tp_alvo do teste contém valores; possível acesso indevido ao alvo.")

    target_months = test.time.values.astype("datetime64[M]")
    origin_months = test.time_origem.values.astype("datetime64[M]")
    if not np.array_equal(origin_months + np.timedelta64(1, "M"), target_months):
        raise ValueError("time_origem não corresponde exatamente ao mês T−1.")


def export_submission(
    sample_path: Path,
    output_path: Path,
    gzip_path: Path,
    test: xr.Dataset,
    climatology: np.ndarray,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    target_months = [str(value)[:7].replace("-", "_") for value in test.time.values]
    latitudes = test.lat.values
    longitudes = test.lon.values

    rows = 0
    with sample_path.open(encoding="utf-8-sig", newline="") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        reader = csv.reader(source)
        writer = csv.writer(destination, lineterminator="\n")
        if next(reader, None) != ["id", "tp_mm_day"]:
            raise ValueError("sample_submission.csv não tem as colunas oficiais esperadas.")
        writer.writerow(["id", "tp_mm_day"])

        for row_index, row in enumerate(reader):
            if len(row) != 2:
                raise ValueError(f"Linha oficial inválida: {row_index + 2}.")
            target_index, point_index = divmod(row_index, GRID_POINTS)
            if target_index >= len(target_months):
                raise ValueError("O arquivo oficial possui mais de 24 meses-alvo.")
            lat_index, lon_index = divmod(point_index, GRID_COLUMNS)
            expected_id = (
                f"{target_months[target_index]}_"
                f"{latitudes[lat_index]:.2f}_{longitudes[lon_index]:.2f}"
            )
            if row[0] != expected_id:
                raise ValueError(
                    f"ID ou ordem oficial divergente na linha {row_index + 2}: {row[0]!r}."
                )
            month_index = int(target_months[target_index][5:7]) - 1
            value = float(climatology[month_index, lat_index, lon_index])
            writer.writerow([row[0], f"{value:.6f}"])
            rows += 1

    if rows != EXPECTED_ROWS:
        raise ValueError(f"Quantidade de previsões inválida: {rows:,}.")

    with output_path.open("rb") as source, gzip_path.open("wb") as compressed:
        with gzip.GzipFile(fileobj=compressed, mode="wb", compresslevel=9, mtime=0) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    return rows


def run(data_dir: Path, output_path: Path, gzip_path: Path, report_path: Path) -> dict:
    tp_path = data_dir / "treino_tp.nc"
    test_path = data_dir / "teste_features.nc"
    sample_path = data_dir / "sample_submission.csv"
    for required in (tp_path, test_path, sample_path):
        if not required.is_file():
            raise FileNotFoundError(f"Arquivo oficial ausente: {required}.")

    with xr.open_dataset(tp_path) as train_dataset, xr.open_dataset(test_path) as test:
        tp = train_dataset["tp"]
        _validate_official_contract(tp, test)
        validation = temporal_validation(tp)
        climatology = _monthly_climatology(tp, "2022-12-01")
        rows = export_submission(sample_path, output_path, gzip_path, test, climatology)

    report = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_id": "monthly-climatology-v1",
        "method": "média espacial por mês do ano, ajustada somente com 1940–2022",
        "temporal_contract": "dados históricos até T−1 ou antes → previsão de T",
        "target_period": "2023-01/2024-12",
        "validation": validation,
        "submission": {
            "rows": rows,
            "columns": ["id", "tp_mm_day"],
            "sample_sha256": _sha256(sample_path),
            "csv_sha256": _sha256(output_path),
            "csv_bytes": output_path.stat().st_size,
            "gzip_sha256": _sha256(gzip_path),
            "gzip_bytes": gzip_path.stat().st_size,
        },
        "source_files": {
            "treino_tp.nc_sha256": _sha256(tp_path),
            "teste_features.nc_sha256": _sha256(test_path),
        },
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o CSV oficial completo com um baseline temporalmente válido."
    )
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/submission.csv"))
    parser.add_argument(
        "--gzip", dest="gzip_path", type=Path, default=Path("artifacts/submission.csv.gz")
    )
    parser.add_argument(
        "--report", type=Path, default=Path("artifacts/submission_report.json")
    )
    args = parser.parse_args()
    report = run(args.data_dir, args.output, args.gzip_path, args.report)
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
