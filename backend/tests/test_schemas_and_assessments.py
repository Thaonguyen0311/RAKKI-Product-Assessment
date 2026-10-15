import pytest
from pydantic import ValidationError
from app.schemas.product import ProductIn, MaterialIn
from app.services.assessment import carbon_assessment, rapu_assessment

def test_material_percentage_total_rejected():
    with pytest.raises(ValidationError):
        ProductIn(name='Jacket', materials=[MaterialIn(name='Cotton',percentage=70),MaterialIn(name='Wool',percentage=40)])

def test_unknown_percentages_are_allowed():
    assert ProductIn(name='Jacket',materials=[MaterialIn(name='Unknown')]).materials[0].percentage is None

def test_assessments_do_not_invent_methodology():
    product=object()
    assert carbon_assessment(product)['status']=='insufficient_data'
    assert rapu_assessment(product)['status']=='awaiting_methodology'
