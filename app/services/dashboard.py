from app.models import DashboardOptions

MONTHS = [f"{year}-{month:02d}" for year in (2023, 2024) for month in range(1, 13)]
REGIONS = ["america-do-sul", "amazonia", "nordeste", "centro-sul"]


def get_options() -> DashboardOptions:
    return DashboardOptions(
        months=MONTHS,
        regions=REGIONS,
        default_month="2024-12",
        default_region="america-do-sul",
    )
