"""sub folder

Revision ID: 5274cdb99115
Revises: 7c2d9f4a8b10
Create Date: 2026-03-29 11:53:17.570567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


revision: str = '5274cdb99115'
down_revision: Union[str, Sequence[str], None] = '7c2d9f4a8b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table, column):
    cols = [c["name"] for c in sa_inspect(conn).get_columns(table)]
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()
    if not sa_inspect(conn).has_table("document_drive_folders"):
        return
    if not _has_column(conn, "document_drive_folders", "parent_id"):
        with op.batch_alter_table("document_drive_folders") as batch_op:
            batch_op.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_ddf_parent_id", "document_drive_folders", ["parent_id"], ["id"]
            )


def downgrade() -> None:
    with op.batch_alter_table("document_drive_folders") as batch_op:
        batch_op.drop_constraint("fk_ddf_parent_id", type_="foreignkey")
        batch_op.drop_column("parent_id")
