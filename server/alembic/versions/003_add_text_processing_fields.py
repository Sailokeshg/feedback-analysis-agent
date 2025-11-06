"""Add text processing fields

Revision ID: 003
Revises: 002
Create Date: 2024-11-06 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add normalized_text and detected_language columns to feedback table
    op.add_column('feedback', sa.Column('normalized_text', sa.Text(), nullable=True))
    op.add_column('feedback', sa.Column('detected_language', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('feedback', 'detected_language')
    op.drop_column('feedback', 'normalized_text')
