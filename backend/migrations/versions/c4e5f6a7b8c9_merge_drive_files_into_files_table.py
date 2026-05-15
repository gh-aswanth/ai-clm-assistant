"""merge_drive_files_into_files_table

Revision ID: c4e5f6a7b8c9
Revises: 9979e050d698
Create Date: 2026-03-30

Adds folder_id / upload_id to ``files``, restores any missing ``document_versions``
columns, backfills from ``document_drive_files``, then drops ``document_drive_files``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "9979e050d698"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect, text

    conn = op.get_bind()
    insp = inspect(conn)

    # ── files: folder_id, upload_id ─────────────────────────────────────
    if insp.has_table("files"):
        fcols = {c["name"] for c in insp.get_columns("files")}
        if "folder_id" not in fcols:
            with op.batch_alter_table("files") as batch_op:
                batch_op.add_column(sa.Column("folder_id", sa.Integer(), nullable=True))
                batch_op.create_index("ix_files_folder_id", ["folder_id"], unique=False)
                batch_op.create_foreign_key(
                    "fk_files_folder_id",
                    "document_drive_folders",
                    ["folder_id"],
                    ["id"],
                )
        if "upload_id" not in fcols:
            with op.batch_alter_table("files") as batch_op:
                batch_op.add_column(sa.Column("upload_id", sa.String(), nullable=True))
                batch_op.create_index("ix_files_upload_id", ["upload_id"], unique=False)

    # ── document_versions: label, signed_file_path, is_latest ─────────────
    if insp.has_table("document_versions"):
        dvcols = {c["name"] for c in insp.get_columns("document_versions")}
        with op.batch_alter_table("document_versions") as batch_op:
            if "label" not in dvcols:
                batch_op.add_column(sa.Column("label", sa.String(), nullable=True))
            if "signed_file_path" not in dvcols:
                batch_op.add_column(sa.Column("signed_file_path", sa.String(), nullable=True))
            if "is_latest" not in dvcols:
                batch_op.add_column(
                    sa.Column("is_latest", sa.Boolean(), nullable=True, server_default="0")
                )

    # ── Backfill from document_drive_files → files ────────────────────────
    if insp.has_table("document_drive_files"):
        rows = conn.execute(
            text(
                "SELECT id, folder_id, file_id, upload_id FROM document_drive_files "
                "WHERE file_id IS NOT NULL"
            )
        ).fetchall()
        for _ddf_id, folder_id, file_id, upload_id in rows:
            conn.execute(
                text(
                    "UPDATE files SET folder_id = :fid, upload_id = :uid "
                    "WHERE id = :file_id AND (folder_id IS NULL OR upload_id IS NULL)"
                ),
                {"fid": folder_id, "uid": upload_id, "file_id": file_id},
            )
        # Prefer always setting from drive row (authoritative)
        for _ddf_id, folder_id, file_id, upload_id in rows:
            conn.execute(
                text(
                    "UPDATE files SET folder_id = :fid, upload_id = :uid WHERE id = :file_id"
                ),
                {"fid": folder_id, "uid": upload_id, "file_id": file_id},
            )

        op.drop_table("document_drive_files")


def downgrade() -> None:
    op.create_table(
        "document_drive_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("folder_id", sa.Integer(), sa.ForeignKey("document_drive_folders.id"), nullable=False),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("files.id"), nullable=True),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), default=0),
        sa.Column("upload_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_document_drive_files_file_id", "document_drive_files", ["file_id"])
    op.create_index("ix_document_drive_files_upload_id", "document_drive_files", ["upload_id"])

    from sqlalchemy import text

    conn = op.get_bind()
    conn.execute(
        text(
            "INSERT INTO document_drive_files "
            "(folder_id, file_id, original_filename, filename, content_type, size_bytes, upload_id, created_at) "
            "SELECT folder_id, id, original_filename, original_filename, content_type, size_bytes, "
            "COALESCE(upload_id, ''), created_at FROM files WHERE folder_id IS NOT NULL"
        )
    )

    with op.batch_alter_table("files") as batch_op:
        batch_op.drop_index("ix_files_upload_id")
        batch_op.drop_column("upload_id")
        batch_op.drop_constraint("fk_files_folder_id", type_="foreignkey")
        batch_op.drop_index("ix_files_folder_id")
        batch_op.drop_column("folder_id")
