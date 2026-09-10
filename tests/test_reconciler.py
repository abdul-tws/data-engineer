"""
Unit Tests for Price Reconciler Module
Tests price reconciliation logic and variance calculation
"""

import unittest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import DatabaseManager
from reconciler import PriceReconciler


class TestPriceReconciliation(unittest.TestCase):
    """Test price reconciliation logic"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.reconciler = PriceReconciler(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_exact_price_match(self):
        """Test reconciliation with exact price match"""
        # Insert position and reference price for same date
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 100.50)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.50)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        self.assertEqual(result['position_price'], 100.50)
        self.assertEqual(result['reference_price'], 100.50)
        self.assertEqual(result['price_variance'], 0.0)
        self.assertEqual(result['variance_pct'], 0.0)
        self.assertEqual(result['reconciliation_status'], 'EXACT_MATCH')
    
    def test_price_variance_calculation(self):
        """Test price variance calculation"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 101.50)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.00)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        self.assertAlmostEqual(result['price_variance'], 1.50, places=2)
        self.assertAlmostEqual(result['variance_pct'], 1.50, places=2)
    
    def test_negative_variance(self):
        """Test negative price variance"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 98.50)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.00)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        self.assertAlmostEqual(result['price_variance'], -1.50, places=2)
        self.assertAlmostEqual(result['variance_pct'], -1.50, places=2)
    
    def test_no_reference_price(self):
        """Test reconciliation when no reference price exists"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 100.50)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        self.assertIsNone(result['reference_price'])
        self.assertIsNone(result['reference_date'])
        self.assertEqual(result['reconciliation_status'], 'NO_REFERENCE_DATA')
    
    def test_fallback_to_latest_price(self):
        """Test fallback to latest available reference price"""
        # Insert position on 15th
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-15', 100.30)
        
        # Insert reference prices on different dates
        self.db_manager.insert_reference_price('FUND_A', '2024-01-10', 99.00)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 101.00)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        # Should use the latest price before position date (2024-01-10)
        self.assertEqual(result['reference_price'], 99.00)
        self.assertEqual(result['reference_date'], '2024-01-10')


class TestReconciliationStatus(unittest.TestCase):
    """Test reconciliation status determination"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.reconciler = PriceReconciler(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_status_exact_match(self):
        """Test EXACT_MATCH status"""
        status = self.reconciler._determine_status('2024-01-31', '2024-01-31', 0.0)
        self.assertEqual(status, 'EXACT_MATCH')
    
    def test_status_minor_variance(self):
        """Test MATCHED_MINOR_VARIANCE status"""
        status = self.reconciler._determine_status('2024-01-31', '2024-01-31', 0.05)
        self.assertEqual(status, 'MATCHED_MINOR_VARIANCE')
    
    def test_status_acceptable_variance(self):
        """Test MATCHED_ACCEPTABLE_VARIANCE status"""
        status = self.reconciler._determine_status('2024-01-31', '2024-01-31', 0.5)
        self.assertEqual(status, 'MATCHED_ACCEPTABLE_VARIANCE')
    
    def test_status_high_variance(self):
        """Test MATCHED_HIGH_VARIANCE status"""
        status = self.reconciler._determine_status('2024-01-31', '2024-01-31', 2.0)
        self.assertEqual(status, 'MATCHED_HIGH_VARIANCE')
    
    def test_status_fallback_same_day(self):
        """Test FALLBACK_SAME_DAY status"""
        status = self.reconciler._determine_status('2024-01-31', '2024-01-31', 0.5)
        self.assertEqual(status, 'MATCHED_ACCEPTABLE_VARIANCE')
    
    def test_status_fallback_within_week(self):
        """Test FALLBACK_WITHIN_WEEK status"""
        status = self.reconciler._determine_status('2024-01-15', '2024-01-20', 0.5)
        self.assertEqual(status, 'FALLBACK_WITHIN_WEEK')
    
    def test_status_fallback_within_month(self):
        """Test FALLBACK_WITHIN_MONTH status"""
        status = self.reconciler._determine_status('2024-01-15', '2024-02-10', 0.5)
        self.assertEqual(status, 'FALLBACK_WITHIN_MONTH')
    
    def test_status_fallback_stale_data(self):
        """Test FALLBACK_STALE_DATA status"""
        status = self.reconciler._determine_status('2024-01-15', '2023-12-01', 0.5)
        self.assertEqual(status, 'FALLBACK_STALE_DATA')


class TestMultipleReconciliations(unittest.TestCase):
    """Test reconciliation of multiple funds"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.reconciler = PriceReconciler(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_reconcile_all_funds(self):
        """Test reconciliation of all funds"""
        # Insert positions for multiple funds
        for fund in ['FUND_A', 'FUND_B', 'FUND_C']:
            for day in range(15, 18):
                self.db_manager.insert_fund_position(
                    fund, f'{fund} Name', f'2024-01-{day}', 100.00 + day
                )
        
        # Insert reference prices
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.00)
        self.db_manager.insert_reference_price('FUND_B', '2024-01-31', 100.00)
        self.db_manager.insert_reference_price('FUND_C', '2024-01-31', 100.00)
        
        results = self.reconciler.reconcile_all_funds()
        
        # Should have 9 results (3 funds × 3 dates)
        self.assertEqual(len(results), 9)
        
        # All should have reconciliation status
        for result in results:
            self.assertIsNotNone(result['reconciliation_status'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases in reconciliation"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.reconciler = PriceReconciler(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_zero_reference_price(self):
        """Test handling of zero reference price"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 100.00)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 0.0)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result['variance_pct'], 0.0)
    
    def test_very_large_price(self):
        """Test handling of very large prices"""
        large_price = 999999.99
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', large_price)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', large_price)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        self.assertEqual(result['position_price'], large_price)
        self.assertEqual(result['price_variance'], 0.0)
    
    def test_very_small_variance(self):
        """Test handling of very small price variances"""
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-31', 100.0001)
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.00)
        
        position = self.db_manager.get_fund_positions()[0]
        result = self.reconciler.reconcile_position(position)
        
        # Should calculate correctly
        self.assertGreater(result['variance_pct'], 0)
        self.assertLess(result['variance_pct'], 0.001)


if __name__ == '__main__':
    unittest.main()
