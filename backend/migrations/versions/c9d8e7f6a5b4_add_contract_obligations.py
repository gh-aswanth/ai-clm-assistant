"""add contract_obligations (CPWD obligation radar)

Revision ID: c9d8e7f6a5b4
Revises: b1c2d3e4f5a6
Create Date: 2026-04-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d8e7f6a5b4"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contract_obligations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contract_id", sa.Integer(), nullable=False),
        sa.Column("obligation_kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("remind_days_before", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contract_obligations_id"), "contract_obligations", ["id"], unique=False)
    op.create_index(op.f("ix_contract_obligations_contract_id"), "contract_obligations", ["contract_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contract_obligations_contract_id"), table_name="contract_obligations")
    op.drop_index(op.f("ix_contract_obligations_id"), table_name="contract_obligations")
    op.drop_table("contract_obligations")
