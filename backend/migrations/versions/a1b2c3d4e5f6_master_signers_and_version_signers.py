"""master_signers_version_signers_redesign

Revision ID: a1b2c3d4e5f8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision: str = 'a1b2c3d4e5f8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _column_exists(table: str, column: str) -> bool:
    cols = [c['name'] for c in inspect(op.get_bind()).get_columns(table)]
    return column in cols


def upgrade() -> None:
    # ── 1. master_signers ────────────────────────────────────────────────────
    if not _table_exists('master_signers'):
        op.create_table(
            'master_signers',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
            sa.Column('phone', sa.String(), nullable=True),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('organization', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    # ── 2. document_versions — new columns ───────────────────────────────────
    # On a fresh DB the core tables are created by the other migration branch;
    # skip all ALTER operations here — they'll already have the right schema.
    if not _table_exists('document_versions'):
        return
    with op.batch_alter_table('document_versions') as batch_op:
        if not _column_exists('document_versions', 'label'):
            batch_op.add_column(sa.Column('label', sa.String(), nullable=True))
        if not _column_exists('document_versions', 'signed_file_path'):
            batch_op.add_column(sa.Column('signed_file_path', sa.String(), nullable=True))
        if not _column_exists('document_versions', 'is_latest'):
            batch_op.add_column(sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='0'))

    # ── 3. contracts — contract_number ───────────────────────────────────────
    with op.batch_alter_table('contracts') as batch_op:
        if not _column_exists('contracts', 'contract_number'):
            batch_op.add_column(sa.Column('contract_number', sa.String(), nullable=True))

    # ── 4. templates — is_active ─────────────────────────────────────────────
    with op.batch_alter_table('templates') as batch_op:
        if not _column_exists('templates', 'is_active'):
            batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))

    # ── 5. version_signers ───────────────────────────────────────────────────
    if not _table_exists('version_signers'):
        op.create_table(
            'version_signers',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('version_id', sa.Integer(), sa.ForeignKey('document_versions.id'), nullable=False),
            sa.Column('master_signer_id', sa.Integer(), sa.ForeignKey('master_signers.id'), nullable=False),
            sa.Column('signing_order', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('status', sa.String(), nullable=False, server_default='pending'),
            sa.Column('token', sa.String(), nullable=True, unique=True, index=True),
            sa.Column('invited_at', sa.DateTime(), nullable=True),
            sa.Column('signed_at', sa.DateTime(), nullable=True),
            sa.Column('declined_reason', sa.Text(), nullable=True),
            sa.UniqueConstraint('version_id', 'master_signer_id', name='uq_version_master_signer'),
        )

    # ── 6. signature_fields — new columns ────────────────────────────────────
    with op.batch_alter_table('signature_fields') as batch_op:
        if not _column_exists('signature_fields', 'version_id'):
            batch_op.add_column(sa.Column('version_id', sa.Integer(), nullable=True))
        if not _column_exists('signature_fields', 'version_signer_id'):
            batch_op.add_column(sa.Column('version_signer_id', sa.Integer(), nullable=True))

    # ── 7. Data migration ─────────────────────────────────────────────────────
    conn = op.get_bind()

    # 7a. For contracts with file_path but no document_version yet, create v1
    contracts = conn.execute(sa.text(
        "SELECT id, file_path, file_type, signed_file_path, updated_at FROM contracts WHERE file_path IS NOT NULL"
    )).fetchall()

    for contract in contracts:
        existing = conn.execute(sa.text(
            "SELECT id FROM document_versions WHERE contract_id = :cid"
        ), {"cid": contract[0]}).fetchone()

        if not existing:
            conn.execute(sa.text("""
                INSERT INTO document_versions
                    (contract_id, version_number, label, file_path, signed_file_path, file_type, is_latest, created_at)
                VALUES (:cid, 1, 'Initial Upload', :fp, :sfp, :ft, 1, :ca)
            """), {
                "cid": contract[0],
                "fp": contract[1],
                "sfp": contract[3],
                "ft": contract[2] or "pdf",
                "ca": contract[4],
            })

    # 7b. Mark is_latest = TRUE for the highest version_number per contract
    conn.execute(sa.text("""
        UPDATE document_versions
        SET is_latest = 1
        WHERE id IN (
            SELECT id FROM document_versions dv1
            WHERE version_number = (
                SELECT MAX(version_number) FROM document_versions dv2
                WHERE dv2.contract_id = dv1.contract_id
            )
        )
    """))

    # 7c. Migrate existing signers → master_signers (deduplicate by email)
    old_signers = conn.execute(sa.text(
        "SELECT DISTINCT name, email FROM signers"
    )).fetchall()

    for signer in old_signers:
        existing_ms = conn.execute(sa.text(
            "SELECT id FROM master_signers WHERE email = :email"
        ), {"email": signer[1]}).fetchone()

        if not existing_ms:
            conn.execute(sa.text("""
                INSERT INTO master_signers (name, email, is_active)
                VALUES (:name, :email, 1)
            """), {"name": signer[0], "email": signer[1]})

    # 7d. For each existing contract signer, create a version_signer linked to latest version
    old_signer_rows = conn.execute(sa.text(
        "SELECT id, contract_id, email, status, signed_at FROM signers"
    )).fetchall()

    import uuid as _uuid

    for row in old_signer_rows:
        signer_id, contract_id, email, status, signed_at = row

        ms = conn.execute(sa.text(
            "SELECT id FROM master_signers WHERE email = :email"
        ), {"email": email}).fetchone()
        if not ms:
            continue

        latest_ver = conn.execute(sa.text(
            "SELECT id FROM document_versions WHERE contract_id = :cid AND is_latest = 1"
        ), {"cid": contract_id}).fetchone()
        if not latest_ver:
            continue

        already = conn.execute(sa.text(
            "SELECT id FROM version_signers WHERE version_id = :vid AND master_signer_id = :msid"
        ), {"vid": latest_ver[0], "msid": ms[0]}).fetchone()
        if already:
            continue

        vs_status = "signed" if status == "signed" else "invited"
        conn.execute(sa.text("""
            INSERT INTO version_signers
                (version_id, master_signer_id, signing_order, status, token, invited_at, signed_at)
            VALUES (:vid, :msid, 1, :st, :tok, :ia, :sa)
        """), {
            "vid": latest_ver[0],
            "msid": ms[0],
            "st": vs_status,
            "tok": str(_uuid.uuid4()),
            "ia": signed_at,
            "sa": signed_at if status == "signed" else None,
        })

    # 7e. Update signature_fields to point to version + version_signer
    sf_rows = conn.execute(sa.text(
        "SELECT id, contract_id, signer_id FROM signature_fields WHERE version_id IS NULL"
    )).fetchall()

    for sf_id, contract_id, signer_id in sf_rows:
        latest_ver = conn.execute(sa.text(
            "SELECT id FROM document_versions WHERE contract_id = :cid AND is_latest = 1"
        ), {"cid": contract_id}).fetchone()
        if not latest_ver:
            continue

        version_signer_id = None
        if signer_id:
            signer_email = conn.execute(sa.text(
                "SELECT email FROM signers WHERE id = :sid"
            ), {"sid": signer_id}).fetchone()
            if signer_email:
                ms = conn.execute(sa.text(
                    "SELECT id FROM master_signers WHERE email = :email"
                ), {"email": signer_email[0]}).fetchone()
                if ms:
                    vs = conn.execute(sa.text(
                        "SELECT id FROM version_signers WHERE version_id = :vid AND master_signer_id = :msid"
                    ), {"vid": latest_ver[0], "msid": ms[0]}).fetchone()
                    if vs:
                        version_signer_id = vs[0]

        conn.execute(sa.text("""
            UPDATE signature_fields
            SET version_id = :vid, version_signer_id = :vsid
            WHERE id = :sfid
        """), {"vid": latest_ver[0], "vsid": version_signer_id, "sfid": sf_id})

    # 7f. Generate contract numbers for existing contracts
    existing_contracts = conn.execute(sa.text(
        "SELECT id, created_at FROM contracts ORDER BY id"
    )).fetchall()

    for idx, (cid, created_at) in enumerate(existing_contracts, start=1):
        year = 2026
        if created_at:
            try:
                year = int(str(created_at)[:4])
            except Exception:
                pass
        conn.execute(sa.text(
            "UPDATE contracts SET contract_number = :cn WHERE id = :cid AND contract_number IS NULL"
        ), {"cn": f"CLM-{year}-{idx:04d}", "cid": cid})


def downgrade() -> None:
    with op.batch_alter_table('signature_fields') as batch_op:
        if _column_exists('signature_fields', 'version_signer_id'):
            batch_op.drop_column('version_signer_id')
        if _column_exists('signature_fields', 'version_id'):
            batch_op.drop_column('version_id')

    if _table_exists('version_signers'):
        op.drop_table('version_signers')

    with op.batch_alter_table('document_versions') as batch_op:
        if _column_exists('document_versions', 'is_latest'):
            batch_op.drop_column('is_latest')
        if _column_exists('document_versions', 'signed_file_path'):
            batch_op.drop_column('signed_file_path')
        if _column_exists('document_versions', 'label'):
            batch_op.drop_column('label')

    with op.batch_alter_table('contracts') as batch_op:
        if _column_exists('contracts', 'contract_number'):
            batch_op.drop_column('contract_number')

    with op.batch_alter_table('templates') as batch_op:
        if _column_exists('templates', 'is_active'):
            batch_op.drop_column('is_active')

    if _table_exists('master_signers'):
        op.drop_table('master_signers')
