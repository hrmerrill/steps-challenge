"""add description to challenges

Revision ID: 9f07556743a1
Revises: 
Create Date: 2026-04-15 17:59:30.792969

This is a combined initial + incremental migration. It creates all tables
if they don't exist (fresh install), OR just adds the description column
if the tables already exist (existing production DB).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '9f07556743a1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if "challenges" not in existing_tables:
        # Fresh install — create all tables
        op.create_table('challenges',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.String(length=5000), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('end_date', sa.Date(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table('users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('display_name', sa.String(length=100), nullable=False),
            sa.Column('garmin_token', sa.String(length=500), nullable=True),
            sa.Column('strava_token', sa.String(length=500), nullable=True),
            sa.Column('fitbit_token', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_table('challenge_participants',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('challenge_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('miles_club_tier', sa.Enum('GOLD', 'SILVER', 'BRONZE', 'NONE', name='milesclubtier'), nullable=False),
            sa.ForeignKeyConstraint(['challenge_id'], ['challenges.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('challenge_id', 'user_id', name='uq_challenge_user')
        )
        op.create_index(op.f('ix_challenge_participants_challenge_id'), 'challenge_participants', ['challenge_id'], unique=False)
        op.create_index(op.f('ix_challenge_participants_user_id'), 'challenge_participants', ['user_id'], unique=False)
        op.create_table('daily_steps',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('step_count', sa.Integer(), nullable=False),
            sa.Column('source', sa.Enum('manual', 'garmin', 'strava', 'google_health', name='stepsource'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'date', name='uq_user_date')
        )
        op.create_index(op.f('ix_daily_steps_date'), 'daily_steps', ['date'], unique=False)
        op.create_index(op.f('ix_daily_steps_user_id'), 'daily_steps', ['user_id'], unique=False)
    else:
        # Existing DB — just add the description column if missing
        columns = [c["name"] for c in inspector.get_columns("challenges")]
        if "description" not in columns:
            op.add_column('challenges', sa.Column('description', sa.String(length=5000), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if "daily_steps" in existing_tables:
        columns = [c["name"] for c in inspector.get_columns("challenges")]
        if "description" in columns:
            op.drop_column('challenges', 'description')
