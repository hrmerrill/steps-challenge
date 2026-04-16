"""add profile_photo_url to users

Revision ID: 227d93f0d934
Revises: b3a1e7c94d02
Create Date: 2026-04-16 08:36:47.006669
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '227d93f0d934'
down_revision: Union[str, None] = 'b3a1e7c94d02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('profile_photo_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'profile_photo_url')
