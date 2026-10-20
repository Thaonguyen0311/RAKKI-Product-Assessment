import json
import re
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def material_records() -> tuple[dict, ...]:
    path = Path(__file__).resolve().parents[1] / 'data' / 'material_mapping.json'
    records = json.loads(path.read_text(encoding='utf-8'))
    return tuple(records)


def normalize_material_name(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip().casefold()


def resolve_material(value: str | None) -> dict | None:
    if value is None or not value.strip():
        return None
    normalized = normalize_material_name(value)
    matches = [record for record in material_records()
               if normalize_material_name(record['material']) == normalized]
    return matches[0] if len(matches) == 1 else None


def validated_material(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    record = resolve_material(value)
    if record is None:
        raise ValueError('Select a material from the canonical material list')
    return record['material']


def resolve_suggestion(value: str | None) -> dict | None:
    return resolve_material(value)
