"""add_analysis_and_transaction_tables

Revision ID: 751f9c4c31d3
Revises: a609c4c67f13
Create Date: 2025-12-08 21:43:11.275862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '751f9c4c31d3'
down_revision: Union[str, None] = 'a609c4c67f13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add credits_balance column to user table
    op.add_column('user', sa.Column('credits_balance', sa.Integer(), nullable=False, server_default='100'))

    # Create analysis table
    op.create_table(
        'analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('original_response', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('models_used', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='analysisstatus'), nullable=False),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('credits_used', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_user_id'), 'analysis', ['user_id'], unique=False)

    # Create transaction table
    op.create_table(
        'transaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('purchase', 'usage', 'refund', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaction_user_id'), 'transaction', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transaction_user_id'), table_name='transaction')
    op.drop_table('transaction')
    op.drop_index(op.f('ix_analysis_user_id'), table_name='analysis')
    op.drop_table('analysis')
    op.drop_column('user', 'credits_balance')
