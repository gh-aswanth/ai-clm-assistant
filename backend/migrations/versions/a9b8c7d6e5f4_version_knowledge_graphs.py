"""version_knowledge_graphs

Revision ID: a9b8c7d6e5f4
Revises: d5e6f7a8b0c1
Create Date: 2026-03-31

Stores LangChain LLM graph output (list of GraphDocument JSON) per document version.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "version_knowledge_graphs" not in existing_tables:
        op.create_table(
            "version_knowledge_graphs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
            sa.Column(
                "document_version_id",
                sa.Integer(),
                sa.ForeignKey("document_versions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("graph_documents_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    existing_indexes = [idx["name"] for idx in inspector.get_indexes("version_knowledge_graphs")]
    if "ix_version_knowledge_graphs_contract_id" not in existing_indexes:
        op.create_index("ix_version_knowledge_graphs_contract_id", "version_knowledge_graphs", ["contract_id"])
    if "ix_version_knowledge_graphs_document_version_id" not in existing_indexes:
        op.create_index(
            "ix_version_knowledge_graphs_document_version_id",
            "version_knowledge_graphs",
            ["document_version_id"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_table("version_knowledge_graphs")
