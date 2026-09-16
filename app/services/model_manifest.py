import json
from functools import lru_cache
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "model_manifest.json"


@lru_cache
def load_model_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)
