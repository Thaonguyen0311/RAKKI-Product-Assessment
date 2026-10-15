from app.api.routes import safe_cell

def test_formula_injection_prefixes_apostrophe():
    assert safe_cell('=HYPERLINK("x")').startswith("'")
    assert safe_cell('normal text')=='normal text'
