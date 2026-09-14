"""
Database Tests
Tests for SQLAlchemy models and database operations
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Fund, ReferencePrice, FundPosition, ReconciledPrice, MonthlyReturn
from src.database.models import Base


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# Fund Tests
# ============================================================================

class TestFundModel:
    """Test Fund model"""
    
    def test_create_fund(self, db_session):
        """Test creating a fund"""
        fund = Fund(
            fund_id="FUND_A",
            fund_name="Growth Fund",
            currency="USD"
        )
        db_session.add(fund)
        db_session.commit()
        
        # Verify
        result = db_session.query(Fund).filter(Fund.fund_id == "FUND_A").first()
        assert result is not None
        assert result.fund_name == "Growth Fund"
        assert result.currency == "USD"
        assert result.is_active is True
    
    def test_fund_unique_constraint(self, db_session):
        """Test fund_id uniqueness"""
        fund1 = Fund(fund_id="FUND_A", fund_name="Fund 1")
        fund2 = Fund(fund_id="FUND_A", fund_name="Fund 2")
        
        db_session.add(fund1)
        db_session.commit()
        
        db_session.add(fund2)
        with pytest.raises(Exception):  # Integrity error
            db_session.commit()
    
    def test_fund_timestamps(self, db_session):
        """Test fund timestamps"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        assert fund.created_at is not None
        assert fund.updated_at is not None


# ============================================================================
# Reference Price Tests
# ============================================================================

class TestReferencePriceModel:
    """Test ReferencePrice model"""
    
    def setup_method(self):
        """Setup test data"""
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def test_create_reference_price(self, db_session):
        """Test creating reference price"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        ref = ReferencePrice(
            fund_id="FUND_A",
            price_date=datetime(2024, 1, 31),
            price=Decimal("100.50")
        )
        db_session.add(ref)
        db_session.commit()
        
        result = db_session.query(ReferencePrice).filter(
            ReferencePrice.fund_id == "FUND_A"
        ).first()
        
        assert result is not None
        assert result.price == Decimal("100.50")
    
    def test_multiple_reference_prices(self, db_session):
        """Test multiple reference prices for same fund"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        prices = [
            ReferencePrice(fund_id="FUND_A", price_date=datetime(2024, 1, 15), price=Decimal("100.00")),
            ReferencePrice(fund_id="FUND_A", price_date=datetime(2024, 1, 31), price=Decimal("100.50")),
        ]
        db_session.add_all(prices)
        db_session.commit()
        
        results = db_session.query(ReferencePrice).filter(
            ReferencePrice.fund_id == "FUND_A"
        ).all()
        
        assert len(results) == 2


# ============================================================================
# Fund Position Tests
# ============================================================================

class TestFundPositionModel:
    """Test FundPosition model"""
    
    def test_create_position(self, db_session):
        """Test creating fund position"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        position = FundPosition(
            fund_id="FUND_A",
            position_date=datetime(2024, 1, 31),
            position_price=Decimal("101.50"),
            quantity=Decimal("1000"),
            value=Decimal("101500")
        )
        db_session.add(position)
        db_session.commit()
        
        result = db_session.query(FundPosition).filter(
            FundPosition.fund_id == "FUND_A"
        ).first()
        
        assert result is not None
        assert result.position_price == Decimal("101.50")
        assert result.quantity == Decimal("1000")
    
    def test_position_optional_fields(self, db_session):
        """Test position with optional fields"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        position = FundPosition(
            fund_id="FUND_A",
            position_date=datetime(2024, 1, 31),
            position_price=Decimal("101.50")
            # quantity and value are optional
        )
        db_session.add(position)
        db_session.commit()
        
        result = db_session.query(FundPosition).first()
        assert result.quantity is None
        assert result.value is None


# ============================================================================
# Reconciled Price Tests
# ============================================================================

class TestReconciledPriceModel:
    """Test ReconciledPrice model"""
    
    def test_create_reconciled_price(self, db_session):
        """Test creating reconciled price"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        reconciled = ReconciledPrice(
            fund_id="FUND_A",
            position_date=datetime(2024, 1, 31),
            position_price=Decimal("101.50"),
            reference_price=Decimal("101.50"),
            variance=Decimal("0.00"),
            variance_pct=Decimal("0.00"),
            status="EXACT_MATCH",
            is_flagged=False
        )
        db_session.add(reconciled)
        db_session.commit()
        
        result = db_session.query(ReconciledPrice).first()
        assert result.status == "EXACT_MATCH"
        assert result.is_flagged is False
    
    def test_flagged_reconciliation(self, db_session):
        """Test flagged reconciliation"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        reconciled = ReconciledPrice(
            fund_id="FUND_A",
            position_date=datetime(2024, 1, 31),
            position_price=Decimal("105.00"),
            reference_price=Decimal("101.50"),
            variance=Decimal("3.50"),
            variance_pct=Decimal("3.45"),
            status="MATCHED_HIGH_VARIANCE",
            is_flagged=True
        )
        db_session.add(reconciled)
        db_session.commit()
        
        result = db_session.query(ReconciledPrice).filter(
            ReconciledPrice.is_flagged == True
        ).first()
        
        assert result is not None
        assert result.variance_pct == Decimal("3.45")


# ============================================================================
# Monthly Return Tests
# ============================================================================

class TestMonthlyReturnModel:
    """Test MonthlyReturn model"""
    
    def test_create_monthly_return(self, db_session):
        """Test creating monthly return"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        returns = MonthlyReturn(
            fund_id="FUND_A",
            year=2024,
            month=1,
            opening_price=Decimal("100.00"),
            closing_price=Decimal("105.00"),
            monthly_return=Decimal("5.00"),
            monthly_return_pct=Decimal("5.00"),
            is_best_performer=True
        )
        db_session.add(returns)
        db_session.commit()
        
        result = db_session.query(MonthlyReturn).first()
        assert result.monthly_return_pct == Decimal("5.00")
        assert result.is_best_performer is True
    
    def test_multiple_monthly_returns(self, db_session):
        """Test multiple monthly returns"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        returns_list = [
            MonthlyReturn(
                fund_id="FUND_A", year=2024, month=1,
                opening_price=Decimal("100.00"), closing_price=Decimal("105.00"),
                monthly_return=Decimal("5.00"), monthly_return_pct=Decimal("5.00")
            ),
            MonthlyReturn(
                fund_id="FUND_A", year=2024, month=2,
                opening_price=Decimal("105.00"), closing_price=Decimal("110.00"),
                monthly_return=Decimal("5.00"), monthly_return_pct=Decimal("4.76")
            ),
        ]
        db_session.add_all(returns_list)
        db_session.commit()
        
        results = db_session.query(MonthlyReturn).filter(
            MonthlyReturn.fund_id == "FUND_A"
        ).order_by(MonthlyReturn.month).all()
        
        assert len(results) == 2
        assert results[0].month == 1
        assert results[1].month == 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestDatabaseIntegration:
    """Integration tests across models"""
    
    def test_full_reconciliation_workflow(self, db_session):
        """Test complete reconciliation workflow"""
        
        # 1. Create fund
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        # 2. Add reference prices
        ref = ReferencePrice(
            fund_id="FUND_A",
            price_date=datetime(2024, 1, 31),
            price=Decimal("100.50")
        )
        db_session.add(ref)
        db_session.commit()
        
        # 3. Add position
        position = FundPosition(
            fund_id="FUND_A",
            position_date=datetime(2024, 1, 31),
            position_price=Decimal("100.50")
        )
        db_session.add(position)
        db_session.commit()
        
        # 4. Create reconciled price
        reconciled = ReconciledPrice(
            fund_id="FUND_A",
            position_date=datetime(2024, 1, 31),
            position_price=Decimal("100.50"),
            reference_price=Decimal("100.50"),
            status="EXACT_MATCH"
        )
        db_session.add(reconciled)
        db_session.commit()
        
        # 5. Verify all records
        assert db_session.query(Fund).count() == 1
        assert db_session.query(ReferencePrice).count() == 1
        assert db_session.query(FundPosition).count() == 1
        assert db_session.query(ReconciledPrice).count() == 1
    
    def test_multiple_funds_workflow(self, db_session):
        """Test workflow with multiple funds"""
        
        # Create multiple funds
        funds_data = [
            ("FUND_A", "Growth Fund"),
            ("FUND_B", "Income Fund"),
            ("FUND_C", "Balanced Fund"),
        ]
        
        for fund_id, fund_name in funds_data:
            fund = Fund(fund_id=fund_id, fund_name=fund_name)
            db_session.add(fund)
        db_session.commit()
        
        # Add positions for each fund
        for fund_id, _ in funds_data:
            position = FundPosition(
                fund_id=fund_id,
                position_date=datetime(2024, 1, 31),
                position_price=Decimal("100.00")
            )
            db_session.add(position)
        db_session.commit()
        
        # Verify counts
        assert db_session.query(Fund).count() == 3
        assert db_session.query(FundPosition).count() == 3
        
        # Verify per-fund data
        fund_a_positions = db_session.query(FundPosition).filter(
            FundPosition.fund_id == "FUND_A"
        ).all()
        assert len(fund_a_positions) == 1


# ============================================================================
# Query Tests
# ============================================================================

class TestDatabaseQueries:
    """Test common database queries"""
    
    def test_query_by_fund_and_date(self, db_session):
        """Test querying by fund and date"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        positions = [
            FundPosition(fund_id="FUND_A", position_date=datetime(2024, 1, 15), position_price=Decimal("100.00")),
            FundPosition(fund_id="FUND_A", position_date=datetime(2024, 1, 31), position_price=Decimal("100.50")),
        ]
        db_session.add_all(positions)
        db_session.commit()
        
        result = db_session.query(FundPosition).filter(
            FundPosition.fund_id == "FUND_A",
            FundPosition.position_date == datetime(2024, 1, 31)
        ).first()
        
        assert result is not None
        assert result.position_price == Decimal("100.50")
    
    def test_query_flagged_reconciliations(self, db_session):
        """Test querying flagged reconciliations"""
        fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
        db_session.add(fund)
        db_session.commit()
        
        records = [
            ReconciledPrice(fund_id="FUND_A", position_date=datetime(2024, 1, 15),
                           position_price=Decimal("100.00"), status="EXACT_MATCH", is_flagged=False),
            ReconciledPrice(fund_id="FUND_A", position_date=datetime(2024, 1, 31),
                           position_price=Decimal("105.00"), status="MATCHED_HIGH_VARIANCE", is_flagged=True),
        ]
        db_session.add_all(records)
        db_session.commit()
        
        flagged = db_session.query(ReconciledPrice).filter(
            ReconciledPrice.is_flagged == True
        ).all()
        
        assert len(flagged) == 1
        assert flagged[0].status == "MATCHED_HIGH_VARIANCE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
