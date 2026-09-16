from datetime import UTC, date, datetime
from math import cos

from app.models import DashboardOptions, DashboardSummary
from app.services.model_manifest import load_model_manifest

MONTHS = [f"{year}-{month:02d}" for year in (2023, 2024) for month in range(1, 13)]
REGIONS = {
    "america-do-sul": "América do Sul",
    "amazonia": "Amazônia",
    "nordeste": "Nordeste",
    "centro-sul": "Centro-Sul",
}
MONTH_NAMES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)


def get_options() -> DashboardOptions:
    return DashboardOptions(
        months=MONTHS,
        regions=list(REGIONS),
        default_month="2024-12",
        default_region="america-do-sul",
    )


def _previous_month(value: str) -> str:
    current = date.fromisoformat(f"{value}-01")
    if current.month == 1:
        return f"{current.year - 1}-12"
    return f"{current.year}-{current.month - 1:02d}"


def _demo_precipitation(target_month: str, region: str) -> float:
    """Valor determinístico de interface; não representa saída do modelo científico."""
    month = int(target_month[-2:])
    region_offset = list(REGIONS).index(region) * 0.31
    seasonal = 1.25 * cos((month - 1) / 12 * 6.28318)
    return round(max(0.2, 3.4 + seasonal + region_offset), 2)


def get_demo_summary(
    target_month: str = "2024-12", region: str = "america-do-sul"
) -> DashboardSummary:
    """Fallback honesto até o pipeline publicar um artefato de inferência versionado."""
    if target_month not in MONTHS:
        raise ValueError("Mês fora do período de avaliação: use 2023-01 a 2024-12.")
    if region not in REGIONS:
        raise ValueError("Região não reconhecida.")

    year, month = (int(part) for part in target_month.split("-"))
    predicted = _demo_precipitation(target_month, region)
    manifest = load_model_manifest()
    model_metrics = manifest["metrics"]
    series = []
    for offset in range(5, -1, -1):
        index = (year * 12 + month - 1) - offset
        point_year, point_month_zero = divmod(index, 12)
        point_month = point_month_zero + 1
        point_key = f"{point_year}-{point_month:02d}"
        value = _demo_precipitation(point_key, region)
        series.append(
            {
                "month": MONTH_NAMES[point_month - 1][:3],
                "observed": None if point_key == target_month else round(value * 0.96, 2),
                "predicted": value,
            }
        )

    return DashboardSummary.model_validate(
        {
            "project": "Climazoide",
            "target_month": f"{MONTH_NAMES[month - 1]} de {year}",
            "precipitation": {
                "label": "Precipitação prevista",
                "value": predicted,
                "unit": "mm/dia",
                "status": "demo",
            },
            "oni": {"label": "Índice ONI", "value": -0.4, "unit": "°C", "status": "demo"},
            "model": {
                "name": "PCA/EOF + LSTM",
                "status": "calculated",
                "scope": f"{REGIONS[region]} · grade 0,25°",
                "rmse": model_metrics["model"]["rmse"],
            },
            "metrics": [
                {
                    "label": "Skill vs. climatologia",
                    "value": round(model_metrics["skill_score_vs_climatology"] * 100, 2),
                    "unit": "%",
                    "status": "calculated",
                },
                {"label": "R²", "value": None, "unit": "", "status": "unavailable"},
                {"label": "Erro < 1 mm/dia", "value": None, "unit": "%", "status": "unavailable"},
                {"label": "Erro < 2 mm/dia", "value": None, "unit": "%", "status": "unavailable"},
            ],
            "physical_variables": [
                {"label": "SST Atlântico", "value": "Aguardando fonte", "status": "unavailable"},
                {
                    "label": "Rios voadores · 850 hPa",
                    "value": "Aguardando fonte",
                    "status": "unavailable",
                },
                {"label": "Umidade do solo", "value": "Aguardando fonte", "status": "unavailable"},
            ],
            "series": series,
            "dataset_period": "ERA5 · treino 1940–2022 · avaliação 2023–2024",
            "updated_at": datetime.now(UTC),
            "region": region,
            "context": {
                "origin_month": _previous_month(target_month),
                "target_month": target_month,
                "horizon_months": 1,
                "grid_resolution": "0,25° · 301 × 261",
                "grid_points": 78561,
                "evaluation_metric": "RMSE global em mm/dia",
                "submission_rows": 1885464,
            },
        }
    )
