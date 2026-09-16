import asyncio
from datetime import UTC, datetime
from xml.etree import ElementTree

import httpx

LOCATIONS = {
    "recife": {"name": "Recife", "state": "PE", "latitude": -8.0476, "longitude": -34.8770},
    "sao-paulo": {"name": "São Paulo", "state": "SP", "latitude": -23.5505, "longitude": -46.6333},
    "manaus": {"name": "Manaus", "state": "AM", "latitude": -3.1190, "longitude": -60.0217},
    "brasilia": {"name": "Brasília", "state": "DF", "latitude": -15.7939, "longitude": -47.8828},
    "porto-alegre": {
        "name": "Porto Alegre", "state": "RS", "latitude": -30.0346, "longitude": -51.2177
    },
}

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
CPTEC_URL = "https://servicos.cptec.inpe.br/XML/cidade/7dias/{lat}/{lon}/previsaoLatLon.xml"


def _value(payload: dict, group: str, key: str, default=None):
    return payload.get(group, {}).get(key, default)


def _daily(weather: dict) -> list[dict]:
    daily = weather.get("daily", {})
    keys = [
        "time", "weather_code", "temperature_2m_max", "temperature_2m_min",
        "precipitation_sum", "precipitation_probability_max", "uv_index_max",
        "et0_fao_evapotranspiration",
    ]
    length = len(daily.get("time", []))
    return [
        {key: daily.get(key, [None] * length)[index] for key in keys}
        for index in range(length)
    ]


async def _fetch_json(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    response = await client.get(url, params=params)
    response.raise_for_status()
    return response.json()


async def _fetch_cptec(client: httpx.AsyncClient, latitude: float, longitude: float) -> dict:
    url = CPTEC_URL.format(lat=latitude, lon=longitude)
    response = await client.get(url)
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    return {
        "available": True,
        "provider": "CPTEC/INPE",
        "location": root.findtext("nome"),
        "state": root.findtext("uf"),
        "updated_at": root.findtext("atualizacao"),
        "forecast": [
            {
                "date": node.findtext("dia"),
                "condition_code": node.findtext("tempo"),
                "temperature_max": float(node.findtext("maxima", "0")),
                "temperature_min": float(node.findtext("minima", "0")),
                "uv_index": float(node.findtext("iuv", "0")),
            }
            for node in root.findall("previsao")
        ],
    }


async def fetch_live_overview(location_id: str, timeout: float) -> dict:
    if location_id not in LOCATIONS:
        raise ValueError("Localidade não reconhecida.")
    location = LOCATIONS[location_id]
    coordinates = {"latitude": location["latitude"], "longitude": location["longitude"]}
    weather_params = {
        **coordinates,
        "timezone": "auto",
        "forecast_days": 7,
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "precipitation", "weather_code", "cloud_cover", "surface_pressure",
            "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
        ]),
        "hourly": "soil_moisture_0_to_1cm,vapour_pressure_deficit",
        "daily": ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "precipitation_probability_max", "uv_index_max",
            "et0_fao_evapotranspiration",
        ]),
    }
    air_params = {
        **coordinates,
        "timezone": "auto",
        "current": "us_aqi,pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,ozone,uv_index",
    }
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        weather_task = _fetch_json(client, WEATHER_URL, weather_params)
        air_task = _fetch_json(client, AIR_URL, air_params)
        cptec_task = _fetch_cptec(client, location["latitude"], location["longitude"])
        weather, air, cptec = await asyncio.gather(
            weather_task, air_task, cptec_task, return_exceptions=True
        )

    if isinstance(weather, Exception):
        raise httpx.HTTPError("A fonte meteorológica principal não respondeu.") from weather
    if isinstance(air, Exception):
        air = {}
    if isinstance(cptec, Exception):
        cptec = {"available": False, "provider": "CPTEC/INPE", "forecast": []}

    current = weather.get("current", {})
    hourly = weather.get("hourly", {})
    current_hour = str(current.get("time", ""))[:13] + ":00"
    try:
        hour_index = hourly.get("time", []).index(current_hour)
    except ValueError:
        hour_index = 0

    return {
        "project": "Climazoide",
        "location_id": location_id,
        "location": location,
        "generated_at": datetime.now(UTC).isoformat(),
        "timezone": weather.get("timezone"),
        "current": {
            "observed_at": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "cloud_cover": current.get("cloud_cover"),
            "surface_pressure": current.get("surface_pressure"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "wind_gusts": current.get("wind_gusts_10m"),
            "soil_moisture": (hourly.get("soil_moisture_0_to_1cm") or [None])[hour_index],
            "vapour_pressure_deficit": (
                hourly.get("vapour_pressure_deficit") or [None]
            )[hour_index],
        },
        "air_quality": {
            "observed_at": _value(air, "current", "time"),
            "us_aqi": _value(air, "current", "us_aqi"),
            "pm2_5": _value(air, "current", "pm2_5"),
            "pm10": _value(air, "current", "pm10"),
            "carbon_monoxide": _value(air, "current", "carbon_monoxide"),
            "nitrogen_dioxide": _value(air, "current", "nitrogen_dioxide"),
            "ozone": _value(air, "current", "ozone"),
            "uv_index": _value(air, "current", "uv_index"),
        },
        "daily": _daily(weather),
        "cptec": cptec,
        "impacts": _impact_indicators(weather, air),
        "sources": [
            {
                "name": "Open-Meteo",
                "scope": "modelos meteorológicos internacionais",
                "available": True,
                "updated_at": current.get("time"),
                "url": "https://open-meteo.com/en/docs",
            },
            {
                "name": "CAMS/Copernicus",
                "scope": "composição atmosférica e qualidade do ar",
                "available": bool(air),
                "updated_at": _value(air, "current", "time"),
                "url": "https://open-meteo.com/en/docs/air-quality-api",
            },
            {
                "name": "CPTEC/INPE",
                "scope": "previsão nacional independente",
                "available": cptec["available"],
                "updated_at": cptec.get("updated_at"),
                "url": "https://servicos.cptec.inpe.br/XML/",
            },
        ],
    }


def _impact_indicators(weather: dict, air: dict) -> list[dict]:
    daily = weather.get("daily", {})
    precipitation = sum(value or 0 for value in daily.get("precipitation_sum", []))
    et0 = sum(value or 0 for value in daily.get("et0_fao_evapotranspiration", []))
    max_temperature = max(daily.get("temperature_2m_max", [0]) or [0])
    aqi = _value(air, "current", "us_aqi")
    return [
        {
            "id": "water",
            "label": "Balanço hídrico em 7 dias",
            "value": round(precipitation - et0, 1),
            "unit": "mm",
            "detail": "Chuva prevista menos evapotranspiração de referência.",
        },
        {
            "id": "agriculture",
            "label": "Demanda evaporativa em 7 dias",
            "value": round(et0, 1),
            "unit": "mm",
            "detail": "Indicador útil para irrigação; não substitui manejo agronômico.",
        },
        {
            "id": "heat",
            "label": "Maior temperatura em 7 dias",
            "value": round(max_temperature, 1),
            "unit": "°C",
            "detail": "Sinal de atenção para conforto térmico e demanda de energia.",
        },
        {
            "id": "health",
            "label": "Qualidade do ar agora",
            "value": aqi,
            "unit": "AQI",
            "detail": "Índice dos EUA calculado pelo CAMS; maior significa pior.",
        },
    ]
