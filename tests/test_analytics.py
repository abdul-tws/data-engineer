"""
Unit Tests for Analytics Module
Tests monthly return calculations and performance identification
"""

import unittest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import DatabaseManager
from analytics import AnalyticsCalculator


class TestMonthlyReturnCalculation(unittest.TestCase):
    """Test monthly return calculations"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.analytics = AnalyticsCalculator(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_positive_monthly_return(self):
        """Test positive monthly return calculation"""
        # Insert opening and closing prices
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 105.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns[0]['opening_price'], 100.00)
        self.assertEqual(returns[0]['closing_price'], 105.00)
        self.assertEqual(returns[0]['monthly_return'], 5.00)
        self.assertAlmostEqual(returns[0]['monthly_return_pct'], 5.0, places=2)
    
    def test_negative_monthly_return(self):
        """Test negative monthly return calculation"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 95.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns[0]['monthly_return'], -5.00)
        self.assertAlmostEqual(returns[0]['monthly_return_pct'], -5.0, places=2)
    
    def test_zero_monthly_return(self):
        """Test zero monthly return"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 100.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns[0]['monthly_return'], 0.0)
        self.assertEqual(returns[0]['monthly_return_pct'], 0.0)
    
    def test_single_price_no_return(self):
        """Test that single price entry doesn't create return"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-15', 100.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        # Should not calculate return with only one price
        self.assertEqual(len(returns), 0)
    
    def test_multiple_funds_monthly_returns(self):
        """Test returns for multiple funds in same month"""
        # Fund A
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 102.00)
        
        # Fund B
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-05', 50.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-31', 51.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 2)
    
    def test_multiple_months_returns(self):
        """Test returns across multiple months"""
        # Month 1
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 102.00)
        
        # Month 2
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-02-05', 102.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-02-29', 105.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 2)
        self.assertEqual(returns[0]['month'], 1)
        self.assertEqual(returns[1]['month'], 2)


class TestBestPerformerIdentification(unittest.TestCase):
    """Test identification of best performing funds"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.analytics = AnalyticsCalculator(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_single_fund_best_performer(self):
        """Test best performer with single fund"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 105.00)
        
        self.analytics.calculate_monthly_returns()
        best = self.analytics.identify_best_performers()
        
        self.assertEqual(len(best), 1)
        self.assertEqual(best[0]['fund_id'], 'FUND_A')
        self.assertAlmostEqual(best[0]['monthly_return_pct'], 5.0, places=2)
    
    def test_multiple_funds_best_performer(self):
        """Test identifying best performer among multiple funds"""
        # Fund A: 2% return
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 102.00)
        
        # Fund B: 5% return (best)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-31', 105.00)
        
        # Fund C: 3% return
        self.db_manager.insert_fund_position('FUND_C', 'Fund C', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_C', 'Fund C', '2024-01-31', 103.00)
        
        self.analytics.calculate_monthly_returns()
        best = self.analytics.identify_best_performers()
        
        # Should identify Fund B as best
        self.assertEqual(len(best), 1)
        self.assertEqual(best[0]['fund_id'], 'FUND_B')
    
    def test_negative_returns_best_performer(self):
        """Test best performer selection with negative returns"""
        # Fund A: -5% return
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 95.00)
        
        # Fund B: -2% return (best)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-31', 98.00)
        
        self.analytics.calculate_monthly_returns()
        best = self.analytics.identify_best_performers()
        
        # Fund B should be best (least negative)
        self.assertEqual(best[0]['fund_id'], 'FUND_B')
    
    def test_best_performer_multiple_months(self):
        """Test best performer across multiple months"""
        # January: Fund A wins
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 105.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-31', 103.00)
        
        # February: Fund B wins
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-02-05', 105.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-02-29', 106.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-02-05', 103.00)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-02-29', 108.00)
        
        self.analytics.calculate_monthly_returns()
        best = self.analytics.identify_best_performers()
        
        self.assertEqual(len(best), 2)
        self.assertEqual(best[0]['month'], 1)
        self.assertEqual(best[0]['fund_id'], 'FUND_A')
        self.assertEqual(best[1]['month'], 2)
        self.assertEqual(best[1]['fund_id'], 'FUND_B')


class TestMonthLabelGeneration(unittest.TestCase):
    """Test month label generation"""
    
    def test_month_label_january(self):
        """Test January label"""
        label = AnalyticsCalculator._get_month_label(2024, 1)
        self.assertEqual(label, 'January 2024')
    
    def test_month_label_december(self):
        """Test December label"""
        label = AnalyticsCalculator._get_month_label(2024, 12)
        self.assertEqual(label, 'December 2024')
    
    def test_month_label_all_months(self):
        """Test all month labels"""
        expected_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        for month in range(1, 13):
            label = AnalyticsCalculator._get_month_label(2024, month)
            self.assertIn(expected_names[month-1], label)
            self.assertIn('2024', label)


class TestEdgeCasesAnalytics(unittest.TestCase):
    """Test edge cases in analytics"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.analytics = AnalyticsCalculator(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_very_small_return(self):
        """Test calculation of very small returns"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 100.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 100.001)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 1)
        self.assertGreater(returns[0]['monthly_return_pct'], 0)
        self.assertLessEqual(returns[0]['monthly_return_pct'], 0.002)  # Allow for floating point precision
    
    def test_very_large_return(self):
        """Test calculation of very large returns"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-05', 10.00)
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 1000.00)
        
        returns = self.analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 1)
        self.assertAlmostEqual(returns[0]['monthly_return_pct'], 9900.0, places=0)
    
    def test_no_positions(self):
        """Test with no fund positions"""
        returns = self.analytics.calculate_monthly_returns()
        self.assertEqual(len(returns), 0)
        
        best = self.analytics.identify_best_performers()
        self.assertEqual(len(best), 0)


if __name__ == '__main__':
    unittest.main()
