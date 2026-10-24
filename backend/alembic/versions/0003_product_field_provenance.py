"""Track AI provenance and human verification for editable product fields.

Revision ID: 0003_product_field_provenance
Revises: 0002_primary_product_image
"""
import json

from alembic import op
import sqlalchemy as sa

revision = '0003_product_field_provenance'
down_revision = '0002_primary_product_image'
branch_labels = None
depends_on = None

PRODUCT_FIELDS = ('name', 'category', 'subtype', 'brand', 'sku', 'color', 'description', 'condition')


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column['name']: column for column in inspector.get_columns('products')}
    for name in ('field_provenance', 'field_verification'):
        if name not in columns:
            op.add_column('products', sa.Column(name, sa.JSON(), nullable=True))

    bind = op.get_bind()
    products_table = sa.Table('products', sa.MetaData(), autoload_with=bind)
    # A fresh database is created from the current SQLAlchemy models by 0001,
    # so it may not contain retired fields that older databases still have.
    product_columns = (
        'id',
        *(name for name in PRODUCT_FIELDS if name in columns),
        'field_provenance',
        'field_verification',
    )
    products = bind.execute(sa.select(*(products_table.c[name] for name in product_columns))).mappings().all()
    latest_extractions = {}
    for row in bind.execute(sa.text('SELECT product_id, payload FROM ai_extractions ORDER BY created_at, id')).mappings():
        payload = row['payload']
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        latest_extractions[row['product_id']] = payload if isinstance(payload, dict) else {}

    for product in products:
        provenance = product['field_provenance'] or {}
        verification = product['field_verification'] or {}
        if isinstance(provenance, str):
            provenance = json.loads(provenance)
        if isinstance(verification, str):
            verification = json.loads(verification)
        extraction = latest_extractions.get(product['id'], {})
        for field in PRODUCT_FIELDS:
            if field not in product:
                continue
            value = product[field]
            if field not in provenance and value is not None:
                provenance[field] = 'ai_inference' if extraction.get(field) == value else 'legacy'
            verification.setdefault(field, 'unverified')
        bind.execute(sa.text(
            'UPDATE products SET field_provenance = :provenance, field_verification = :verification WHERE id = :product_id'
        ), {'provenance': json.dumps(provenance), 'verification': json.dumps(verification), 'product_id': product['id']})

    for name in ('field_provenance', 'field_verification'):
        column = next(column for column in sa.inspect(bind).get_columns('products') if column['name'] == name)
        if column['nullable']:
            if bind.dialect.name == 'sqlite':
                with op.batch_alter_table('products') as batch:
                    batch.alter_column(name, existing_type=sa.JSON(), nullable=False)
            else:
                op.alter_column('products', name, existing_type=sa.JSON(), nullable=False)


def downgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('products')}
    for name in ('field_verification', 'field_provenance'):
        if name in columns:
            op.drop_column('products', name)
