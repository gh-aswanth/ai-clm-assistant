"""compliance_record_document_version_id

Revision ID: d5e6f7a8b0c1
Revises: c4d5e6f7a8b9
Create Date: 2026-03-30

Scopes automated compliance rows per ``document_versions`` row; re-run replaces only that version's rows.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5e6f7a8b0c1"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("compliance_records")}
    if "document_version_id" not in cols:
        with op.batch_alter_table("compliance_records") as batch_op:
            batch_op.add_column(sa.Column("document_version_id", sa.Integer(), nullable=True))
        op.create_index(
            "ix_compliance_records_document_version_id",
            "compliance_records",
            ["document_version_id"],
            unique=False,
        )
        # FK is defined on the SQLAlchemy model; SQLite cannot ALTER ADD CONSTRAINT here.


def downgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns("compliance_records")}
    if "document_version_id" in cols:
        op.drop_index("ix_compliance_records_document_version_id", table_name="compliance_records")
        with op.batch_alter_table("compliance_records") as batch_op:
            batch_op.drop_column("document_version_id")
