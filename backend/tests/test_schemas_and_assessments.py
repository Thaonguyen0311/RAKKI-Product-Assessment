import pytest
from pydantic import ValidationError
from app.schemas.product import ProductIn, MaterialIn
from app.services.assessment import carbon_assessment, rapu_assessment
from app.services.materials import resolve_best_suggestion

def test_material_percentage_total_rejected():
    with pytest.raises(ValidationError):
        ProductIn(name='Jacket', materials=[MaterialIn(name='Cotton',percentage=70),MaterialIn(name='Wool',percentage=40)])

def test_unknown_percentages_are_allowed():
    assert ProductIn(name='Jacket',materials=[MaterialIn(name='Unknown')]).materials[0].percentage is None

def test_assessments_do_not_invent_methodology():
    product=object()
    assert carbon_assessment(product)['status']=='insufficient_data'
    assert rapu_assessment(product)['status']=='awaiting_methodology'

def test_best_confidence_candidate_uses_nearest_canonical_mapping():
    result = resolve_best_suggestion([
        {'name': 'Crushed concrete aggregate', 'confidence': 0.91},
        {'name': 'Fly ash', 'confidence': 0.84},
    ])
    assert result['mapping']['material'] == 'Crushed concrete'
    assert result['mapping']['material_id'] == 7000000187
    assert result['confidence'] == 0.91
    assert result['candidate_count'] == 2
