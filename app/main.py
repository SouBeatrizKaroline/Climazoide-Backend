from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from httpx import HTTPError

from app.config import get_settings
from app.models import CatalogItem, DashboardOptions, DashboardSummary, PowerMonthlyQuery
from app.services.catalog import CATALOG
from app.services.dashboard import get_demo_summary, get_options
from app.services.model_manifest import load_model_manifest
from app.services.nasa_power import fetch_monthly

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Camada de integração e entrega de dados do Climazoide.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/v1/dashboard/summary", response_model=DashboardSummary, tags=["dashboard"])
def dashboard_summary(
    target_month: str = Query(default="2024-12", pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    region: str = Query(default="america-do-sul"),
) -> DashboardSummary:
    try:
        return get_demo_summary(target_month=target_month, region=region)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/dashboard/options", response_model=DashboardOptions, tags=["dashboard"])
def dashboard_options() -> DashboardOptions:
    return get_options()


@app.get("/v1/integrations/catalog", response_model=list[CatalogItem], tags=["integrations"])
def integrations_catalog() -> list[CatalogItem]:
    return CATALOG


@app.get("/v1/model/manifest", tags=["model"])
def model_manifest() -> dict:
    return load_model_manifest()


@app.post("/v1/integrations/nasa-power/monthly", tags=["integrations"])
async def nasa_power_monthly(query: PowerMonthlyQuery) -> dict:
    try:
        return await fetch_monthly(query, settings.http_timeout_seconds)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail="A fonte NASA POWER não respondeu.") from exc
