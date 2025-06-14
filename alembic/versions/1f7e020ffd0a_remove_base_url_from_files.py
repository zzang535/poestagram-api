"""remove base_url from files

Revision ID: 1f7e020ffd0a
Revises: 5b85f84ab0d8
Create Date: 2025-06-14 13:02:15.202202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f7e020ffd0a'
down_revision: Union[str, None] = '5b85f84ab0d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""   
    op.drop_column('files', 'base_url')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('files',
        sa.Column('base_url', sa.String(length=255), nullable=True)
    )
