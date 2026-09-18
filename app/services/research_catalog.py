import json
from functools import lru_cache
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "research_catalog.json"


@lru_cache
def load_research_catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        return json.load(catalog_file)
