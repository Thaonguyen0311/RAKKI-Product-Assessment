PROCESS_OPTIONS = (
    ('Construction, residential building', '7000000642'), ('Earthwork, building site', '7000000645'),
    ('Stabilization', '7000000646'), ('Waste processing, wooden materials', '7000000653'),
    ('Waste processing, metal materials', '7000000654'), ('Waste disposal', '7000000655'),
    ('Transport, bulk carrier, medium, 14 000 DWT', '7000000823'), ('Transport, container ship, 1 000 TEU', '7000000822'),
    ('Transport, container train, diesel', '7000000820'),
    ('Transport, earth moving truck (32 t), load 40 % (80 % / 0 %), urban driving', '7000000971'),
    ('Transport, earth moving truck (32 t), load 40 % (80 % / 0 %), highway driving', '7000000972'),
    ('Transport, earth moving truck (32 t), load 50 % (100 % / 0 %), urban driving', '7000000711'),
    ('Transport, earth moving truck (32 t), load 50 % (100 % / 0 %), highway driving', '7000000710'),
    ('Transport, semitrailer truck (40 t), load 40 % (80 % / 0 %), urban driving', '7000000967'),
    ('Transport, semitrailer truck (40 t), load 40 % (80 % / 0 %), highway driving', '7000000968'),
    ('Transport, semitrailer truck (40 t), load 50 % (100 % / 0 %), urban driving', '7000000715'),
    ('Transport, semitrailer truck (40 t), load 50 % (100 % / 0 %), highway driving', '7000000714'),
    ('Transport, heavy delivery lorry (15 t), load 40 % (80 % / 0 %), urban driving', '7000000969'),
    ('Transport, heavy delivery lorry (15 t), load 40 % (80 % / 0 %), highway driving', '7000000970'),
    ('Transport, heavy delivery lorry (15 t), load 50 % (100 % / 0 %), urban driving', '7000000713'),
    ('Transport, heavy delivery lorry (15 t), load 50 % (100 % / 0 %), highway driving', '7000000712'),
    ('Transportation of building materials, building', '7000000980'), ('Waste processing, concrete materials', '7000000999'),
    ('Waste processing, bricks, gypsum and lime sand bricks', '7000001000'), ('Waste processing, glass', '7000001003'),
    ('Waste processing, plastics', '7000001004'), ('Waste processing, bitumen membrane', '7000001005'),
    ('Demolition, building', '7000001039'), ('Construction, other buildings', '7000001040'),
    ('Carbon handprint, steel, recycling', '7000001080'), ('Carbon handprint, aluminium, recycling', '7000001081'),
    ('Carbon handprint, copper, recycling', '7000001082'), ('Carbon handprint, bitumen membrane, recycling', '7000001083'),
    ('Carbon handprint, organic material, carbon storage', '7000001085'), ('Carbon handprint, concrete, carbonation', '7000001086'),
    ('Fossil diesel', '7000001093'), ('Fossil gasoline', '7000001094'), ('Biofuel, ethanol', '7000001095'),
    ('Biofuel, FAME', '7000001096'), ('Biofuel, HVO', '7000001097'), ('Gasoline', '7000001098'),
    ('Diesel', '7000001099'), ('Light fuel oil', '7000001100'), ('Light fuel oil, fossil', '7000001101'),
    ('Heavy fuel oil, HFO', '7000001102'), ('Demolition, building site', '7000001117'),
    ('Transportation of building materials, building site', '7000001118'), ('Others', 'Others'),
)
PROCESS_IDS = dict(PROCESS_OPTIONS)
def validated_process(value):
    if value is None or not value.strip(): return None
    if value not in PROCESS_IDS: raise ValueError('Select a process from the process list')
    return value
