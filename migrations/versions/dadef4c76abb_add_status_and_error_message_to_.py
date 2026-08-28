"""add status and error_message to documents

Revision ID: dadef4c76abb
Revises: 849b4cbf882d
Create Date: 2026-08-27 21:36:54.070696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dadef4c76abb'
down_revision: Union[str, Sequence[str], None] = '849b4cbf882d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('documents', sa.Column('status', sa.String(length=20), server_default='completed', nullable=False))
    op.add_column('documents', sa.Column('error_message', sa.Text(), nullable=True))
    op.alter_column('documents', 'status', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'error_message')
    op.drop_column('documents', 'status')
