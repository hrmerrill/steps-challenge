"""rename fitbit to google_health

Revision ID: a1b2c3d4e5f6
Revises: ce50cbdb694e
Create Date: 2026-04-24 11:00:00.000000

Renames Fitbit-specific columns and enum values to Google Health API,
reflecting the migration from the deprecated Fitbit Web API (sunsetting
September 2026) to the Google Health API.
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "ce50cbdb694e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename user columns: fitbit_token → google_health_token
    op.alter_column("users", "fitbit_token", new_column_name="google_health_token")
    op.alter_column("users", "fitbit_refresh_token", new_column_name="google_health_refresh_token")

    # Add new enum value 'google_health' to stepsource
    # (PostgreSQL requires ALTER TYPE; SQLite ignores enum types)
    op.execute("ALTER TYPE stepsource ADD VALUE IF NOT EXISTS 'google_health'")

    # Update existing rows that used 'fitbit' source to 'google_health'
    op.execute("UPDATE daily_steps SET source = 'google_health' WHERE source = 'fitbit'")
    op.execute("UPDATE users SET preferred_step_source = 'google_health' WHERE preferred_step_source = 'fitbit'")


def downgrade() -> None:
    # Revert data
    op.execute("UPDATE daily_steps SET source = 'fitbit' WHERE source = 'google_health'")
    op.execute("UPDATE users SET preferred_step_source = 'fitbit' WHERE preferred_step_source = 'google_health'")

    # Rename columns back
    op.alter_column("users", "google_health_token", new_column_name="fitbit_token")
    op.alter_column("users", "google_health_refresh_token", new_column_name="fitbit_refresh_token")

    # Note: PostgreSQL does not support removing enum values.
    # 'google_health' will remain in the enum type after downgrade.
