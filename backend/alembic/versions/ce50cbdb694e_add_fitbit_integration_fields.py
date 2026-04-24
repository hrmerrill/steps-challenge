"""add fitbit integration fields and multi-source constraint

Revision ID: ce50cbdb694e
Revises: fc0a468fbb9b
Create Date: 2026-04-24 09:40:00.000000

Adds preferred_step_source to users table, fitbit_refresh_token column,
and changes the daily_steps unique constraint from (user_id, date) to
(user_id, date, source) to allow multiple sources per day.
"""

from alembic import op
import sqlalchemy as sa

revision = "ce50cbdb694e"
down_revision = "fc0a468fbb9b"
branch_labels = None
depends_on = None

# Enum values for StepSource
step_source_enum = sa.Enum("manual", "garmin", "strava", "fitbit", name="stepsource")


def upgrade() -> None:
    # Add preferred_step_source to users
    op.add_column(
        "users",
        sa.Column(
            "preferred_step_source",
            step_source_enum,
            server_default="manual",
            nullable=False,
        ),
    )
    # Add fitbit_refresh_token to users
    op.add_column(
        "users",
        sa.Column("fitbit_refresh_token", sa.String(500), nullable=True),
    )

    # Change unique constraint on daily_steps: (user_id, date) → (user_id, date, source)
    op.drop_constraint("uq_user_date", "daily_steps", type_="unique")
    op.create_unique_constraint(
        "uq_user_date_source", "daily_steps", ["user_id", "date", "source"]
    )


def downgrade() -> None:
    # Revert unique constraint
    op.drop_constraint("uq_user_date_source", "daily_steps", type_="unique")
    op.create_unique_constraint("uq_user_date", "daily_steps", ["user_id", "date"])

    # Remove columns
    op.drop_column("users", "fitbit_refresh_token")
    op.drop_column("users", "preferred_step_source")
