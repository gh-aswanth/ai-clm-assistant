"""document_chunk_page_number

Revision ID: a3b4c5d6e7f8
Revises: f8a9b0c1d2e3
Create Date: 2026-03-30

Adds optional ``page_number`` to ``document_chunks`` for preview navigation (PDF).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, Sequence[str], None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("document_chunks")}
    if "page_number" not in cols:
        with op.batch_alter_table("document_chunks") as batch_op:
            batch_op.add_column(sa.Column("page_number", sa.Integer(), nullable=True))


def downgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("document_chunks")}
    if "page_number" in cols:
        with op.batch_alter_table("document_chunks") as batch_op:
            batch_op.drop_column("page_number")
