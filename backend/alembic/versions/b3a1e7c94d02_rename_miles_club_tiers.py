"""rename miles club tiers to daily step ranges

Revision ID: b3a1e7c94d02
Revises: 9f07556743a1
Create Date: 2026-04-15 22:45:00.000000

Replaces GOLD/SILVER/BRONZE/NONE with HIGH/MID/LOW/NONE.
Tier assignment now based on average daily steps instead of monthly totals.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3a1e7c94d02"
down_revision: Union[str, None] = "9f07556743a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Convert to text first — avoids the "new enum values must be
        # committed before they can be used" transaction restriction.
        op.execute(
            "ALTER TABLE challenge_participants "
            "ALTER COLUMN miles_club_tier TYPE VARCHAR USING miles_club_tier::text"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'HIGH' WHERE miles_club_tier = 'GOLD'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'MID' WHERE miles_club_tier = 'SILVER'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'LOW' WHERE miles_club_tier = 'BRONZE'"
        )
        # Recreate enum with new values and convert column back
        op.execute("DROP TYPE IF EXISTS milesclubtier")
        op.execute("CREATE TYPE milesclubtier AS ENUM ('HIGH', 'MID', 'LOW', 'NONE')")
        op.execute(
            "ALTER TABLE challenge_participants "
            "ALTER COLUMN miles_club_tier TYPE milesclubtier USING miles_club_tier::milesclubtier"
        )
    else:
        # SQLite: simple string update
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'HIGH' WHERE miles_club_tier = 'GOLD'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'MID' WHERE miles_club_tier = 'SILVER'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'LOW' WHERE miles_club_tier = 'BRONZE'"
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(
            "ALTER TABLE challenge_participants "
            "ALTER COLUMN miles_club_tier TYPE VARCHAR USING miles_club_tier::text"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'GOLD' WHERE miles_club_tier = 'HIGH'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'SILVER' WHERE miles_club_tier = 'MID'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'BRONZE' WHERE miles_club_tier = 'LOW'"
        )
        op.execute("DROP TYPE IF EXISTS milesclubtier")
        op.execute("CREATE TYPE milesclubtier AS ENUM ('GOLD', 'SILVER', 'BRONZE', 'NONE')")
        op.execute(
            "ALTER TABLE challenge_participants "
            "ALTER COLUMN miles_club_tier TYPE milesclubtier USING miles_club_tier::milesclubtier"
        )
    else:
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'GOLD' WHERE miles_club_tier = 'HIGH'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'SILVER' WHERE miles_club_tier = 'MID'"
        )
        op.execute(
            "UPDATE challenge_participants SET miles_club_tier = 'BRONZE' WHERE miles_club_tier = 'LOW'"
        )
