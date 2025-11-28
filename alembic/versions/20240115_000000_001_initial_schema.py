"""Initial schema - users, interests, digests

Revision ID: 001
Revises: 
Create Date: 2024-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('preferred_time', sa.String(length=5), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_preferred_time', 'users', ['preferred_time'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)

    # Create interests table
    op.create_table(
        'interests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('newsapi_category', sa.String(length=50), nullable=True),
        sa.Column('newsapi_query', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_interests_slug', 'interests', ['slug'], unique=True)
    op.create_index('ix_interests_is_active', 'interests', ['is_active'], unique=False)

    # Create user_interests junction table
    op.create_table(
        'user_interests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('interest_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['interest_id'], ['interests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'interest_id', name='uq_user_interest')
    )
    op.create_index('ix_user_interests_user_id', 'user_interests', ['user_id'], unique=False)

    # Create digests table
    op.create_table(
        'digests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('digest_date', sa.Date(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=True),
        sa.Column('headlines_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('interests_included', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'digest_date', name='uq_user_digest_date')
    )
    op.create_index('ix_digests_user_id', 'digests', ['user_id'], unique=False)
    op.create_index('ix_digests_digest_date', 'digests', ['digest_date'], unique=False)
    op.create_index('ix_digests_created_at', 'digests', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('digests')
    op.drop_table('user_interests')
    op.drop_table('interests')
    op.drop_table('users')
