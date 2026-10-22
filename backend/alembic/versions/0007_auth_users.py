"""Add shared-workspace user accounts for login."""
from alembic import op
import sqlalchemy as sa

revision = '0007_auth_users'
down_revision = '0006_process_fields'
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(80), nullable=False, unique=True),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('session_version', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        )


def downgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if 'users' in tables:
        op.drop_table('users')
