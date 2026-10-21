"""Add process mapping and remove retired product attributes."""
from alembic import op
import sqlalchemy as sa

revision = '0006_process_remove_legacy_fields'
down_revision = '0005_canonical_material'
branch_labels = None
depends_on = None

def upgrade():
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('products')}
    if 'process' not in columns: op.add_column('products', sa.Column('process', sa.String(180), nullable=True))
    if 'process_id' not in columns: op.add_column('products', sa.Column('process_id', sa.String(20), nullable=True))
    op.get_bind().execute(sa.text("UPDATE products SET process='Others', process_id='Others' WHERE process IS NULL OR process_id IS NULL"))
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('products')}
    for name in ('subtype', 'brand', 'sku', 'color', 'description', 'condition'):
        if name in columns: op.drop_column('products', name)

def downgrade():
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('products')}
    for name, typ in (('subtype', sa.String(80)), ('brand', sa.String(120)), ('sku', sa.String(100)), ('color', sa.String(100)), ('description', sa.Text()), ('condition', sa.String(80))):
        if name not in columns: op.add_column('products', sa.Column(name, typ, nullable=True))
    for name in ('process_id', 'process'):
        if name in columns: op.drop_column('products', name)
