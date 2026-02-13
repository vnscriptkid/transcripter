"""Initial transcripts table

Revision ID: 001
Revises: 
Create Date: 2025-02-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transcripts',
        sa.Column('id', sa.String(length=8), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('relative_path', sa.String(length=500), nullable=True),
        sa.Column('batch_id', sa.String(length=8), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('transcript_content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transcripts_batch_id', 'transcripts', ['batch_id'])
    op.create_index('idx_transcripts_status', 'transcripts', ['status'])
    op.create_index('idx_transcripts_created_at', 'transcripts', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_transcripts_created_at', table_name='transcripts')
    op.drop_index('idx_transcripts_status', table_name='transcripts')
    op.drop_index('idx_transcripts_batch_id', table_name='transcripts')
    op.drop_table('transcripts')
