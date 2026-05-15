"""add_scoring_results_table

Revision ID: 385a0a29b077
Revises: 7c4539bf1683
Create Date: 2026-03-30 15:41:40.000901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '385a0a29b077'
down_revision: Union[str, Sequence[str], None] = '7c4539bf1683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scoring_results",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("contract_id", sa.Integer, sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_version_id", sa.Integer, sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("result_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("scoring_results")
