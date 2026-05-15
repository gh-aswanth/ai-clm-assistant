"""contract_guidelines_tables_views_seed

Revision ID: e8f9a0b1c2d3
Revises: b3b7f95b8128
Create Date: 2026-03-26 12:00:00.000000

"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, None] = "b3b7f95b8128"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SECTION_ORDER: list[tuple[str, str]] = [
    ("financial_limits", "Financial limits"),
    ("mandatory_clauses", "Mandatory clauses"),
    ("technical_standards", "Technical standards"),
    ("compliance_requirements", "Compliance requirements"),
    ("contractor_eligibility", "Contractor eligibility"),
    ("work_execution_standards", "Work execution standards"),
    ("measurement_payment", "Measurement & payment"),
    ("contract_administration", "Contract administration"),
    ("defect_liability", "Defect liability"),
    ("documentation_requirements", "Documentation requirements"),
    ("decision_thresholds", "Decision thresholds"),
    ("validation_weights", "Validation weights"),
    ("critical_issues", "Critical issues"),
]


def _load_payload() -> dict:
    backend = Path(__file__).resolve().parents[2]
    p = backend / "app" / "seeds" / "cpwd_guideline_v1.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _seed_catalog(conn, framework_id: int, data: dict) -> None:
    rows: list[dict] = []

    def add_list(bucket: str, domain: str | None, items: list, base_order: int = 0) -> None:
        for i, code in enumerate(items):
            rows.append(
                {
                    "framework_id": framework_id,
                    "bucket": bucket,
                    "domain": domain,
                    "code": str(code),
                    "sort_order": base_order + i,
                }
            )

    mc = data.get("mandatory_clauses") or {}
    if isinstance(mc, dict):
        for domain, items in mc.items():
            if isinstance(items, list):
                add_list("mandatory_clauses", domain, items)

    cr = data.get("compliance_requirements") or {}
    if isinstance(cr, dict):
        for domain, items in cr.items():
            if isinstance(items, list):
                add_list("compliance_requirements", domain, items)

    dr = data.get("documentation_requirements") or {}
    if isinstance(dr, dict):
        for domain, items in dr.items():
            if isinstance(items, list):
                add_list("documentation_requirements", domain, items)

    ci = data.get("critical_issues")
    if isinstance(ci, list):
        add_list("critical_issues", None, ci)

    for row in rows:
        conn.execute(
            sa.text(
                "INSERT INTO guideline_catalog_entries "
                "(framework_id, bucket, domain, code, sort_order) "
                "VALUES (:framework_id, :bucket, :domain, :code, :sort_order)"
            ),
            row,
        )


def upgrade() -> None:
    op.create_table(
        "guideline_frameworks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("version_label", sa.String(length=64), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("ix_guideline_frameworks_slug", "guideline_frameworks", ["slug"], unique=True)

    op.create_table(
        "guideline_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("framework_id", sa.Integer(), sa.ForeignKey("guideline_frameworks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("body", sa.JSON(), nullable=False),
    )
    op.create_index("ix_guideline_sections_framework_id", "guideline_sections", ["framework_id"])
    op.create_index(
        "uq_guideline_section_framework_key",
        "guideline_sections",
        ["framework_id", "section_key"],
        unique=True,
    )

    op.create_table(
        "guideline_catalog_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "framework_id",
            sa.Integer(),
            sa.ForeignKey("guideline_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bucket", sa.String(length=64), nullable=False),
        sa.Column("domain", sa.String(length=128), nullable=True),
        sa.Column("code", sa.String(length=256), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
    )
    op.create_index("ix_gce_framework_bucket", "guideline_catalog_entries", ["framework_id", "bucket"])

    op.execute(
        """
        CREATE VIEW v_guideline_section_index AS
        SELECT
            f.id AS framework_id,
            f.slug AS framework_slug,
            f.title AS framework_title,
            s.id AS section_id,
            s.section_key,
            s.title AS section_title,
            s.sort_order
        FROM guideline_sections s
        JOIN guideline_frameworks f ON f.id = s.framework_id
        """
    )

    op.execute(
        """
        CREATE VIEW v_guideline_catalog AS
        SELECT
            e.id AS catalog_entry_id,
            f.slug AS framework_slug,
            e.bucket,
            e.domain,
            e.code,
            e.sort_order
        FROM guideline_catalog_entries e
        JOIN guideline_frameworks f ON f.id = e.framework_id
        """
    )

    payload = _load_payload()
    conn = op.get_bind()

    conn.execute(
        sa.text(
            "INSERT INTO guideline_frameworks (slug, title, summary, version_label, is_default) "
            "VALUES (:slug, :title, :summary, :version_label, :is_default)"
        ),
        {
            "slug": "cpwd-v1",
            "title": "CPWD-aligned contract review guideline",
            "summary": "Financial limits, mandatory clauses, technical standards, compliance, scoring weights, and decision thresholds for engineering / works contracts.",
            "version_label": "1.0",
            "is_default": True,
        },
    )

    res = conn.execute(sa.text("SELECT id FROM guideline_frameworks WHERE slug = 'cpwd-v1'"))
    row = res.fetchone()
    if not row:
        return
    fw_id = int(row[0])

    for i, (key, title) in enumerate(SECTION_ORDER):
        body = payload.get(key)
        if body is None:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO guideline_sections (framework_id, section_key, title, sort_order, body) "
                "VALUES (:framework_id, :section_key, :title, :sort_order, :body)"
            ),
            {
                "framework_id": fw_id,
                "section_key": key,
                "title": title,
                "sort_order": i,
                "body": json.dumps(body, ensure_ascii=False),
            },
        )

    _seed_catalog(conn, fw_id, payload)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_guideline_catalog")
    op.execute("DROP VIEW IF EXISTS v_guideline_section_index")
    op.drop_index("ix_gce_framework_bucket", table_name="guideline_catalog_entries")
    op.drop_table("guideline_catalog_entries")
    op.drop_index("uq_guideline_section_framework_key", table_name="guideline_sections")
    op.drop_index("ix_guideline_sections_framework_id", table_name="guideline_sections")
    op.drop_table("guideline_sections")
    op.drop_index("ix_guideline_frameworks_slug", table_name="guideline_frameworks")
    op.drop_table("guideline_frameworks")
