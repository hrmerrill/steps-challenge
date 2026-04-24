"""add google health integration fields and multi-source constraint

Revision ID: ce50cbdb694e
Revises: fc0a468fbb9b
Create Date: 2026-04-24 09:40:00.000000

Adds preferred_step_source and google_health_refresh_token to users,
renames fitbit_token → google_health_token, adds 'google_health' to
the stepsource enum, and changes the daily_steps unique constraint from
(user_id, date) to (user_id, date, source) to allow multiple sources
per day.

Note: the original version of this migration created intermediate
"fitbit" column names that were immediately renamed in the next
migration (a1b2c3d4e5f6). Since the fitbit migration was never applied
in production, this consolidated version skips the intermediate state
and creates the final google_health columns directly.
"""

from alembic import op
import sqlalchemy as sa

revision = "ce50cbdb694e"
down_revision = "fc0a468fbb9b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # PostgreSQL: ALTER TYPE ... ADD VALUE cannot run inside a transaction.
        # Commit the current transaction, add the value, then re-open.
        op.execute("COMMIT")
        op.execute("ALTER TYPE stepsource ADD VALUE IF NOT EXISTS 'google_health'")
        op.execute("BEGIN")

    # Rename fitbit_token → google_health_token (column exists from initial schema)
    op.alter_column("users", "fitbit_token", new_column_name="google_health_token")

    # Add google_health_refresh_token (new column)
    op.add_column(
        "users",
        sa.Column("google_health_refresh_token", sa.String(500), nullable=True),
    )

    # Add preferred_step_source — use the existing stepsource enum (don't recreate)
    existing_enum = sa.Enum(
        "manual", "garmin", "strava", "google_health",
        name="stepsource", create_type=False,
    )
    op.add_column(
        "users",
        sa.Column(
            "preferred_step_source",
            existing_enum,
            server_default="manual",
            nullable=False,
        ),
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
    op.drop_column("users", "preferred_step_source")
    op.drop_column("users", "google_health_refresh_token")

    # Rename back
    op.alter_column("users", "google_health_token", new_column_name="fitbit_token")

    # Note: PostgreSQL does not support removing enum values.
    # 'google_health' will remain in the stepsource enum after downgrade.
