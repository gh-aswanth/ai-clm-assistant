"""add review_items table

Revision ID: f7e8d9c0b1a2
Revises: c2d3e4f5a6b7
Create Date: 2026-03-26 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = 'f7e8d9c0b1a2'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not inspect(op.get_bind()).has_table('review_items'):
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
    if inspect(op.get_bind()).has_table('review_items'):
        op.drop_index('ix_review_items_contract_id', table_name='review_items')
        op.drop_index('ix_review_items_id', table_name='review_items')
        op.drop_table('review_items')
