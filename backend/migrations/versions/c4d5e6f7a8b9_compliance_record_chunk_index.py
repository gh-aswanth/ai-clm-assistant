"""compliance_record_chunk_index

Revision ID: c4d5e6f7a8b9
Revises: a3b4c5d6e7f8
Create Date: 2026-03-30

Adds ``chunk_index`` to ``compliance_records`` (links LLM checks to ``document_chunks.chunk_index``).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("compliance_records")}
    if "chunk_index" not in cols:
        with op.batch_alter_table("compliance_records") as batch_op:
            batch_op.add_column(sa.Column("chunk_index", sa.Integer(), nullable=True))


def downgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("compliance_records")}
    if "chunk_index" in cols:
        with op.batch_alter_table("compliance_records") as batch_op:
            batch_op.drop_column("chunk_index")
