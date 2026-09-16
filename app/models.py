from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DataStatus = Literal["demo", "calculated", "unavailable"]


class Metric(BaseModel):
    label: str
    value: float | None
    unit: str = ""
    status: DataStatus


class ModelInfo(BaseModel):
    name: str
    status: DataStatus
    scope: str
    rmse: float | None = None


class PhysicalVariable(BaseModel):
    label: str
    value: str
    status: DataStatus


class SeriesPoint(BaseModel):
    month: str
    observed: float | None
    predicted: float


class DashboardSummary(BaseModel):
    project: str
    target_month: str
    precipitation: Metric
    oni: Metric
    model: ModelInfo
    metrics: list[Metric]
    physical_variables: list[PhysicalVariable]
    series: list[SeriesPoint]
    dataset_period: str
    updated_at: datetime


class CatalogItem(BaseModel):
    id: str
    institution: str
    region: Literal["national", "international"]
    role: str
    requirement: Literal["required", "extra"]
    access: str
    documentation_url: str
    enabled: bool = False


class PowerMonthlyQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    start: int = Field(ge=1981, le=2100)
    end: int = Field(ge=1981, le=2100)
    parameters: list[str] = Field(default=["PRECTOTCORR"], min_length=1, max_length=20)
