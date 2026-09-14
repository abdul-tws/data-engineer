"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # Create funds table
    op.create_table(
        'funds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.String(50), nullable=False),
        sa.Column('fund_name', sa.String(255), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fund_id', name='uq_fund_id')
    )
    op.create_index('idx_fund_id', 'funds', ['fund_id'])
    
    # Create reference_prices table
    op.create_table(
        'reference_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.String(50), nullable=False),
        sa.Column('price_date', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Numeric(18, 6), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.fund_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fund_price_date', 'reference_prices', ['fund_id', 'price_date'])
    
    # Create fund_positions table
    op.create_table(
        'fund_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.String(50), nullable=False),
        sa.Column('position_date', sa.DateTime(), nullable=False),
        sa.Column('position_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 6), nullable=True),
        sa.Column('value', sa.Numeric(18, 6), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='csv'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.fund_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fund_position_date', 'fund_positions', ['fund_id', 'position_date'])
    
    # Create reconciled_prices table
    op.create_table(
        'reconciled_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.String(50), nullable=False),
        sa.Column('position_date', sa.DateTime(), nullable=False),
        sa.Column('position_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('reference_price', sa.Numeric(18, 6), nullable=True),
        sa.Column('variance', sa.Numeric(18, 6), nullable=True),
        sa.Column('variance_pct', sa.Numeric(10, 4), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.fund_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fund_status', 'reconciled_prices', ['fund_id', 'status'])
    
    # Create monthly_returns table
    op.create_table(
        'monthly_returns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fund_id', sa.String(50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('opening_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('closing_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('monthly_return', sa.Numeric(18, 6), nullable=False),
        sa.Column('monthly_return_pct', sa.Numeric(10, 4), nullable=False),
        sa.Column('is_best_performer', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['fund_id'], ['funds.fund_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_fund_year_month', 'monthly_returns', ['fund_id', 'year', 'month'])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_index('idx_fund_year_month', table_name='monthly_returns')
    op.drop_table('monthly_returns')
    op.drop_index('idx_fund_status', table_name='reconciled_prices')
    op.drop_table('reconciled_prices')
    op.drop_index('idx_fund_position_date', table_name='fund_positions')
    op.drop_table('fund_positions')
    op.drop_index('idx_fund_price_date', table_name='reference_prices')
    op.drop_table('reference_prices')
    op.drop_index('idx_fund_id', table_name='funds')
    op.drop_table('funds')
