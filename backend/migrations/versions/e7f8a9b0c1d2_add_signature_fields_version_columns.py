"""add_signature_fields_version_columns

Revision ID: e7f8a9b0c1d2
Revises: d5e6f7a8b9c0
Create Date: 2026-03-30

Adds ``version_id`` and ``version_signer_id`` to ``signature_fields`` when missing.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    if not insp.has_table("signature_fields"):
        return
    cols = {c["name"] for c in insp.get_columns("signature_fields")}
    with op.batch_alter_table("signature_fields") as batch_op:
        if "version_id" not in cols:
            batch_op.add_column(sa.Column("version_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_signature_fields_version_id",
                "document_versions",
                ["version_id"],
                ["id"],
            )
            batch_op.create_index("ix_signature_fields_version_id", ["version_id"], unique=False)
        if "version_signer_id" not in cols:
            batch_op.add_column(sa.Column("version_signer_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_signature_fields_version_signer_id",
                "version_signers",
                ["version_signer_id"],
                ["id"],
            )
            batch_op.create_index(
                "ix_signature_fields_version_signer_id",
                ["version_signer_id"],
                unique=False,
            )


def downgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    if not insp.has_table("signature_fields"):
        return
    cols = {c["name"] for c in insp.get_columns("signature_fields")}
    with op.batch_alter_table("signature_fields") as batch_op:
        if "version_signer_id" in cols:
            batch_op.drop_constraint("fk_signature_fields_version_signer_id", type_="foreignkey")
            batch_op.drop_index("ix_signature_fields_version_signer_id")
            batch_op.drop_column("version_signer_id")
        if "version_id" in cols:
            batch_op.drop_constraint("fk_signature_fields_version_id", type_="foreignkey")
            batch_op.drop_index("ix_signature_fields_version_id")
            batch_op.drop_column("version_id")
