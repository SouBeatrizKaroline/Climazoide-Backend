"""Treina um candidato XGBoost de anomalias com contrato temporal auditável.

Para um alvo T e horizonte L, as entradas são a atmosfera de T-1, a
precipitação congelada na origem T-L e o próprio horizonte. O alvo é a
anomalia de precipitação em T em relação à climatologia mensal. Nenhum valor
de precipitação de 2023-2024 é lido.
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

import joblib
import numpy as np
import xarray as xr
from xgboost import XGBRegressor

FEATURES = (
    "t2",
    "cloud_cover",
    "surface_pressure",
    "shum_850",
    "rel_hum_850",
    "temperature_850",
    "geopotential_850",
    "u_850",
    "v_850",
)
TRAIN_FILES = {name: f"treino_{name}.nc" for name in FEATURES}
GRID_ROWS = 301
GRID_COLUMNS = 261
GRID_POINTS = GRID_ROWS * GRID_COLUMNS
EXPECTED_ROWS = 1_885_464
FEATURE_NAMES = [
    *(f"{name}_anomaly" for name in FEATURES),
    "tp_origin",
    "tp_origin_anomaly",
    "target_climatology",
    "latitude",
    "longitude",
    "target_month_sin",
    "target_month_cos",
    "lag_normalized",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _time_index(values: np.ndarray) -> np.ndarray:
    return values.astype("datetime64[M]")


def _monthly_climatology(values: np.ndarray, times: np.ndarray, end_index: int) -> np.ndarray:
    months = (times[: end_index + 1].astype("datetime64[M]").astype(int) % 12) + 1
    return np.stack(
        [np.nanmean(values[: end_index + 1][months == month], axis=0) for month in range(1, 13)]
    ).astype(np.float32)


def _load_variable(data_dir: Path, name: str) -> tuple[np.ndarray, np.ndarray]:
    path = data_dir / ("treino_tp.nc" if name == "tp" else TRAIN_FILES[name])
    with xr.open_dataset(path) as dataset:
        variable = "tp" if name == "tp" else name
        return (
            dataset[variable].values.astype(np.float32),
            _time_index(dataset.time.values),
        )


def _sample_coordinates(
    rng: np.random.Generator,
    count: int,
    first_target: int,
    last_target: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    target = rng.integers(first_target, last_target + 1, count, dtype=np.int32)
    lag = rng.integers(1, 25, count, dtype=np.int16)
    lag = np.minimum(lag, target).astype(np.int16)
    origin = target - lag
    point = rng.integers(0, GRID_POINTS, count, dtype=np.int32)
    return target, origin, lag, point


def _atmospheric_feature_index(target: np.ndarray) -> np.ndarray:
    """Retorna exclusivamente o mês imediatamente anterior ao alvo."""
    return target - 1


def _base_features(
    count: int,
    target: np.ndarray,
    origin: np.ndarray,
    lag: np.ndarray,
    point: np.ndarray,
    times: np.ndarray,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    tp: np.ndarray,
    tp_climatology: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    lat_index, lon_index = np.divmod(point, GRID_COLUMNS)
    target_month = (times[target].astype(int) % 12).astype(np.int16)
    origin_month = (times[origin].astype(int) % 12).astype(np.int16)
    matrix = np.empty((count, len(FEATURE_NAMES)), dtype=np.float32)
    matrix[:, len(FEATURES)] = tp[origin, lat_index, lon_index]
    matrix[:, len(FEATURES) + 1] = (
        matrix[:, len(FEATURES)] - tp_climatology[origin_month, lat_index, lon_index]
    )
    target_climatology = tp_climatology[target_month, lat_index, lon_index]
    matrix[:, len(FEATURES) + 2] = target_climatology
    matrix[:, len(FEATURES) + 3] = latitudes[lat_index]
    matrix[:, len(FEATURES) + 4] = longitudes[lon_index]
    angle = 2 * math.pi * (target_month + 1) / 12
    matrix[:, len(FEATURES) + 5] = np.sin(angle)
    matrix[:, len(FEATURES) + 6] = np.cos(angle)
    matrix[:, len(FEATURES) + 7] = lag / 24
    return matrix, lat_index, lon_index, target_month, target_climatology


def _build_sample(
    data_dir: Path,
    count: int,
    target: np.ndarray,
    origin: np.ndarray,
    lag: np.ndarray,
    point: np.ndarray,
    climatology_end: int,
) -> tuple[np.ndarray, np.ndarray]:
    tp, times = _load_variable(data_dir, "tp")
    with xr.open_dataset(data_dir / "treino_tp.nc") as dataset:
        latitudes = dataset.lat.values.astype(np.float32)
        longitudes = dataset.lon.values.astype(np.float32)
    tp_climatology = _monthly_climatology(tp, times, climatology_end)
    matrix, lat_index, lon_index, target_month, target_climatology = _base_features(
        count,
        target,
        origin,
        lag,
        point,
        times,
        latitudes,
        longitudes,
        tp,
        tp_climatology,
    )
    feature_index = _atmospheric_feature_index(target)
    for column, name in enumerate(FEATURES):
        values, feature_times = _load_variable(data_dir, name)
        if not np.array_equal(feature_times, times):
            raise ValueError(f"Eixo temporal incompatível em {name}.")
        climatology = _monthly_climatology(values, times, climatology_end)
        feature_month = (times[feature_index].astype(int) % 12).astype(np.int16)
        matrix[:, column] = (
            values[feature_index, lat_index, lon_index]
            - climatology[feature_month, lat_index, lon_index]
        )
        del values, climatology
    target_values = tp[target, lat_index, lon_index]
    residual = target_values - target_climatology
    if not np.isfinite(matrix).all() or not np.isfinite(residual).all():
        raise ValueError("A amostra contém NaN ou infinito.")
    return matrix, residual.astype(np.float32)


def _validation_coordinates(times: np.ndarray) -> tuple[np.ndarray, ...]:
    blocks = (("2018-12", "2019-01", "2020-12"), ("2020-12", "2021-01", "2022-12"))
    targets: list[np.ndarray] = []
    origins: list[np.ndarray] = []
    lags: list[np.ndarray] = []
    points: list[np.ndarray] = []
    for origin_date, start, end in blocks:
        origin_index = int(np.where(times == np.datetime64(origin_date))[0][0])
        target_indexes = np.where((times >= np.datetime64(start)) & (times <= np.datetime64(end)))[
            0
        ]
        for lag_value, target_index in enumerate(target_indexes, start=1):
            targets.append(np.full(GRID_POINTS, target_index, dtype=np.int32))
            origins.append(np.full(GRID_POINTS, origin_index, dtype=np.int32))
            lags.append(np.full(GRID_POINTS, lag_value, dtype=np.int16))
            points.append(np.arange(GRID_POINTS, dtype=np.int32))
    return tuple(np.concatenate(values) for values in (targets, origins, lags, points))


def _predict_validation(
    model: XGBRegressor,
    data_dir: Path,
    climatology_end: int,
    chunk_size: int = 200_000,
    spatial_stride: int = 1,
) -> dict:
    tp, times = _load_variable(data_dir, "tp")
    target, origin, lag, point = _validation_coordinates(times)
    if spatial_stride > 1:
        keep = point % spatial_stride == 0
        target, origin, lag, point = (values[keep] for values in (target, origin, lag, point))
    with xr.open_dataset(data_dir / "treino_tp.nc") as dataset:
        latitudes = dataset.lat.values.astype(np.float32)
        longitudes = dataset.lon.values.astype(np.float32)
    tp_climatology = _monthly_climatology(tp, times, climatology_end)
    matrix, lat_index, lon_index, target_month, baseline = _base_features(
        len(target),
        target,
        origin,
        lag,
        point,
        times,
        latitudes,
        longitudes,
        tp,
        tp_climatology,
    )
    feature_index = _atmospheric_feature_index(target)
    feature_month = (times[feature_index].astype(int) % 12).astype(np.int16)
    for column, name in enumerate(FEATURES):
        values, feature_times = _load_variable(data_dir, name)
        if not np.array_equal(feature_times, times):
            raise ValueError(f"Eixo temporal incompatível em {name}.")
        climatology = _monthly_climatology(values, times, climatology_end)
        matrix[:, column] = (
            values[feature_index, lat_index, lon_index]
            - climatology[feature_month, lat_index, lon_index]
        )
        del values, climatology
    truth = tp[target, lat_index, lon_index]
    if not np.isfinite(matrix).all() or not np.isfinite(truth).all():
        raise ValueError("A validação contém NaN ou infinito.")
    squared_error = 0.0
    baseline_squared_error = 0.0
    observations = 0
    for start in range(0, len(target), chunk_size):
        stop = min(start + chunk_size, len(target))
        prediction_residual = model.predict(matrix[start:stop])
        prediction = np.clip(baseline[start:stop] + prediction_residual, 0, None)
        residual = truth[start:stop] - baseline[start:stop]
        squared_error += float(np.square(truth[start:stop] - prediction).sum(dtype=np.float64))
        baseline_squared_error += float(np.square(residual).sum(dtype=np.float64))
        observations += stop - start
    return {
        "period": "2019-01/2022-12 em dois blocos operacionais de 24 meses",
        "observations": observations,
        "spatial_stride": spatial_stride,
        "candidate_rmse": math.sqrt(squared_error / observations),
        "climatology_rmse": math.sqrt(baseline_squared_error / observations),
    }


def _test_features(
    data_dir: Path,
    climatology_end: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tp, times = _load_variable(data_dir, "tp")
    with (
        xr.open_dataset(data_dir / "treino_tp.nc") as train,
        xr.open_dataset(data_dir / "teste_features.nc") as test,
    ):
        if np.isfinite(test.tp_alvo.values).any():
            raise ValueError("tp_alvo do teste contém valores; possível acesso ao alvo.")
        targets = test.time.values.astype("datetime64[M]")
        origins = test.time_origem.values.astype("datetime64[M]")
        if not np.array_equal(origins + np.timedelta64(1, "M"), targets):
            raise ValueError("time_origem não corresponde a T−1.")
        latitudes = train.lat.values.astype(np.float32)
        longitudes = train.lon.values.astype(np.float32)
        tp_climatology = _monthly_climatology(tp, times, climatology_end)
        matrix = np.empty((EXPECTED_ROWS, len(FEATURE_NAMES)), dtype=np.float32)
        baseline_values = np.empty(EXPECTED_ROWS, dtype=np.float32)
        lat_grid, lon_grid = np.meshgrid(latitudes, longitudes, indexing="ij")
        for column, name in enumerate(FEATURES):
            train_values, feature_times = _load_variable(data_dir, name)
            if not np.array_equal(feature_times, times):
                raise ValueError(f"Eixo temporal incompatível em {name}.")
            feature_climatology = _monthly_climatology(train_values, times, climatology_end)
            for target_index, origin_date in enumerate(origins):
                start = target_index * GRID_POINTS
                stop = start + GRID_POINTS
                origin_month = int(origin_date.astype(int) % 12)
                matrix[start:stop, column] = (
                    test[name].isel(time=target_index).values - feature_climatology[origin_month]
                ).reshape(-1)
            del train_values, feature_climatology
        for target_index, target_date in enumerate(targets):
            start = target_index * GRID_POINTS
            stop = start + GRID_POINTS
            target_month = int(target_date.astype(int) % 12)
            origin_month = int(origins[target_index].astype(int) % 12)
            baseline = tp_climatology[target_month]
            tp_origin = test.tp_ultima_obs.isel(time=target_index).values.astype(np.float32)
            matrix[start:stop, len(FEATURES)] = tp_origin.reshape(-1)
            matrix[start:stop, len(FEATURES) + 1] = (
                tp_origin - tp_climatology[origin_month]
            ).reshape(-1)
            matrix[start:stop, len(FEATURES) + 2] = baseline.reshape(-1)
            matrix[start:stop, len(FEATURES) + 3] = lat_grid.reshape(-1)
            matrix[start:stop, len(FEATURES) + 4] = lon_grid.reshape(-1)
            angle = 2 * math.pi * (target_month + 1) / 12
            matrix[start:stop, len(FEATURES) + 5] = math.sin(angle)
            matrix[start:stop, len(FEATURES) + 6] = math.cos(angle)
            matrix[start:stop, len(FEATURES) + 7] = float(test.lag_meses.values[target_index]) / 24
            baseline_values[start:stop] = baseline.reshape(-1)
    if not np.isfinite(matrix).all() or not np.isfinite(baseline_values).all():
        raise ValueError("As features de teste contêm NaN ou infinito.")
    return matrix, baseline_values, targets


def _export_submission(
    model: XGBRegressor,
    data_dir: Path,
    climatology_end: int,
    output_path: Path,
    gzip_path: Path,
) -> dict:
    matrix, baseline, _ = _test_features(data_dir, climatology_end)
    prediction = np.clip(baseline + model.predict(matrix), 0, None)
    sample_path = data_dir / "sample_submission.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with (
        sample_path.open(encoding="utf-8-sig", newline="") as source,
        output_path.open("w", encoding="utf-8", newline="") as destination,
    ):
        reader = csv.reader(source)
        writer = csv.writer(destination, lineterminator="\n")
        if next(reader) != ["id", "tp_mm_day"]:
            raise ValueError("Cabeçalho oficial inesperado.")
        writer.writerow(["id", "tp_mm_day"])
        for value, row in zip(prediction, reader, strict=True):
            writer.writerow([row[0], f"{float(value):.6f}"])
            rows += 1
    if rows != EXPECTED_ROWS:
        raise ValueError(f"Quantidade de linhas inválida: {rows}.")
    with output_path.open("rb") as source, gzip_path.open("wb") as target_file:
        with gzip.GzipFile(fileobj=target_file, mode="wb", compresslevel=9, mtime=0) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    return {
        "rows": rows,
        "columns": ["id", "tp_mm_day"],
        "csv_sha256": _sha256(output_path),
        "gzip_sha256": _sha256(gzip_path),
    }


def run(
    data_dir: Path,
    artifacts_dir: Path,
    samples: int,
    estimators: int,
    seed: int,
    validation_stride: int = 1,
    export_submission: bool = True,
) -> dict:
    tp, times = _load_variable(data_dir, "tp")
    train_end = int(np.where(times == np.datetime64("2018-12"))[0][0])
    rng = np.random.default_rng(seed)
    target, origin, lag, point = _sample_coordinates(rng, samples, 24, train_end)
    matrix, residual = _build_sample(data_dir, samples, target, origin, lag, point, train_end)
    model = XGBRegressor(
        n_estimators=estimators,
        max_depth=8,
        learning_rate=0.035,
        min_child_weight=20,
        subsample=0.85,
        colsample_bytree=0.9,
        reg_alpha=0.05,
        reg_lambda=2.0,
        objective="reg:squarederror",
        eval_metric="rmse",
        tree_method="hist",
        n_jobs=-1,
        random_state=seed,
    )
    model.fit(matrix, residual, verbose=False)
    validation = _predict_validation(model, data_dir, train_end, spatial_stride=validation_stride)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "xgboost-anomaly-v1.joblib"
    joblib.dump({"model": model, "feature_names": FEATURE_NAMES}, model_path, compress=3)
    promoted = validation["candidate_rmse"] < validation["climatology_rmse"]
    submission = None
    if promoted and export_submission:
        submission = _export_submission(
            model,
            data_dir,
            int(np.where(times == np.datetime64("2022-12"))[0][0]),
            artifacts_dir / "submission-xgboost-anomaly-v1.csv",
            artifacts_dir / "submission-xgboost-anomaly-v1.csv.gz",
        )
    report = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_id": "xgboost-anomaly-v1",
        "status": "validated_candidate" if promoted else "rejected_candidate",
        "temporal_contract": "atmosfera T−1 + tp congelada na origem → precipitação T",
        "training_period": "1940-01/2018-12",
        "training_samples": samples,
        "seed": seed,
        "features": FEATURE_NAMES,
        "validation": validation,
        "submission": submission,
        "official_score": None,
        "submission_export_requested": export_submission,
        "target_period_read": False,
        "source_repository_modified": False,
    }
    (artifacts_dir / "xgboost-anomaly-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--samples", type=int, default=400_000)
    parser.add_argument("--estimators", type=int, default=450)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-stride", type=int, default=1)
    parser.add_argument("--no-export", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.data_dir,
                args.artifacts_dir,
                args.samples,
                args.estimators,
                args.seed,
                validation_stride=args.validation_stride,
                export_submission=not args.no_export,
            ),
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
