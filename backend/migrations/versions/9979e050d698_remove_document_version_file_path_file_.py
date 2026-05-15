"""remove_document_version_file_path_file_type

Revision ID: 9979e050d698
Revises: 802d370c2e6d
Create Date: 2026-03-30 17:48:10.309711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9979e050d698'
down_revision: Union[str, Sequence[str], None] = '802d370c2e6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # compliance_records — recreate FK with explicit name
    with op.batch_alter_table('compliance_records') as batch_op:
        batch_op.create_foreign_key('fk_compliance_records_contract_id', 'contracts', ['contract_id'], ['id'])

    # document_chunks — add file_id, drop old columns/indexes, add new FK
    with op.batch_alter_table('document_chunks') as batch_op:
        batch_op.add_column(sa.Column('file_id', sa.Integer(), nullable=True))
        batch_op.drop_index('ix_document_chunks_document_version_id')
        batch_op.drop_index('ix_document_chunks_drive_file_id')
        batch_op.create_index('ix_document_chunks_file_id', ['file_id'], unique=False)
        batch_op.create_foreign_key('fk_document_chunks_file_id', 'files', ['file_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_column('drive_file_id')
        batch_op.drop_column('document_version_id')

    # document_drive_files — add file_id, drop file_path
    with op.batch_alter_table('document_drive_files') as batch_op:
        batch_op.add_column(sa.Column('file_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_document_drive_files_file_id', ['file_id'], unique=False)
        batch_op.create_foreign_key('fk_document_drive_files_file_id', 'files', ['file_id'], ['id'])
        batch_op.drop_column('file_path')

    # document_versions — add file_id, drop file_path & file_type
    with op.batch_alter_table('document_versions') as batch_op:
        batch_op.add_column(sa.Column('file_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_document_versions_file_id', ['file_id'], unique=False)
        batch_op.create_foreign_key('fk_document_versions_file_id', 'files', ['file_id'], ['id'])
        batch_op.drop_column('file_type')
        batch_op.drop_column('file_path')


def downgrade() -> None:
    # document_versions
    with op.batch_alter_table('document_versions') as batch_op:
        batch_op.add_column(sa.Column('file_path', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('file_type', sa.VARCHAR(), nullable=True))
        batch_op.drop_constraint('fk_document_versions_file_id', type_='foreignkey')
        batch_op.drop_index('ix_document_versions_file_id')
        batch_op.drop_column('file_id')

    # document_drive_files
    with op.batch_alter_table('document_drive_files') as batch_op:
        batch_op.add_column(sa.Column('file_path', sa.VARCHAR(), nullable=True))
        batch_op.drop_constraint('fk_document_drive_files_file_id', type_='foreignkey')
        batch_op.drop_index('ix_document_drive_files_file_id')
        batch_op.drop_column('file_id')

    # document_chunks
    with op.batch_alter_table('document_chunks') as batch_op:
        batch_op.add_column(sa.Column('document_version_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('drive_file_id', sa.INTEGER(), nullable=True))
        batch_op.drop_constraint('fk_document_chunks_file_id', type_='foreignkey')
        batch_op.create_foreign_key('fk_document_chunks_document_version_id', 'document_versions', ['document_version_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_document_chunks_drive_file_id', 'document_drive_files', ['drive_file_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_index('ix_document_chunks_file_id')
        batch_op.create_index('ix_document_chunks_drive_file_id', ['drive_file_id'], unique=False)
        batch_op.create_index('ix_document_chunks_document_version_id', ['document_version_id'], unique=False)
        batch_op.drop_column('file_id')

    # compliance_records
    with op.batch_alter_table('compliance_records') as batch_op:
        batch_op.drop_constraint('fk_compliance_records_contract_id', type_='foreignkey')
        batch_op.create_foreign_key('fk_compliance_records_contract_id_cascade', 'contracts', ['contract_id'], ['id'], ondelete='CASCADE')
