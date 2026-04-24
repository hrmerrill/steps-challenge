"""rename fitbit to google_health (no-op)

Revision ID: a1b2c3d4e5f6
Revises: ce50cbdb694e
Create Date: 2026-04-24 11:00:00.000000

Originally renamed Fitbit-specific columns and enum values to Google
Health API. This work has been consolidated into the previous migration
(ce50cbdb694e) which now creates google_health columns directly, since
the intermediate fitbit column names were never applied in production.

This migration is kept as a no-op to preserve the Alembic revision chain.
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "ce50cbdb694e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All work consolidated into ce50cbdb694e. Nothing to do.
    pass


def downgrade() -> None:
    # Nothing to revert.
    pass
