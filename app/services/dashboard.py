from datetime import UTC, datetime

from app.models import DashboardSummary


def get_demo_summary() -> DashboardSummary:
    """Fallback honesto até o pipeline publicar um artefato de inferência versionado."""
    return DashboardSummary.model_validate(
        {
            "project": "Climazoide",
            "target_month": "Janeiro de 2025",
            "precipitation": {
                "label": "Precipitação prevista", "value": 4.27, "unit": "mm/dia", "status": "demo"
            },
            "oni": {"label": "Índice ONI", "value": -0.4, "unit": "°C", "status": "demo"},
            "model": {
                "name": "PCA/EOF + LSTM",
                "status": "demo",
                "scope": "América do Sul · grade 0,25°",
                "rmse": None,
            },
            "metrics": [
                {"label": "Skill Score", "value": None, "unit": "%", "status": "unavailable"},
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
            "series": [
                {"month": "Ago", "observed": 2.8, "predicted": 3.0},
                {"month": "Set", "observed": 3.2, "predicted": 3.1},
                {"month": "Out", "observed": 3.9, "predicted": 3.7},
                {"month": "Nov", "observed": 4.1, "predicted": 4.0},
                {"month": "Dez", "observed": 4.4, "predicted": 4.3},
                {"month": "Jan", "observed": None, "predicted": 4.27},
            ],
            "dataset_period": "ERA5 · treino 1940–2022 · avaliação 2023–2024",
            "updated_at": datetime.now(UTC),
        }
    )
