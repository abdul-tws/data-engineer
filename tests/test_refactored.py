"""
Comprehensive Test Suite for Refactored Enterprise System
Tests core business logic and E2E functionality
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Core engine tests
from src.core import (
    ReconciliationEngine,
    PricePoint,
    Position,
    AnalyticsEngine,
    PriceSnapshot,
    CSVProcessor,
    ParsedFund
)

# CLI tests
from src.cli import CLIRunner


# ============================================================================
# Reconciliation Engine Tests
# ============================================================================

class TestReconciliationEngine:
    """Test reconciliation engine"""
    
    def setup_method(self):
        """Setup test data"""
        self.engine = ReconciliationEngine()
        
        self.position = Position(
            fund_id="FUND_A",
            date=datetime(2024, 1, 31),
            price=Decimal("101.50")
        )
        
        self.ref_prices = [
            PricePoint("FUND_A", datetime(2024, 1, 31), Decimal("101.50")),
            PricePoint("FUND_A", datetime(2024, 1, 30), Decimal("101.00")),
            PricePoint("FUND_B", datetime(2024, 1, 31), Decimal("50.00")),
        ]
    
    def test_exact_match(self):
        """Test exact price match"""
        result = self.engine.reconcile_position(self.position, self.ref_prices)
        
        assert result.status == "EXACT_MATCH"
        assert result.variance_pct < 0.01
        assert not result.is_flagged
    
    def test_minor_variance(self):
        """Test minor variance"""
        position = Position(
            fund_id="FUND_A",
            date=datetime(2024, 1, 31),
            price=Decimal("101.55")
        )
        
        result = self.engine.reconcile_position(position, self.ref_prices)
        
        assert result.status == "MATCHED_MINOR_VARIANCE"
        assert 0 < result.variance_pct < 0.1
        assert not result.is_flagged
    
    def test_high_variance(self):
        """Test high variance"""
        position = Position(
            fund_id="FUND_A",
            date=datetime(2024, 1, 31),
            price=Decimal("105.00")
        )
        
        result = self.engine.reconcile_position(position, self.ref_prices)
        
        assert "VARIANCE" in result.status
        assert result.is_flagged
    
    def test_no_reference_data(self):
        """Test when no reference data exists"""
        position = Position(
            fund_id="FUND_C",  # No reference data
            date=datetime(2024, 1, 31),
            price=Decimal("100.00")
        )
        
        result = self.engine.reconcile_position(position, self.ref_prices)
        
        assert result.status == "NO_REFERENCE_DATA"
        assert result.is_flagged
        assert result.reference_price is None
    
    def test_multiple_positions(self):
        """Test reconciling multiple positions"""
        positions = [
            Position("FUND_A", datetime(2024, 1, 31), Decimal("101.50")),
            Position("FUND_B", datetime(2024, 1, 31), Decimal("50.00")),
            Position("FUND_C", datetime(2024, 1, 31), Decimal("75.00")),
        ]
        
        results = self.engine.reconcile_positions(positions, self.ref_prices)
        
        assert len(results) == 3
        assert results[0].status == "EXACT_MATCH"
        assert results[1].status == "EXACT_MATCH"
        assert results[2].status == "NO_REFERENCE_DATA"


# ============================================================================
# Analytics Engine Tests
# ============================================================================

class TestAnalyticsEngine:
    """Test analytics engine"""
    
    def setup_method(self):
        """Setup test data"""
        self.engine = AnalyticsEngine()
    
    def test_monthly_return_calculation(self):
        """Test monthly return calculation"""
        prices = [
            PriceSnapshot("FUND_A", datetime(2024, 1, 15), Decimal("100.00")),
            PriceSnapshot("FUND_A", datetime(2024, 1, 31), Decimal("110.00")),
        ]
        
        returns = self.engine.calculate_monthly_returns("FUND_A", "Test Fund", prices)
        
        assert len(returns) == 1
        assert returns[0].opening_price == Decimal("100.00")
        assert returns[0].closing_price == Decimal("110.00")
        assert returns[0].monthly_return_pct == 10.0
    
    def test_multiple_months(self):
        """Test returns across multiple months"""
        prices = [
            # January
            PriceSnapshot("FUND_A", datetime(2024, 1, 15), Decimal("100.00")),
            PriceSnapshot("FUND_A", datetime(2024, 1, 31), Decimal("105.00")),
            # February
            PriceSnapshot("FUND_A", datetime(2024, 2, 15), Decimal("105.00")),
            PriceSnapshot("FUND_A", datetime(2024, 2, 29), Decimal("110.00")),
        ]
        
        returns = self.engine.calculate_monthly_returns("FUND_A", "Test Fund", prices)
        
        assert len(returns) == 2
        assert returns[0].month == 1
        assert returns[0].monthly_return_pct == 5.0
        assert returns[1].month == 2
        assert returns[1].monthly_return_pct == 4.761904761904762
    
    def test_best_performers(self):
        """Test identifying best performers"""
        prices = [
            PriceSnapshot("FUND_A", datetime(2024, 1, 15), Decimal("100.00")),
            PriceSnapshot("FUND_A", datetime(2024, 1, 31), Decimal("110.00")),
            PriceSnapshot("FUND_B", datetime(2024, 1, 15), Decimal("100.00")),
            PriceSnapshot("FUND_B", datetime(2024, 1, 31), Decimal("105.00")),
        ]
        
        fund_prices = {
            "FUND_A": ("Fund A", [prices[0], prices[1]]),
            "FUND_B": ("Fund B", [prices[2], prices[3]]),
        }
        
        all_returns = self.engine.calculate_all_returns(fund_prices)
        best = self.engine.get_best_performers(all_returns)
        
        assert len(best) == 1
        assert best[0].fund_id == "FUND_A"
        assert best[0].is_best_performer


# ============================================================================
# CSV Processor Tests
# ============================================================================

class TestCSVProcessor:
    """Test CSV processor"""
    
    def setup_method(self):
        """Setup test data"""
        self.processor = CSVProcessor()
    
    def test_format_a_detection(self):
        """Test Format A detection"""
        row = {
            'Fund_ID': 'FUND_A',
            'Fund_Name': 'Growth Fund',
            'Date': '2024-01-15',
            'Price': '100.50'
        }
        
        fmt = self.processor._detect_format(row)
        assert fmt == self.processor.FORMAT_A
    
    def test_format_b_detection(self):
        """Test Format B detection"""
        row = {
            'FundCode': 'FUND_A',
            'FundName': 'Growth Fund',
            'TradeDate': '2024-01-15',
            'Value': '50000'
        }
        
        fmt = self.processor._detect_format(row)
        assert fmt == self.processor.FORMAT_B
    
    def test_date_parsing_iso(self):
        """Test ISO date parsing"""
        date = self.processor._parse_date("2024-01-15")
        assert date == datetime(2024, 1, 15)
    
    def test_date_parsing_various_formats(self):
        """Test various date formats"""
        dates = [
            ("2024-01-15", datetime(2024, 1, 15)),
            ("15-01-2024", datetime(2024, 1, 15)),
            ("01/15/2024", datetime(2024, 1, 15)),
        ]
        
        for date_str, expected in dates:
            parsed = self.processor._parse_date(date_str)
            assert parsed == expected
    
    def test_decimal_parsing(self):
        """Test decimal parsing"""
        test_cases = [
            ("100.50", Decimal("100.50")),
            ("1000.5", Decimal("1000.5")),
            ("1,000.50", Decimal("1000.50")),
            ("$100.50", Decimal("100.50")),
        ]
        
        for value_str, expected in test_cases:
            parsed = self.processor._parse_decimal(value_str)
            assert parsed == expected
    
    def test_process_format_a_csv(self):
        """Test processing Format A CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Fund_ID,Fund_Name,Date,Price,Quantity,Value\n")
            f.write("FUND_A,Growth Fund,2024-01-15,100.50,1000,100500\n")
            f.write("FUND_B,Income Fund,2024-01-15,50.75,2000,101500\n")
            f.flush()
            
            path = Path(f.name)
            parsed = self.processor.process_file(path)
            
            assert len(parsed) == 2
            assert parsed[0].fund_id == "FUND_A"
            assert parsed[0].price == Decimal("100.50")
            assert parsed[1].fund_id == "FUND_B"
            
            path.unlink()


# ============================================================================
# CLI Runner Tests
# ============================================================================

class TestCLIRunner:
    """Test CLI runner"""
    
    def test_initialization(self):
        """Test CLI runner initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CLIRunner(
                data_dir=Path(tmpdir) / "data",
                output_dir=Path(tmpdir) / "output"
            )
            
            assert runner.reconciliation_engine is not None
            assert runner.analytics_engine is not None
            assert runner.csv_processor is not None
            assert (Path(tmpdir) / "data").exists()
            assert (Path(tmpdir) / "output").exists()
    
    def test_empty_workflow(self):
        """Test workflow with no data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CLIRunner(
                data_dir=Path(tmpdir) / "data",
                output_dir=Path(tmpdir) / "output"
            )
            
            summary = runner.run_full_workflow(verbose=False)
            
            assert "status" in summary or "data_loaded" in summary
    
    def test_summary_generation(self):
        """Test summary generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CLIRunner(
                data_dir=Path(tmpdir) / "data",
                output_dir=Path(tmpdir) / "output"
            )
            
            # Add some test data
            runner.positions = [
                Position("FUND_A", datetime(2024, 1, 31), Decimal("100.00")),
            ]
            runner.reference_prices = [
                PricePoint("FUND_A", datetime(2024, 1, 31), Decimal("100.00")),
            ]
            runner.reconciliation_results = [
                # Would be populated by reconciliation
            ]
            
            summary = runner._get_summary()
            
            assert "timestamp" in summary
            assert "data_loaded" in summary
            assert summary["data_loaded"]["positions"] == 1
            assert summary["data_loaded"]["reference_prices"] == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow_with_data(self):
        """Test complete workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create data directory with CSV
            data_dir = tmpdir / "data"
            send_dir = data_dir / "Send_data"
            send_dir.mkdir(parents=True)
            
            # Write sample CSV
            csv_file = send_dir / "sample.csv"
            with open(csv_file, 'w') as f:
                f.write("Fund_ID,Fund_Name,Date,Price,Quantity,Value\n")
                f.write("FUND_A,Growth Fund,2024-01-31,100.50,1000,100500\n")
                f.write("FUND_B,Income Fund,2024-01-31,50.75,2000,101500\n")
            
            # Write reference prices
            ref_file = data_dir / "reference_prices.sql"
            with open(ref_file, 'w') as f:
                f.write("INSERT INTO reference_prices (fund_id, price_date, price) VALUES ('FUND_A', '2024-01-31', 100.50);\n")
                f.write("INSERT INTO reference_prices (fund_id, price_date, price) VALUES ('FUND_B', '2024-01-31', 50.75);\n")
            
            # Run workflow
            runner = CLIRunner(data_dir=data_dir, output_dir=tmpdir / "output")
            summary = runner.run_full_workflow(verbose=False)
            
            assert "data_loaded" in summary
            assert summary["data_loaded"]["positions"] == 2
            assert summary["data_loaded"]["reference_prices"] == 2


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests"""
    
    def test_reconciliation_performance(self):
        """Test reconciliation performance with many records"""
        engine = ReconciliationEngine()
        
        # Create 1000 positions
        positions = [
            Position(
                f"FUND_{i % 10}",
                datetime(2024, 1, 31),
                Decimal(str(100 + i % 50))
            )
            for i in range(1000)
        ]
        
        # Create reference prices
        refs = [
            PricePoint(
                f"FUND_{i}",
                datetime(2024, 1, 31),
                Decimal("100.00")
            )
            for i in range(10)
        ]
        
        # Reconcile (should be fast)
        import time
        start = time.time()
        results = engine.reconcile_positions(positions, refs)
        elapsed = time.time() - start
        
        assert len(results) == 1000
        assert elapsed < 1.0  # Should complete in under 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
