"""scoring_results_file_id

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-03-30

Adds ``file_id`` to ``scoring_results`` for per-document scoring; backfills from ``document_versions``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    if not insp.has_table("scoring_results"):
        return

    cols = {c["name"] for c in insp.get_columns("scoring_results")}
    if "file_id" not in cols:
        with op.batch_alter_table("scoring_results") as batch_op:
            batch_op.add_column(sa.Column("file_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_scoring_results_file_id_files",
                "files",
                ["file_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index("ix_scoring_results_file_id", ["file_id"], unique=False)

    conn.execute(
        sa.text(
            """
            UPDATE scoring_results
            SET file_id = (
                SELECT dv.file_id FROM document_versions dv
                WHERE dv.id = scoring_results.document_version_id
            )
            WHERE document_version_id IS NOT NULL
              AND file_id IS NULL
            """
        )
    )


def downgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    if not insp.has_table("scoring_results"):
        return
    cols = {c["name"] for c in insp.get_columns("scoring_results")}
    if "file_id" not in cols:
        return

    with op.batch_alter_table("scoring_results") as batch_op:
        batch_op.drop_constraint("fk_scoring_results_file_id_files", type_="foreignkey")
        batch_op.drop_index("ix_scoring_results_file_id")
        batch_op.drop_column("file_id")
