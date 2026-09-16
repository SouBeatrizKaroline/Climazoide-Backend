import httpx

from app.models import PowerMonthlyQuery

BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"


async def fetch_monthly(query: PowerMonthlyQuery, timeout: float) -> dict:
    if query.end < query.start:
        raise ValueError("O ano final deve ser maior ou igual ao ano inicial.")

    params = {
        "parameters": ",".join(query.parameters),
        "community": "AG",
        "longitude": query.longitude,
        "latitude": query.latitude,
        "format": "JSON",
        "start": query.start,
        "end": query.end,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
