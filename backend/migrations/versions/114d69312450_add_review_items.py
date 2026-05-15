"""add review_items table

Revision ID: 114d69312450
Revises: a1b2c3d4e5f8
Create Date: 2026-03-26 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '114d69312450'
down_revision: Union[str, None] = 'a1b2c3d4e5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    if inspect(op.get_bind()).has_table('review_items'):
        return
    op.create_table(
        'review_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_query', sa.Text(), nullable=True),
        sa.Column('item_type', sa.String(64), nullable=False, server_default='finding'),
        sa.Column('severity', sa.String(32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_review_items_id', 'review_items', ['id'])
    op.create_index('ix_review_items_contract_id', 'review_items', ['contract_id'])


def downgrade() -> None:
    op.drop_index('ix_review_items_contract_id', table_name='review_items')
    op.drop_index('ix_review_items_id', table_name='review_items')
    op.drop_table('review_items')
