"""Add files table

Revision ID: ea96ce3c9b6e
Revises: 6faccb00fb91
Create Date: 2025-04-08 20:42:41.198430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea96ce3c9b6e'
down_revision: Union[str, None] = '6faccb00fb91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_name', sa.String(255), nullable=False),
    sa.Column('file_path', sa.String(255), nullable=False),
    sa.Column('file_type', sa.String(100), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_files_id'), table_name='files')
    op.drop_table('files')
    # ### end Alembic commands ###
