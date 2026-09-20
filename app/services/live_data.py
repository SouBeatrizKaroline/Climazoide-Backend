import asyncio
import logging
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import httpx

LOCATIONS = {
    "buenos-aires": {
        "name": "Buenos Aires", "country": "Argentina", "code": "AR",
        "latitude": -34.6037, "longitude": -58.3816,
    },
    "la-paz": {
        "name": "La Paz", "country": "Bolívia", "code": "BO",
        "latitude": -16.4897, "longitude": -68.1193,
    },
    "brasilia": {
        "name": "Brasília", "country": "Brasil", "code": "BR", "state": "DF",
        "latitude": -15.7939, "longitude": -47.8828,
    },
    "santiago": {
        "name": "Santiago", "country": "Chile", "code": "CL",
        "latitude": -33.4489, "longitude": -70.6693,
    },
    "bogota": {
        "name": "Bogotá", "country": "Colômbia", "code": "CO",
        "latitude": 4.7110, "longitude": -74.0721,
    },
    "quito": {
        "name": "Quito", "country": "Equador", "code": "EC",
        "latitude": -0.1807, "longitude": -78.4678,
    },
    "georgetown": {
        "name": "Georgetown", "country": "Guiana", "code": "GY",
        "latitude": 6.8013, "longitude": -58.1551,
    },
    "asuncion": {
        "name": "Assunção", "country": "Paraguai", "code": "PY",
        "latitude": -25.2637, "longitude": -57.5759,
    },
    "lima": {
        "name": "Lima", "country": "Peru", "code": "PE",
        "latitude": -12.0464, "longitude": -77.0428,
    },
    "paramaribo": {
        "name": "Paramaribo", "country": "Suriname", "code": "SR",
        "latitude": 5.8520, "longitude": -55.2038,
    },
    "montevideu": {
        "name": "Montevidéu", "country": "Uruguai", "code": "UY",
        "latitude": -34.9011, "longitude": -56.1645,
    },
    "caracas": {
        "name": "Caracas", "country": "Venezuela", "code": "VE",
        "latitude": 10.4806, "longitude": -66.9036,
    },
    "caiena": {
        "name": "Caiena", "country": "Guiana Francesa", "code": "GF",
        "latitude": 4.9224, "longitude": -52.3135,
    },
}

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
CPTEC_URL = "https://servicos.cptec.inpe.br/XML/cidade/7dias/{lat}/{lon}/previsaoLatLon.xml"
NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
USNO_URL = "https://aa.usno.navy.mil/api/rstt/oneday"
MET_NO_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
logger = logging.getLogger(__name__)
_MET_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}


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
    """Fetch a public JSON source with a short retry for transient network failures."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(0.4 * (attempt + 1))
    raise httpx.HTTPError(f"Fonte indisponível após 3 tentativas: {url}") from last_error


async def _fetch_met_no(client: httpx.AsyncClient, latitude: float, longitude: float) -> dict:
    key = (latitude, longitude)
    cached = _MET_CACHE.get(key)
    now = datetime.now(UTC)
    if cached and cached[0] > now.timestamp():
        return cached[1]
    response = await client.get(
        MET_NO_URL,
        params={"lat": latitude, "lon": longitude},
        headers={"User-Agent": "Climazoide/0.3 (https://github.com/SouBeatrizKaroline/Climazoide-Backend)"},
    )
    response.raise_for_status()
    payload = response.json()
    cache_control = response.headers.get("cache-control", "")
    try:
        max_age = next(
            (int(part.split("=", 1)[1]) for part in cache_control.split(",")
             if part.strip().startswith("max-age=")),
            None,
        )
    except ValueError:
        max_age = None
    expires = now.timestamp() + max_age if max_age is not None else None
    expires_header = response.headers.get("expires")
    if expires is None and expires_header:
        try:
            expires = parsedate_to_datetime(expires_header).timestamp()
        except (TypeError, ValueError, OverflowError):
            expires = None
    # If the provider omits cache headers, avoid frequent repeat requests.
    ttl = max(0, expires - now.timestamp()) if expires is not None else 60
    _MET_CACHE[key] = (now.timestamp() + ttl, payload)
    return payload


def _met_no_weather(payload: dict, timezone: str) -> dict:
    """Normalize MET Norway's timestamped forecast; omit unavailable quantities."""
    properties = payload.get("properties", {})
    series = properties.get("timeseries", [])
    if not series:
        return {}
    current_entry = series[0]
    current_data = current_entry.get("data", {})
    current_details = current_data.get("instant", {}).get("details", {})
    symbol = (
        current_data.get("next_1_hours", {}).get("summary", {}).get("symbol_code")
        or current_data.get("next_6_hours", {}).get("summary", {}).get("symbol_code")
        or ""
    )
    condition = _met_no_condition(symbol)
    current = {
        "time": current_entry.get("time"),
        "temperature_2m": current_details.get("air_temperature"),
        "apparent_temperature": None,
        "relative_humidity_2m": current_details.get("relative_humidity"),
        "weather_code": None,
        "condition": condition,
        "cloud_cover": current_details.get("cloud_area_fraction"),
        "surface_pressure": None,
        "wind_speed_10m": (
            round(current_details["wind_speed"] * 3.6, 1)
            if current_details.get("wind_speed") is not None else None
        ),
        "wind_direction_10m": current_details.get("wind_from_direction"),
        "wind_gusts_10m": (
            round(current_details["wind_speed_of_gust"] * 3.6, 1)
            if current_details.get("wind_speed_of_gust") is not None else None
        ),
    }
    # MET Norway's symbols are descriptive but are not WMO codes. Do not
    # translate them into a different code system or pretend they are equivalent.
    grouped: dict[str, list[dict]] = {}
    for entry in series:
        local_date = entry.get("time", "")[:10]
        if not local_date:
            continue
        data = entry.get("data", {})
        details = data.get("instant", {}).get("details", {})
        next_data = data.get("next_1_hours") or data.get("next_6_hours") or {}
        precip = next_data.get("details", {}).get("precipitation_amount")
        day = grouped.setdefault(local_date, {"time": local_date, "temps": [], "precip": []})
        temperature = details.get("air_temperature")
        if temperature is not None:
            day["temps"].append(temperature)
        if precip is not None:
            day["precip"].append(precip)
    daily = [
        {
            "time": date,
            "weather_code": None,
            "temperature_2m_max": max(item["temps"]) if item["temps"] else None,
            "temperature_2m_min": min(item["temps"]) if item["temps"] else None,
            "precipitation_sum": round(sum(item["precip"]), 1) if item["precip"] else None,
            "precipitation_probability_max": None,
            "uv_index_max": None,
            "et0_fao_evapotranspiration": None,
        }
        for date, item in sorted(grouped.items())[:7]
    ]
    return {
        "timezone": timezone,
        "current": current,
        "hourly": {"time": [], "soil_moisture_0_to_1cm": [], "vapour_pressure_deficit": []},
        "daily": {key: [day[key] for day in daily] for key in daily[0]} if daily else {},
        "provider": "MET Norway",
        "model_updated_at": properties.get("meta", {}).get("updated_at"),
        "valid_from": series[0].get("time"),
        "valid_until": series[-1].get("time"),
    }


def _met_no_condition(symbol: str) -> str | None:
    key = symbol.split("_")[0].lower()
    if key.startswith("clearsky"):
        return "Céu limpo"
    if key.startswith("fair"):
        return "Predomínio de sol"
    if key.startswith("partlycloudy"):
        return "Parcialmente nublado"
    if key.startswith("cloudy"):
        return "Nublado"
    if key.startswith("fog"):
        return "Névoa"
    if "thunderstorm" in key:
        return "Trovoadas"
    if "sleet" in key:
        return "Chuva e neve"
    if "snow" in key:
        return "Neve"
    if "rain" in key:
        return "Chuva"
    return None


async def _fetch_cptec(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> dict:
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


async def _fetch_oni(client: httpx.AsyncClient) -> dict:
    response = await client.get(NOAA_ONI_URL)
    response.raise_for_status()
    values = response.text.strip().splitlines()[-1].split()
    anomaly = float(values[3])
    phase = "El Niño" if anomaly >= 0.5 else "La Niña" if anomaly <= -0.5 else "Neutro"
    return {
        "available": True,
        "season": values[0],
        "year": int(values[1]),
        "value": anomaly,
        "phase": phase,
    }


async def _fetch_astronomy(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> dict:
    response = await client.get(
        USNO_URL,
        params={"date": datetime.now(UTC).date().isoformat(), "coords": f"{latitude},{longitude}"},
    )
    response.raise_for_status()
    data = response.json()["properties"]["data"]
    events = {item["phen"]: item["time"] for item in data.get("sundata", [])}
    return {
        "available": True,
        "moon_phase": data.get("curphase"),
        "moon_illumination": data.get("fracillum"),
        "sunrise_utc": events.get("Rise"),
        "sunset_utc": events.get("Set"),
        "date": f"{data.get('year')}-{data.get('month'):02d}-{data.get('day'):02d}",
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
    client_timeout = httpx.Timeout(timeout, connect=min(timeout, 15.0))
    transport = httpx.AsyncHTTPTransport(retries=2)
    async with httpx.AsyncClient(
        timeout=client_timeout,
        transport=transport,
        follow_redirects=True,
        headers={"User-Agent": "Climazoide/0.3 (+https://github.com/SouBeatrizKaroline/Climazoide-Backend)"},
    ) as client:
        weather_task = _fetch_json(client, WEATHER_URL, weather_params)
        air_task = _fetch_json(client, AIR_URL, air_params)
        cptec_task = (
            _fetch_cptec(client, location["latitude"], location["longitude"])
            if location["code"] == "BR"
            else asyncio.sleep(
                0,
                result={
                    "available": False,
                    "applicable": False,
                    "provider": "CPTEC/INPE",
                    "forecast": [],
                },
            )
        )
        oni_task = _fetch_oni(client)
        astronomy_task = _fetch_astronomy(client, location["latitude"], location["longitude"])
        weather, air, cptec, oni, astronomy = await asyncio.gather(
            weather_task, air_task, cptec_task, oni_task, astronomy_task, return_exceptions=True
        )

        weather_provider = "Open-Meteo"
        weather_failure = None
        if isinstance(weather, Exception):
            weather_failure = f"{type(weather).__name__}: {weather}"
            logger.warning("Open-Meteo weather request failed: %s", weather_failure)
            try:
                weather = await _fetch_met_no(client, location["latitude"], location["longitude"])
                weather = _met_no_weather(weather, "UTC")
                weather_provider = "MET Norway"
            except Exception as fallback_error:
                logger.warning("MET Norway fallback failed: %s", fallback_error)
                weather = {}

    if isinstance(weather, Exception):
        weather = {}
    if isinstance(air, Exception):
        air = {}
    if isinstance(cptec, Exception):
        cptec = {"available": False, "provider": "CPTEC/INPE", "forecast": []}
    if isinstance(oni, Exception):
        oni = {"available": False}
    if isinstance(astronomy, Exception):
        astronomy = {"available": False}

    current = weather.get("current", {})
    hourly = weather.get("hourly", {})
    current_hour = str(current.get("time", ""))[:13] + ":00"
    try:
        hour_index = hourly.get("time", []).index(current_hour)
    except ValueError:
        hour_index = 0

    provider = weather.get("provider", weather_provider)
    daily_times = weather.get("daily", {}).get("time", [])
    valid_until = weather.get("valid_until") or (daily_times[-1] if daily_times else None)
    timezone = weather.get("timezone")
    if not timezone:
        timezone = "UTC" if provider == "MET Norway" else "Indisponível"
    return {
        "project": "Climazoide",
        "location_id": location_id,
        "location": location,
        "coverage": {
            "scientific_domain": "América do Sul · 60°S–15°N · 90°O–25°O",
            "grid_resolution": "0,25°",
            "grid_points_per_month": 78561,
            "operational_points": len(LOCATIONS),
            "note": "O ponto operacional não substitui a previsão científica em grade.",
        },
        "generated_at": datetime.now(UTC).isoformat(),
        "timezone": timezone,
        "weather_metadata": {
            "provider": provider,
            "model_updated_at": weather.get("model_updated_at"),
            "valid_from": weather.get("valid_from") or current.get("time"),
            "valid_until": valid_until,
            "fallback_used": provider != "Open-Meteo",
            "primary_source_error": weather_failure,
        },
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
            "soil_moisture": _hour_value(hourly, "soil_moisture_0_to_1cm", hour_index),
            "vapour_pressure_deficit": _hour_value(hourly, "vapour_pressure_deficit", hour_index),
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
        "climate_context": {"oni": oni},
        "astronomy": astronomy,
        "impacts": _impact_indicators(weather, air),
        "sources": [
            {
                "name": "Open-Meteo",
                "scope": "modelos meteorológicos internacionais",
                "available": bool(weather) and provider == "Open-Meteo",
                "updated_at": weather.get("model_updated_at") or current.get("time"),
                "note": weather_failure if weather_failure and provider != "Open-Meteo" else None,
                "url": "https://open-meteo.com/en/docs",
            },
            *([{
                "name": "MET Norway",
                "scope": "previsão meteorológica global de contingência",
                "available": bool(weather),
                "updated_at": weather.get("model_updated_at"),
                "valid_from": weather.get("valid_from"),
                "valid_until": weather.get("valid_until"),
                "url": "https://api.met.no/weatherapi/locationforecast/2.0/documentation",
            }] if provider == "MET Norway" else []),
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
                "applicable": cptec.get("applicable", True),
                "updated_at": cptec.get("updated_at"),
                "url": "https://servicos.cptec.inpe.br/XML/",
            },
            {
                "name": "NOAA CPC",
                "scope": "índice oceânico ONI e fase do ENSO",
                "available": oni["available"],
                "updated_at": f"{oni.get('season', '')} {oni.get('year', '')}".strip() or None,
                "url": NOAA_ONI_URL,
            },
            {
                "name": "US Naval Observatory",
                "scope": "fase lunar e eventos solares",
                "available": astronomy["available"],
                "updated_at": astronomy.get("date"),
                "url": "https://aa.usno.navy.mil/data/api",
            },
        ],
    }


def _impact_indicators(weather: dict, air: dict) -> list[dict]:
    daily = weather.get("daily", {})
    precipitation_values = daily.get("precipitation_sum", [])
    et0_values = daily.get("et0_fao_evapotranspiration", [])
    temperature_values = daily.get("temperature_2m_max", [])
    precipitation_available = [value for value in precipitation_values if value is not None]
    et0_available = [value for value in et0_values if value is not None]
    temperature_available = [value for value in temperature_values if value is not None]
    precipitation = (
        sum(precipitation_available)
        if precipitation_values and len(precipitation_available) == len(precipitation_values)
        else None
    )
    et0 = sum(et0_available) if et0_values and len(et0_available) == len(et0_values) else None
    max_temperature = (
        max(temperature_available)
        if temperature_values and len(temperature_available) == len(temperature_values)
        else None
    )
    aqi = _value(air, "current", "us_aqi")
    return [
        {
            "id": "water",
            "label": "Balanço hídrico em 7 dias",
            "value": (
                round(precipitation - et0, 1)
                if precipitation is not None and et0 is not None
                else None
            ),
            "unit": "mm",
            "detail": "Chuva prevista menos evapotranspiração de referência.",
        },
        {
            "id": "agriculture",
            "label": "Demanda evaporativa em 7 dias",
            "value": round(et0, 1) if et0 is not None else None,
            "unit": "mm",
            "detail": "Indicador útil para irrigação; não substitui manejo agronômico.",
        },
        {
            "id": "heat",
            "label": "Maior temperatura em 7 dias",
            "value": round(max_temperature, 1) if max_temperature is not None else None,
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


def _hour_value(hourly: dict, key: str, index: int):
    values = hourly.get(key) or []
    return values[index] if 0 <= index < len(values) else None
