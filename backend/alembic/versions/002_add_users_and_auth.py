"""Add users table and user_id to transcripts

Revision ID: 002
Revises: 001
Create Date: 2026-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('google_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('picture', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_google_id', 'users', ['google_id'])
    op.create_index('idx_users_email', 'users', ['email'])

    # Add user_id column to transcripts (nullable for backward compat)
    op.add_column('transcripts', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.create_foreign_key('fk_transcripts_user_id', 'transcripts', 'users', ['user_id'], ['id'])
    op.create_index('idx_transcripts_user_id', 'transcripts', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_transcripts_user_id', table_name='transcripts')
    op.drop_constraint('fk_transcripts_user_id', 'transcripts', type_='foreignkey')
    op.drop_column('transcripts', 'user_id')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_google_id', table_name='users')
    op.drop_table('users')
