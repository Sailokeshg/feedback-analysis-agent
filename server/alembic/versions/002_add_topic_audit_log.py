"""Add topic audit log table

Revision ID: 002
Revises: 001
Create Date: 2024-11-06 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create topic_audit_log table
    op.create_table('topic_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('old_label', sa.String(), nullable=True),
        sa.Column('new_label', sa.String(), nullable=True),
        sa.Column('old_keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('new_keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('changed_by', sa.String(), nullable=False),
        sa.Column('changed_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topic.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_audit_log_topic_id'), 'topic_audit_log', ['topic_id'], unique=False)
    op.create_index(op.f('ix_topic_audit_log_changed_at'), 'topic_audit_log', ['changed_at'], unique=False)


def downgrade() -> None:
    # Drop topic_audit_log table
    op.drop_index(op.f('ix_topic_audit_log_changed_at'), table_name='topic_audit_log')
    op.drop_index(op.f('ix_topic_audit_log_topic_id'), table_name='topic_audit_log')
    op.drop_table('topic_audit_log')
