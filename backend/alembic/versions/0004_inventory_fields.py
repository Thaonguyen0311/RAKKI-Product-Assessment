"""Add inventory attributes to existing product records.

Revision ID: 0004_inventory_fields
Revises: 0003_product_field_provenance
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_inventory_fields'
down_revision = '0003_product_field_provenance'
branch_labels = None
depends_on = None


def _columns():
    return {column['name']: column for column in sa.inspect(op.get_bind()).get_columns('products')}


def upgrade():
    columns = _columns()
    additions = (
        ('location', sa.String(length=180), True),
        ('completion_date', sa.Date(), True),
        ('overall_condition', sa.Integer(), True),
        ('is_intact', sa.Boolean(), True),
        ('is_clean', sa.Boolean(), True),
        ('quantity', sa.Integer(), True),
        ('additional_notes', sa.Text(), True),
    )
    for name, column_type, nullable in additions:
        if name not in columns:
            op.add_column('products', sa.Column(name, column_type, nullable=nullable))

    bind = op.get_bind()
    bind.execute(sa.text(
        'UPDATE products SET completion_date = DATE(COALESCE(created_at, CURRENT_TIMESTAMP)) WHERE completion_date IS NULL'
    ))
    bind.execute(sa.text('UPDATE products SET quantity = 1 WHERE quantity IS NULL'))

    columns = _columns()
    if columns['completion_date']['nullable']:
        if bind.dialect.name == 'sqlite':
            with op.batch_alter_table('products') as batch:
                batch.alter_column('completion_date', existing_type=sa.Date(), nullable=False)
        else:
            op.alter_column('products', 'completion_date', existing_type=sa.Date(), nullable=False)

    columns = _columns()
    if columns['quantity']['nullable']:
        if bind.dialect.name == 'sqlite':
            with op.batch_alter_table('products') as batch:
                batch.alter_column('quantity', existing_type=sa.Integer(), nullable=False, server_default='1')
        else:
            op.alter_column('products', 'quantity', existing_type=sa.Integer(), nullable=False, server_default='1')
    elif columns['quantity'].get('default') is None:
        op.alter_column('products', 'quantity', existing_type=sa.Integer(), nullable=False, server_default='1')


def downgrade():
    columns = _columns()
    for name in ('additional_notes', 'quantity', 'is_clean', 'is_intact', 'overall_condition', 'completion_date', 'location'):
        if name in columns:
            op.drop_column('products', name)
