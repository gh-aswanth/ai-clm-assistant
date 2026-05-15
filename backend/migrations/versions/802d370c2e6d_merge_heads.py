"""merge_heads

Revision ID: 802d370c2e6d
Revises: 085938aef0a3, 114d69312450
Create Date: 2026-03-30 17:40:39.147924

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '802d370c2e6d'
down_revision: Union[str, Sequence[str], None] = ('085938aef0a3', '114d69312450')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
