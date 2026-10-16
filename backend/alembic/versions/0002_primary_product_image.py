"""Add primary-image metadata while preserving existing image records.

Revision ID: 0002_primary_product_image
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_primary_product_image'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # 0001 builds metadata dynamically. On a fresh database it may already have
    # this column; on databases upgraded before this release it will not.
    inspector = sa.inspect(op.get_bind())
    columns = {column['name'] for column in inspector.get_columns('product_images')}
    if 'is_primary' not in columns:
        op.add_column('product_images', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()))
    bind = op.get_bind()
    products = bind.execute(sa.text('SELECT DISTINCT product_id FROM product_images')).scalars().all()
    for product_id in products:
        first_id = bind.execute(sa.text('SELECT MIN(id) FROM product_images WHERE product_id = :product_id'), {'product_id': product_id}).scalar()
        if first_id is not None:
            bind.execute(sa.text('UPDATE product_images SET is_primary = (id = :first_id) WHERE product_id = :product_id'),
                         {'first_id': first_id, 'product_id': product_id})


def downgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('product_images')}
    if 'is_primary' in columns:
        op.drop_column('product_images', 'is_primary')
