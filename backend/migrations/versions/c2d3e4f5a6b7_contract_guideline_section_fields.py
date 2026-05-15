"""contract_guideline_section_fields

Revision ID: c2d3e4f5a6b7
Revises: 359680a19941
Create Date: 2026-03-26 09:00:00.000000

Adds one JSON column per guideline section to contracts, plus guideline_framework_title.
Backfills from existing guideline_snapshot where present.
"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa

revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, Sequence[str], None] = '359680a19941'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SECTION_KEYS = [
    'financial_limits',
    'mandatory_clauses',
    'technical_standards',
    'compliance_requirements',
    'contractor_eligibility',
    'work_execution_standards',
    'measurement_payment',
    'contract_administration',
    'defect_liability',
    'documentation_requirements',
    'decision_thresholds',
    'validation_weights',
    'critical_issues',
]


def upgrade() -> None:
    from sqlalchemy import inspect
    if not inspect(op.get_bind()).has_table('contracts'):
        return
    with op.batch_alter_table('contracts') as batch_op:
        batch_op.add_column(sa.Column('guideline_framework_title', sa.String(256), nullable=True))
        for key in SECTION_KEYS:
            batch_op.add_column(sa.Column(f'guideline_{key}', sa.JSON(), nullable=True))

    # Backfill from existing guideline_snapshot
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT id, guideline_snapshot FROM contracts WHERE guideline_snapshot IS NOT NULL"
    )).fetchall()

    for row in rows:
        contract_id, raw_snap = row[0], row[1]
        try:
            snap = json.loads(raw_snap) if isinstance(raw_snap, str) else raw_snap
        except Exception:
            continue
        if not isinstance(snap, dict):
            continue

        title = snap.get('framework_title') or snap.get('framework_slug') or ''
        updates = {'guideline_framework_title': title}

        sections_list = snap.get('sections', [])
        if isinstance(sections_list, list):
            for sec in sections_list:
                skey = sec.get('section_key', '')
                if skey in SECTION_KEYS:
                    body = sec.get('body')
                    updates[f'guideline_{skey}'] = json.dumps(body, ensure_ascii=False) if body is not None else None

        set_clause = ', '.join(
            f'"{col}" = :{col}' for col in updates
        )
        params = {col: val for col, val in updates.items()}
        params['id'] = contract_id
        conn.execute(sa.text(f'UPDATE contracts SET {set_clause} WHERE id = :id'), params)


def downgrade() -> None:
    with op.batch_alter_table('contracts') as batch_op:
        batch_op.drop_column('guideline_framework_title')
        for key in SECTION_KEYS:
            batch_op.drop_column(f'guideline_{key}')
