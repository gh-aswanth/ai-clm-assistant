"""contract_guideline_snapshot_columns

Revision ID: f2a3b4c5d6e7
Revises: e8f9a0b1c2d3
Create Date: 2026-03-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e8f9a0b1c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    if not inspect(op.get_bind()).has_table("contracts"):
        return
    with op.batch_alter_table("contracts") as batch:
        batch.add_column(sa.Column("guideline_framework_slug", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("guideline_snapshot", sa.JSON(), nullable=True))
    op.create_index("ix_contracts_guideline_framework_slug", "contracts", ["guideline_framework_slug"])


def downgrade() -> None:
    op.drop_index("ix_contracts_guideline_framework_slug", table_name="contracts")
    with op.batch_alter_table("contracts") as batch:
        batch.drop_column("guideline_snapshot")
        batch.drop_column("guideline_framework_slug")
