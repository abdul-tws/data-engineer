"""
Unit Tests for Database Module
Tests SQLite database operations and schema
"""

import unittest
import tempfile
from pathlib import Path
import sqlite3
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager"""
    
    def setUp(self):
        """Create temporary database for each test"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_database_connection(self):
        """Test database connection"""
        self.db_manager.connect()
        self.assertIsNotNone(self.db_manager.connection)
        self.assertIsNotNone(self.db_manager.cursor)
    
    def test_database_initialization(self):
        """Test database schema initialization"""
        self.db_manager.initialize()
        
        # Verify tables exist
        self.db_manager.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in self.db_manager.cursor.fetchall()}
        
        expected_tables = {
            'reference_prices',
            'fund_positions',
            'reconciled_prices',
            'monthly_returns'
        }
        self.assertTrue(expected_tables.issubset(tables))
    
    def test_insert_reference_price(self):
        """Test inserting reference price"""
        self.db_manager.initialize()
        
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.50)
        
        # Verify insertion
        self.db_manager.cursor.execute(
            "SELECT price FROM reference_prices WHERE fund_id = ? AND price_date = ?",
            ('FUND_A', '2024-01-31')
        )
        result = self.db_manager.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 100.50)
    
    def test_insert_fund_position(self):
        """Test inserting fund position"""
        self.db_manager.initialize()
        
        self.db_manager.insert_fund_position(
            'FUND_A', 'Growth Fund A', '2024-01-15', 100.25, 1000, 100250, 'test_source'
        )
        
        # Verify insertion
        self.db_manager.cursor.execute(
            "SELECT position_price, quantity FROM fund_positions WHERE fund_id = ? AND position_date = ?",
            ('FUND_A', '2024-01-15')
        )
        result = self.db_manager.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 100.25)
        self.assertEqual(result[1], 1000)
    
    def test_get_reference_price_exact_match(self):
        """Test getting reference price with exact date match"""
        self.db_manager.initialize()
        
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.50)
        
        result = self.db_manager.get_reference_price('FUND_A', '2024-01-31')
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 100.50)
        self.assertEqual(result[1], '2024-01-31')
    
    def test_get_reference_price_fallback(self):
        """Test getting reference price with fallback to latest"""
        self.db_manager.initialize()
        
        # Insert prices on different dates
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.50)
        self.db_manager.insert_reference_price('FUND_A', '2024-02-29', 102.30)
        
        # Query for date between two prices
        result = self.db_manager.get_reference_price('FUND_A', '2024-02-15')
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 100.50)  # Should get latest before date
        self.assertEqual(result[1], '2024-01-31')
    
    def test_get_reference_price_no_data(self):
        """Test getting reference price when no data exists"""
        self.db_manager.initialize()
        
        result = self.db_manager.get_reference_price('FUND_X', '2024-01-31')
        self.assertIsNone(result)
    
    def test_insert_reconciled_price(self):
        """Test inserting reconciled price"""
        self.db_manager.initialize()
        
        self.db_manager.insert_reconciled_price(
            'FUND_A', '2024-01-31', 100.50, 100.50, '2024-01-31', 0.0, 0.0, 'EXACT_MATCH'
        )
        
        # Verify insertion
        self.db_manager.cursor.execute(
            "SELECT reconciliation_status FROM reconciled_prices WHERE fund_id = ?"
        )
        result = self.db_manager.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'EXACT_MATCH')
    
    def test_insert_monthly_return(self):
        """Test inserting monthly return"""
        self.db_manager.initialize()
        
        self.db_manager.insert_monthly_return(
            'FUND_A', 'Growth Fund A', 2024, 1, 100.25, 100.50, 0.25, 0.2498
        )
        
        # Verify insertion
        self.db_manager.cursor.execute(
            "SELECT monthly_return_pct FROM monthly_returns WHERE fund_id = ? AND month = ?",
            ('FUND_A', 1)
        )
        result = self.db_manager.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result[0], 0.2498, places=4)
    
    def test_get_fund_positions(self):
        """Test retrieving all fund positions"""
        self.db_manager.initialize()
        
        # Insert multiple positions
        self.db_manager.insert_fund_position('FUND_A', 'Fund A', '2024-01-15', 100.25)
        self.db_manager.insert_fund_position('FUND_B', 'Fund B', '2024-01-15', 50.10)
        
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 2)
    
    def test_get_monthly_returns(self):
        """Test retrieving monthly returns"""
        self.db_manager.initialize()
        
        self.db_manager.insert_monthly_return('FUND_A', 'Fund A', 2024, 1, 100.0, 101.0, 1.0, 1.0)
        self.db_manager.insert_monthly_return('FUND_A', 'Fund A', 2024, 2, 101.0, 102.0, 1.0, 0.99)
        
        returns = self.db_manager.get_monthly_returns()
        self.assertEqual(len(returns), 2)
    
    def test_duplicate_prevention(self):
        """Test that duplicate entries are prevented"""
        self.db_manager.initialize()
        
        # Insert first record
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 100.50)
        
        # Insert duplicate
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 101.00)
        
        # Check only one record exists
        self.db_manager.cursor.execute(
            "SELECT COUNT(*) FROM reference_prices WHERE fund_id = ? AND price_date = ?",
            ('FUND_A', '2024-01-31')
        )
        count = self.db_manager.cursor.fetchone()[0]
        self.assertEqual(count, 1)


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema integrity"""
    
    def setUp(self):
        """Create temporary database"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
    
    def tearDown(self):
        """Clean up"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_reference_prices_columns(self):
        """Test reference_prices table columns"""
        self.db_manager.cursor.execute("PRAGMA table_info(reference_prices)")
        columns = {row[1]: row[2] for row in self.db_manager.cursor.fetchall()}
        
        self.assertIn('id', columns)
        self.assertIn('fund_id', columns)
        self.assertIn('price_date', columns)
        self.assertIn('price', columns)
    
    def test_fund_positions_columns(self):
        """Test fund_positions table columns"""
        self.db_manager.cursor.execute("PRAGMA table_info(fund_positions)")
        columns = {row[1]: row[2] for row in self.db_manager.cursor.fetchall()}
        
        self.assertIn('fund_id', columns)
        self.assertIn('fund_name', columns)
        self.assertIn('position_date', columns)
        self.assertIn('position_price', columns)
        self.assertIn('source', columns)
    
    def test_reconciled_prices_columns(self):
        """Test reconciled_prices table columns"""
        self.db_manager.cursor.execute("PRAGMA table_info(reconciled_prices)")
        columns = {row[1]: row[2] for row in self.db_manager.cursor.fetchall()}
        
        self.assertIn('reconciliation_status', columns)
        self.assertIn('price_variance', columns)
        self.assertIn('variance_pct', columns)
    
    def test_monthly_returns_columns(self):
        """Test monthly_returns table columns"""
        self.db_manager.cursor.execute("PRAGMA table_info(monthly_returns)")
        columns = {row[1]: row[2] for row in self.db_manager.cursor.fetchall()}
        
        self.assertIn('fund_id', columns)
        self.assertIn('year', columns)
        self.assertIn('month', columns)
        self.assertIn('monthly_return_pct', columns)


if __name__ == '__main__':
    unittest.main()
