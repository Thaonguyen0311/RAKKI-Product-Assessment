import json
import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def material_records() -> tuple[dict, ...]:
    path = Path(__file__).resolve().parents[1] / 'data' / 'material_mapping.json'
    records = json.loads(path.read_text(encoding='utf-8'))
    return tuple(records)


def normalize_material_name(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip().casefold()


def normalize_for_similarity(value: str) -> str:
    value = unicodedata.normalize('NFKD', value).casefold()
    value = ''.join(character for character in value if not unicodedata.combining(character))
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


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
    if value is None or not value.strip():
        return None
    exact = resolve_material(value)
    if exact:
        return {**exact, 'match_score': 1.0}

    target = normalize_for_similarity(value)
    target_tokens = set(target.split())

    def similarity(record: dict) -> float:
        candidate = normalize_for_similarity(record['material'])
        candidate_tokens = set(candidate.split())
        sequence_score = SequenceMatcher(None, target, candidate).ratio()
        overlap_score = (2 * len(target_tokens & candidate_tokens) /
                         (len(target_tokens) + len(candidate_tokens))) if target_tokens or candidate_tokens else 0
        return max(sequence_score, overlap_score)

    best = max(material_records(), key=similarity)
    return {**best, 'match_score': similarity(best)}


def resolve_best_suggestion(candidates: list[dict], fallback_name: str | None = None,
                            fallback_confidence: float = 0) -> dict | None:
    valid = [candidate for candidate in candidates
             if isinstance(candidate.get('name'), str) and candidate['name'].strip()]
    if not valid and fallback_name and fallback_name.strip():
        valid = [{'name': fallback_name, 'confidence': fallback_confidence}]
    if not valid:
        return None

    # Gemini confidence is the primary ranking. Similarity only breaks equal-confidence ties.
    ranked = []
    for candidate in valid:
        mapping = resolve_suggestion(candidate['name'])
        if mapping:
            confidence = float(candidate.get('confidence', 0))
            ranked.append((confidence, mapping['match_score'], candidate['name'], mapping))
    if not ranked:
        return None
    confidence, match_score, candidate_name, mapping = max(ranked, key=lambda row: (row[0], row[1]))
    return {'mapping': mapping, 'suggested_name': candidate_name,
            'confidence': confidence, 'match_score': match_score,
            'candidate_count': len(valid)}
