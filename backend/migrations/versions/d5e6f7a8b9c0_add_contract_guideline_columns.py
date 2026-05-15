"""add_contract_guideline_columns

Revision ID: d5e6f7a8b9c0
Revises: c4e5f6a7b8c9
Create Date: 2026-03-30

Adds guideline / AI automation columns to ``contracts`` when missing (older DBs).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_GUIDELINE_COLS = [
    ("guideline_framework_slug", sa.String(128)),
    ("guideline_framework_title", sa.String(256)),
    ("guideline_snapshot", sa.JSON()),
    ("guideline_financial_limits", sa.JSON()),
    ("guideline_mandatory_clauses", sa.JSON()),
    ("guideline_technical_standards", sa.JSON()),
    ("guideline_compliance_requirements", sa.JSON()),
    ("guideline_contractor_eligibility", sa.JSON()),
    ("guideline_work_execution_standards", sa.JSON()),
    ("guideline_measurement_payment", sa.JSON()),
    ("guideline_contract_administration", sa.JSON()),
    ("guideline_defect_liability", sa.JSON()),
    ("guideline_documentation_requirements", sa.JSON()),
    ("guideline_decision_thresholds", sa.JSON()),
    ("guideline_validation_weights", sa.JSON()),
    ("guideline_critical_issues", sa.JSON()),
]


def upgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    if not insp.has_table("contracts"):
        return
    existing = {c["name"] for c in insp.get_columns("contracts")}
    to_add = [(n, t) for n, t in _GUIDELINE_COLS if n not in existing]
    if not to_add:
        return
    with op.batch_alter_table("contracts") as batch_op:
        for name, coltype in to_add:
            batch_op.add_column(sa.Column(name, coltype, nullable=True))
    if "guideline_framework_slug" in {n for n, _ in to_add}:
        with op.batch_alter_table("contracts") as batch_op:
            batch_op.create_index("ix_contracts_guideline_framework_slug", ["guideline_framework_slug"])


def downgrade() -> None:
    from sqlalchemy import inspect

    conn = op.get_bind()
    insp = inspect(conn)
    if not insp.has_table("contracts"):
        return
    existing = {c["name"] for c in insp.get_columns("contracts")}
    to_drop = [n for n, _ in _GUIDELINE_COLS if n in existing]
    if not to_drop:
        return
    with op.batch_alter_table("contracts") as batch_op:
        if "ix_contracts_guideline_framework_slug" in {i["name"] for i in insp.get_indexes("contracts")}:
            batch_op.drop_index("ix_contracts_guideline_framework_slug")
    with op.batch_alter_table("contracts") as batch_op:
        for name in to_drop:
            batch_op.drop_column(name)
