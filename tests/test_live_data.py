import httpx

from app.services.live_data import (
    _fetch_json,
    _impact_indicators,
    _met_no_weather,
    _short_range_analysis,
)


async def test_public_json_source_retries_transient_status_errors() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(200, json={"status": "available"}, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload = await _fetch_json(client, "https://example.test/data", {})

    assert payload == {"status": "available"}
    assert attempts == 3


def test_missing_weather_does_not_turn_unavailable_values_into_zeros() -> None:
    impacts = _impact_indicators({}, {})

    assert all(item["value"] is None for item in impacts)


def test_short_range_analysis_correlates_only_received_daily_values() -> None:
    weather = {
        "daily": {
            "time": ["2026-09-20", "2026-09-21", "2026-09-22"],
            "weather_code": [0, 1, 2],
            "temperature_2m_max": [34, 32, 30],
            "temperature_2m_min": [20, 20, 20],
            "precipitation_sum": [0, 1, 2],
            "precipitation_probability_max": [10, 40, 80],
            "uv_index_max": [7, 6, 4],
            "et0_fao_evapotranspiration": [4, 3, 2],
        }
    }

    analysis = _short_range_analysis(weather)

    assert analysis["period_start"] == "2026-09-20"
    assert analysis["period_end"] == "2026-09-22"
    assert analysis["rain_temperature_correlation"]["value"] == -1
    assert "não causalidade" in analysis["rain_temperature_correlation"]["detail"]
    assert next(item for item in analysis["metrics"] if item["id"] == "rain_total")[
        "value"
    ] == 3


def test_met_norway_fallback_preserves_period_and_does_not_invent_wmo_or_soil_values() -> None:
    payload = {
        "properties": {
            "meta": {"updated_at": "2026-09-19T18:00:00Z"},
            "timeseries": [
                {
                    "time": "2026-09-19T18:00:00Z",
                    "data": {
                        "instant": {"details": {
                            "air_temperature": 21.5,
                            "relative_humidity": 60,
                            "wind_speed": 2,
                            "wind_speed_of_gust": 4,
                            "cloud_area_fraction": 30,
                        }},
                        "next_1_hours": {
                            "summary": {"symbol_code": "partlycloudy_day"},
                            "details": {"precipitation_amount": 0.4},
                        },
                    },
                },
                {
                    "time": "2026-09-19T19:00:00Z",
                    "data": {
                        "instant": {"details": {"air_temperature": 22}},
                        "next_1_hours": {"details": {"precipitation_amount": 0.2}},
                    },
                },
            ],
        }
    }

    result = _met_no_weather(payload, "UTC")

    assert result["provider"] == "MET Norway"
    assert result["model_updated_at"] == "2026-09-19T18:00:00Z"
    assert result["current"]["wind_speed_10m"] == 7.2
    assert result["current"]["weather_code"] is None
    assert result["current"]["condition"] == "Parcialmente nublado"
    assert result["current"]["apparent_temperature"] is None
    assert result["daily"]["precipitation_sum"] == [0.6]
    assert result["daily"]["precipitation_probability_max"] == [None]
    assert result["hourly"]["soil_moisture_0_to_1cm"] == []
