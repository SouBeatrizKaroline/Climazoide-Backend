"""Gera o catálogo compacto usado pela camada de apoio à decisão.

O arquivo de submissão oficial nunca é alterado. Este processo apenas cruza as
previsões já validadas com estatísticas históricas locais calculadas no treino.
"""

from __future__ import annotations

import calendar
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import xarray as xr

from app.services.live_data import LOCATIONS


def _classification(value: float, p33: float, p67: float) -> str:
    if value < p33:
        return "below_historical"
    if value > p67:
        return "above_historical"
    return "within_historical"


def _rainfall_regime(total: float) -> str:
    if total < 30:
        return "very_low"
    if total < 75:
        return "low"
    if total < 150:
        return "moderate"
    if total < 250:
        return "high"
    return "very_high"


def run(data_dir: Path, submission_path: Path, output_path: Path) -> dict:
    with xr.open_dataset(data_dir / "treino_tp.nc") as dataset:
        tp = dataset["tp"]
        latitudes = tp.lat.values
        longitudes = tp.lon.values
        points: dict[str, dict] = {}
        for location_id, location in LOCATIONS.items():
            lat_index = int(np.abs(latitudes - location["latitude"]).argmin())
            lon_index = int(np.abs(longitudes - location["longitude"]).argmin())
            local = tp.isel(lat=lat_index, lon=lon_index)
            monthly = {}
            for month in range(1, 13):
                values = local.where(local.time.dt.month == month, drop=True).values
                monthly[str(month)] = {
                    "mean_mm_day": round(float(np.mean(values)), 6),
                    "p33_mm_day": round(float(np.quantile(values, 0.33)), 6),
                    "p67_mm_day": round(float(np.quantile(values, 0.67)), 6),
                }
            points[location_id] = {
                "name": location["name"],
                "country": location["country"],
                "grid_latitude": float(latitudes[lat_index]),
                "grid_longitude": float(longitudes[lon_index]),
                "monthly_history": monthly,
                "predictions": {},
            }

    coordinate_index = {
        f"{point['grid_latitude']:.2f}_{point['grid_longitude']:.2f}": location_id
        for location_id, point in points.items()
    }
    with submission_path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["id", "tp_mm_day"]:
            raise ValueError("A submissão não possui o contrato oficial id,tp_mm_day.")
        for row in reader:
            month, latitude, longitude = row["id"].rsplit("_", 2)
            location_id = coordinate_index.get(f"{float(latitude):.2f}_{float(longitude):.2f}")
            if location_id is None:
                continue
            target_month = month.replace("_", "-")
            value = float(row["tp_mm_day"])
            month_number = int(target_month[5:7])
            history = points[location_id]["monthly_history"][str(month_number)]
            total = value * calendar.monthrange(int(target_month[:4]), month_number)[1]
            mean = history["mean_mm_day"]
            anomaly = None if mean == 0 else ((value - mean) / mean) * 100
            points[location_id]["predictions"][target_month] = {
                "predicted_mm_day": round(value, 6),
                "estimated_monthly_mm": round(total, 1),
                "historical_mean_mm_day": mean,
                "historical_p33_mm_day": history["p33_mm_day"],
                "historical_p67_mm_day": history["p67_mm_day"],
                "anomaly_percent": None if anomaly is None else round(anomaly, 1),
                "historical_class": _classification(
                    value, history["p33_mm_day"], history["p67_mm_day"]
                ),
                "rainfall_regime": _rainfall_regime(total),
            }

    for location_id, point in points.items():
        if len(point["predictions"]) != 24:
            raise ValueError(f"{location_id} não possui os 24 meses previstos.")

    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_id": "monthly-climatology-v1",
        "prediction_period": "2023-01/2024-12",
        "training_period": "1940-01/2022-12",
        "temporal_contract": "dados históricos até T−1 ou antes → previsão de T",
        "notice": "Cenários históricos da avaliação 2023–2024; não são previsão atual de 2026.",
        "locations": points,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


if __name__ == "__main__":
    run(
        Path("data"),
        Path("artifacts/submission.csv"),
        Path("artifacts/decision_support_catalog.json"),
    )
