def carbon_assessment(product):
    return {'kind':'carbon','status':'insufficient_data','result':None,'unit':'kg CO2e/product','methodology':None,'details':{'reason':'No documented lifecycle method and complete bill of materials/emission factors are configured.'}}

def rapu_assessment(product):
    return {'kind':'rapu','status':'awaiting_methodology','result':None,'unit':None,'methodology':None,'details':{'reason':'An authoritative RAPU formula has not been provided.'}}
