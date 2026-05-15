"""add_files_table_refactor

Revision ID: a1b2c3d4e5f6
Revises: 385a0a29b077
Create Date: 2026-03-30 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "385a0a29b077"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    insp = inspect(op.get_bind())

    # 1. Create the central files table (only if it doesn't exist yet)
    if not insp.has_table("files"):
        op.create_table(
            "files",
            sa.Column("id", sa.Integer, primary_key=True, index=True),
            sa.Column("original_filename", sa.String, nullable=False),
            sa.Column("file_path", sa.String, nullable=False),
            sa.Column("file_type", sa.String, nullable=True),
            sa.Column("content_type", sa.String, nullable=True),
            sa.Column("size_bytes", sa.Integer, default=0),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )

    # 2. Add file_id columns — skip tables that don't exist yet on a fresh DB
    #    (the 9979e050d698 migration handles file_id for those tables after the merge)
    if not insp.has_table("document_versions"):
        return

    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.add_column(sa.Column("file_id", sa.Integer, nullable=True))

    if insp.has_table("document_drive_files"):
        with op.batch_alter_table("document_drive_files") as batch_op:
            batch_op.add_column(sa.Column("file_id", sa.Integer, nullable=True))

    if insp.has_table("document_chunks"):
        with op.batch_alter_table("document_chunks") as batch_op:
            batch_op.add_column(sa.Column("file_id", sa.Integer, nullable=True))

    # 3. Backfill: create File rows from existing document_versions
    conn = op.get_bind()

    dv_rows = conn.execute(
        sa.text("SELECT id, file_path, file_type, created_at FROM document_versions WHERE file_path IS NOT NULL")
    ).fetchall()

    for row in dv_rows:
        dv_id, fp, ft, ca = row
        if not fp:
            continue
        import os
        fname = os.path.basename(fp)
        result = conn.execute(
            sa.text(
                "INSERT INTO files (original_filename, file_path, file_type, created_at) "
                "VALUES (:fn, :fp, :ft, :ca)"
            ),
            {"fn": fname, "fp": fp, "ft": ft, "ca": ca},
        )
        file_id = result.lastrowid
        conn.execute(
            sa.text("UPDATE document_versions SET file_id = :fid WHERE id = :vid"),
            {"fid": file_id, "vid": dv_id},
        )

    # 4. Backfill: create File rows from existing document_drive_files
    df_rows = conn.execute(
        sa.text("SELECT id, original_filename, file_path, content_type, size_bytes, created_at FROM document_drive_files")
    ).fetchall()

    for row in df_rows:
        df_id, ofn, fp, ct, sb, ca = row
        if not fp:
            continue
        import os
        ext = ofn.rsplit(".", 1)[-1].lower() if ofn else ""
        result = conn.execute(
            sa.text(
                "INSERT INTO files (original_filename, file_path, file_type, content_type, size_bytes, created_at) "
                "VALUES (:fn, :fp, :ft, :ct, :sb, :ca)"
            ),
            {"fn": ofn, "fp": fp, "ft": ext, "ct": ct, "sb": sb or 0, "ca": ca},
        )
        file_id = result.lastrowid
        conn.execute(
            sa.text("UPDATE document_drive_files SET file_id = :fid WHERE id = :did"),
            {"fid": file_id, "did": df_id},
        )

    # 5. Backfill: update document_chunks — map drive_file_id or document_version_id to file_id
    conn.execute(
        sa.text(
            "UPDATE document_chunks SET file_id = ("
            "  SELECT dv.file_id FROM document_versions dv WHERE dv.id = document_chunks.document_version_id"
            ") WHERE document_chunks.document_version_id IS NOT NULL"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE document_chunks SET file_id = ("
            "  SELECT df.file_id FROM document_drive_files df WHERE df.id = document_chunks.drive_file_id"
            ") WHERE document_chunks.drive_file_id IS NOT NULL AND document_chunks.file_id IS NULL"
        )
    )

    # 6. Create indexes on the new file_id columns
    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.create_index("ix_document_versions_file_id", ["file_id"])

    with op.batch_alter_table("document_drive_files") as batch_op:
        batch_op.create_index("ix_document_drive_files_file_id", ["file_id"])

    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.create_index("ix_document_chunks_file_id", ["file_id"])


def downgrade() -> None:
    with op.batch_alter_table("document_chunks") as batch_op:
        batch_op.drop_index("ix_document_chunks_file_id")
        batch_op.drop_column("file_id")

    with op.batch_alter_table("document_drive_files") as batch_op:
        batch_op.drop_index("ix_document_drive_files_file_id")
        batch_op.drop_column("file_id")

    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.drop_index("ix_document_versions_file_id")
        batch_op.drop_column("file_id")

    op.drop_table("files")
