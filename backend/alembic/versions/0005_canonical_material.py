"""Add canonical mapped material fields to products."""
from alembic import op
import sqlalchemy as sa

revision = '0005_canonical_material'
down_revision = '0004_inventory_fields'
branch_labels = None
depends_on = None


def upgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('products')}
    additions = (
        ('material', sa.String(length=180)),
        ('material_id', sa.BigInteger()),
        ('material_category', sa.Text()),
        ('material_verification', sa.String(length=30)),
        ('material_confidence', sa.Numeric(precision=4, scale=3)),
    )
    for name, column_type in additions:
        if name not in columns:
            op.add_column('products', sa.Column(name, column_type, nullable=True))


def downgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('products')}
    for name in ('material_confidence', 'material_verification', 'material_category', 'material_id', 'material'):
        if name in columns:
            op.drop_column('products', name)
