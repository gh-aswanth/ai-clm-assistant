"""sync_models

Revision ID: 359680a19941
Revises: f2a3b4c5d6e7
Create Date: 2026-03-26 12:32:34.503448

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '359680a19941'
down_revision: Union[str, Sequence[str], None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: DB indexes were already applied by the seed migration."""
    pass


def downgrade() -> None:
    pass
