"""
SQLAlchemy ORM Models
Database schema definitions
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Fund(Base):
    """Fund master data"""
    __tablename__ = "funds"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(String(50), unique=True, index=True, nullable=False)
    fund_name = Column(String(255), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fund_id', 'fund_id'),
    )


class ReferencePrice(Base):
    """Reference prices for funds"""
    __tablename__ = "reference_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(String(50), ForeignKey('funds.fund_id'), nullable=False, index=True)
    price_date = Column(DateTime, nullable=False)
    price = Column(Numeric(18, 6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fund_price_date', 'fund_id', 'price_date'),
    )


class FundPosition(Base):
    """Fund positions from CSVs"""
    __tablename__ = "fund_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(String(50), ForeignKey('funds.fund_id'), nullable=False, index=True)
    position_date = Column(DateTime, nullable=False)
    position_price = Column(Numeric(18, 6), nullable=False)
    quantity = Column(Numeric(18, 6), nullable=True)
    value = Column(Numeric(18, 6), nullable=True)
    source = Column(String(50), default="csv", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fund_position_date', 'fund_id', 'position_date'),
    )


class ReconciledPrice(Base):
    """Reconciliation results"""
    __tablename__ = "reconciled_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(String(50), ForeignKey('funds.fund_id'), nullable=False, index=True)
    position_date = Column(DateTime, nullable=False)
    position_price = Column(Numeric(18, 6), nullable=False)
    reference_price = Column(Numeric(18, 6), nullable=True)
    variance = Column(Numeric(18, 6), nullable=True)
    variance_pct = Column(Numeric(10, 4), nullable=True)
    status = Column(String(50), nullable=False)
    is_flagged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fund_status', 'fund_id', 'status'),
    )


class MonthlyReturn(Base):
    """Monthly fund returns"""
    __tablename__ = "monthly_returns"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(String(50), ForeignKey('funds.fund_id'), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    opening_price = Column(Numeric(18, 6), nullable=False)
    closing_price = Column(Numeric(18, 6), nullable=False)
    monthly_return = Column(Numeric(18, 6), nullable=False)
    monthly_return_pct = Column(Numeric(10, 4), nullable=False)
    is_best_performer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fund_year_month', 'fund_id', 'year', 'month'),
    )
