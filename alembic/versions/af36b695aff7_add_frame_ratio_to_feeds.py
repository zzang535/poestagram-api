"""add_frame_ratio_to_feeds

Revision ID: af36b695aff7
Revises: 8ee0ea1f1910
Create Date: 2025-04-19 21:54:35.931839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af36b695aff7'
down_revision: Union[str, None] = '8ee0ea1f1910'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('feeds', sa.Column('frame_ratio', sa.Float(), nullable=False, server_default='1.0'))
    op.create_check_constraint(
        'frame_ratio_range',
        'feeds',
        sa.and_(
            sa.column('frame_ratio') >= 0.54,
            sa.column('frame_ratio') <= 1.25
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('frame_ratio_range', 'feeds', type_='check')
    op.drop_column('feeds', 'frame_ratio')
