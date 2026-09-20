from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from httpx import HTTPError

from app.config import get_settings
from app.models import CatalogItem, DashboardOptions, PowerMonthlyQuery
from app.services.catalog import CATALOG
from app.services.dashboard import get_options
from app.services.live_data import LOCATIONS, fetch_live_overview
from app.services.model_manifest import load_model_manifest
from app.services.nasa_power import fetch_monthly
from app.services.research_catalog import load_research_catalog
from app.services.submission_delivery import (
    EXAMPLE_CSV,
    PARTIAL_PATH,
    SUBMISSION_PATH,
    submission_status,
)

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.3.2",
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
    return {
        "status": "ok",
        "environment": settings.app_env,
        "api_version": "0.3.2",
        "model_contract_version": "1.3",
    }


@app.get("/v1/dashboard/summary", tags=["dashboard"], deprecated=True)
def dashboard_summary(
    target_month: str = Query(default="2024-12", pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    region: str = Query(default="america-do-sul"),
) -> None:
    del target_month, region
    raise HTTPException(
        status_code=503,
        detail=(
            "Inferência mensal indisponível até o retreino com alinhamento M→M+1 "
            "e a publicação de um artefato versionado."
        ),
    )


@app.get("/v1/dashboard/options", response_model=DashboardOptions, tags=["dashboard"])
def dashboard_options() -> DashboardOptions:
    return get_options()


@app.get("/v1/integrations/catalog", response_model=list[CatalogItem], tags=["integrations"])
def integrations_catalog() -> list[CatalogItem]:
    return CATALOG


@app.get("/v1/model/manifest", tags=["model"])
def model_manifest() -> dict:
    return load_model_manifest()


@app.get("/v1/research/branches", tags=["research"])
def research_branches() -> dict:
    """Expose the audited research branch map without coupling the API to its Git history."""
    return load_research_catalog()


@app.get("/v1/submission/status", tags=["submission"])
def get_submission_status() -> dict:
    return submission_status()


@app.get("/v1/submission/example.csv", tags=["submission"])
def download_submission_example() -> Response:
    return Response(
        EXAMPLE_CSV,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="submission-example-not-valid.csv"'},
    )


@app.get("/v1/submission/download", tags=["submission"])
def download_submission() -> FileResponse:
    if not submission_status()["ready"]:
        raise HTTPException(
            status_code=409,
            detail="A submissão validada ainda não foi gerada. Consulte /v1/submission/status.",
        )
    return FileResponse(SUBMISSION_PATH, media_type="text/csv", filename="submission.csv")


@app.get("/v1/submission/partial.csv", tags=["submission"])
def download_research_partial() -> FileResponse:
    if not submission_status()["partial_available"]:
        raise HTTPException(
            status_code=409,
            detail="Ainda não há previsões oficiais parciais validadas para baixar.",
        )
    return FileResponse(
        PARTIAL_PATH,
        media_type="text/csv",
        filename="submission-partial.csv",
    )


@app.get("/v1/live/locations", tags=["live"])
def live_locations() -> list[dict]:
    return [{"id": key, **value} for key, value in LOCATIONS.items()]


@app.get("/v1/live/overview", tags=["live"])
async def live_overview(location: str = Query(default="brasilia")) -> dict:
    try:
        return await fetch_live_overview(location, settings.http_timeout_seconds)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPError as exc:
        raise HTTPException(
            status_code=502, detail="As fontes meteorológicas não responderam."
        ) from exc


@app.post("/v1/integrations/nasa-power/monthly", tags=["integrations"])
async def nasa_power_monthly(query: PowerMonthlyQuery) -> dict:
    try:
        return await fetch_monthly(query, settings.http_timeout_seconds)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail="A fonte NASA POWER não respondeu.") from exc
