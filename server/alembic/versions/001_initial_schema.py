"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-11-06 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension if available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create topic table
    op.create_table('topic',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_label'), 'topic', ['label'], unique=False)

    # Create feedback table
    op.create_table('feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)

    # Create nlp_annotation table using raw SQL to handle pgvector properly
    op.execute("""
    CREATE TABLE nlp_annotation (
        id SERIAL PRIMARY KEY,
        feedback_id UUID NOT NULL REFERENCES feedback(id) ON DELETE CASCADE,
        sentiment SMALLINT NOT NULL,
        sentiment_score FLOAT NOT NULL,
        topic_id INTEGER REFERENCES topic(id),
        toxicity_score FLOAT,
        embedding vector(384)  -- Uses pgvector if available, otherwise change to bytea
    );
    """)
    op.create_index(op.f('ix_nlp_annotation_feedback_id'), 'nlp_annotation', ['feedback_id'], unique=False)
    op.create_index(op.f('ix_nlp_annotation_topic_id'), 'nlp_annotation', ['topic_id'], unique=False)

    # Create materialized view for daily aggregates
    op.execute("""
    CREATE MATERIALIZED VIEW daily_feedback_aggregates AS
    SELECT
        DATE(f.created_at) as date,
        COUNT(DISTINCT f.id) as total_feedback,
        COUNT(CASE WHEN na.sentiment = 1 THEN 1 END) as positive_count,
        COUNT(CASE WHEN na.sentiment = 0 THEN 1 END) as neutral_count,
        COUNT(CASE WHEN na.sentiment = -1 THEN 1 END) as negative_count,
        ROUND(AVG(na.sentiment_score)::numeric, 4) as avg_sentiment_score,
        ROUND(AVG(na.toxicity_score)::numeric, 4) as avg_toxicity_score,
        COUNT(DISTINCT f.customer_id) as unique_customers,
        COUNT(DISTINCT na.topic_id) as unique_topics
    FROM feedback f
    LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
    GROUP BY DATE(f.created_at)
    ORDER BY date DESC;
    """)

    # Create unique index on the materialized view
    op.create_index('idx_daily_feedback_aggregates_date', 'daily_feedback_aggregates', ['date'], unique=True)


def downgrade() -> None:
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS daily_feedback_aggregates")

    # Drop tables
    op.drop_table('nlp_annotation')
    op.drop_table('feedback')
    op.drop_table('topic')

    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
