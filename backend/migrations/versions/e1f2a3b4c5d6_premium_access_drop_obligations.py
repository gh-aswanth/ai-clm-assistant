"""user premium_access; drop contract_obligations

Revision ID: e1f2a3b4c5d6
Revises: c9d8e7f6a5b4
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "c9d8e7f6a5b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "premium_access",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
    op.execute("DROP TABLE IF EXISTS contract_obligations")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("premium_access")
