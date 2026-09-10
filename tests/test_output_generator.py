"""
Unit Tests for Output Generator Module
Tests CSV report generation
"""

import unittest
import tempfile
from pathlib import Path
import csv
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from output_generator import OutputGenerator


class TestOutputGenerator(unittest.TestCase):
    """Test output generation"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.generator = OutputGenerator(self.output_dir)
    
    def tearDown(self):
        """Cleanup"""
        self.temp_dir.cleanup()
    
    def test_generate_reconciliation_csv(self):
        """Test price reconciliation CSV generation"""
        reconciliation_results = [
            {
                'fund_id': 'FUND_A',
                'position_date': '2024-01-31',
                'position_price': 100.50,
                'reference_price': 100.50,
                'reference_date': '2024-01-31',
                'price_variance': 0.0,
                'variance_pct': 0.0,
                'reconciliation_status': 'EXACT_MATCH'
            },
            {
                'fund_id': 'FUND_B',
                'position_date': '2024-01-15',
                'position_price': 50.25,
                'reference_price': 50.00,
                'reference_date': '2024-01-10',
                'price_variance': 0.25,
                'variance_pct': 0.5,
                'reconciliation_status': 'FALLBACK_WITHIN_WEEK'
            }
        ]
        
        self.generator.generate_reconciliation_csv(reconciliation_results)
        
        # Verify file created
        output_file = self.output_dir / 'price_reconciliation.csv'
        self.assertTrue(output_file.exists())
        
        # Verify contents
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['Fund_ID'], 'FUND_A')
        self.assertEqual(rows[0]['Reconciliation_Status'], 'EXACT_MATCH')
        self.assertEqual(rows[1]['Fund_ID'], 'FUND_B')
    
    def test_generate_best_fund_csv(self):
        """Test best fund by month CSV generation"""
        best_by_month = [
            {
                'year': 2024,
                'month': 1,
                'month_label': 'January 2024',
                'fund_id': 'FUND_A',
                'fund_name': 'Growth Fund A',
                'opening_price': 100.00,
                'closing_price': 105.00,
                'monthly_return': 5.00,
                'monthly_return_pct': 5.0
            },
            {
                'year': 2024,
                'month': 2,
                'month_label': 'February 2024',
                'fund_id': 'FUND_B',
                'fund_name': 'Income Fund B',
                'opening_price': 50.00,
                'closing_price': 52.00,
                'monthly_return': 2.00,
                'monthly_return_pct': 4.0
            }
        ]
        
        self.generator.generate_best_fund_csv(best_by_month)
        
        # Verify file created
        output_file = self.output_dir / 'best_fund_by_month.csv'
        self.assertTrue(output_file.exists())
        
        # Verify contents
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['Fund_ID'], 'FUND_A')
        self.assertEqual(rows[0]['Month_Label'], 'January 2024')
        self.assertEqual(rows[1]['Fund_ID'], 'FUND_B')
    
    def test_csv_format_correctness(self):
        """Test CSV format is correct"""
        reconciliation_results = [
            {
                'fund_id': 'TEST_FUND',
                'position_date': '2024-01-15',
                'position_price': 123.45,
                'reference_price': 123.40,
                'reference_date': '2024-01-10',
                'price_variance': 0.05,
                'variance_pct': 0.0406,
                'reconciliation_status': 'MATCHED_MINOR_VARIANCE'
            }
        ]
        
        self.generator.generate_reconciliation_csv(reconciliation_results)
        
        # Read and verify format
        with open(self.output_dir / 'price_reconciliation.csv', 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        # Check all expected columns exist
        expected_cols = [
            'Fund_ID', 'Position_Date', 'Position_Price',
            'Reference_Price', 'Reference_Date', 'Price_Variance',
            'Variance_Pct', 'Reconciliation_Status'
        ]
        for col in expected_cols:
            self.assertIn(col, row)
    
    def test_handling_none_values(self):
        """Test handling of None values in reconciliation"""
        reconciliation_results = [
            {
                'fund_id': 'FUND_A',
                'position_date': '2024-01-15',
                'position_price': 100.00,
                'reference_price': None,
                'reference_date': None,
                'price_variance': None,
                'variance_pct': None,
                'reconciliation_status': 'NO_REFERENCE_DATA'
            }
        ]
        
        self.generator.generate_reconciliation_csv(reconciliation_results)
        
        # Verify file and check None handling
        with open(self.output_dir / 'price_reconciliation.csv', 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        self.assertEqual(row['Reference_Price'], 'N/A')
        self.assertEqual(row['Reference_Date'], 'N/A')


class TestNumberFormatting(unittest.TestCase):
    """Test number formatting utility"""
    
    def test_format_number_valid_float(self):
        """Test formatting valid float"""
        result = OutputGenerator._format_number(100.506, decimals=2)
        self.assertEqual(result, '100.51')  # Should round up
    
    def test_format_number_integer(self):
        """Test formatting integer"""
        result = OutputGenerator._format_number(100, decimals=2)
        self.assertEqual(result, '100.00')
    
    def test_format_number_negative(self):
        """Test formatting negative number"""
        result = OutputGenerator._format_number(-50.25, decimals=2)
        self.assertEqual(result, '-50.25')
    
    def test_format_number_zero(self):
        """Test formatting zero"""
        result = OutputGenerator._format_number(0.0, decimals=2)
        self.assertEqual(result, '0.00')
    
    def test_format_number_none(self):
        """Test formatting None"""
        result = OutputGenerator._format_number(None, decimals=2)
        self.assertEqual(result, 'N/A')
    
    def test_format_number_string(self):
        """Test formatting string representation of number"""
        result = OutputGenerator._format_number('100.50', decimals=2)
        self.assertEqual(result, '100.50')
    
    def test_format_number_invalid_string(self):
        """Test formatting invalid string"""
        result = OutputGenerator._format_number('invalid', decimals=2)
        self.assertEqual(result, 'N/A')
    
    def test_format_number_custom_decimals(self):
        """Test formatting with custom decimal places"""
        result = OutputGenerator._format_number(100.123456, decimals=4)
        self.assertEqual(result, '100.1235')


class TestEmptyOutput(unittest.TestCase):
    """Test handling of empty outputs"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.generator = OutputGenerator(self.output_dir)
    
    def tearDown(self):
        """Cleanup"""
        self.temp_dir.cleanup()
    
    def test_empty_reconciliation_csv(self):
        """Test generating empty reconciliation CSV"""
        self.generator.generate_reconciliation_csv([])
        
        output_file = self.output_dir / 'price_reconciliation.csv'
        self.assertTrue(output_file.exists())
        
        # Should have headers but no data
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 1)  # Only header
    
    def test_empty_best_fund_csv(self):
        """Test generating empty best fund CSV"""
        self.generator.generate_best_fund_csv([])
        
        output_file = self.output_dir / 'best_fund_by_month.csv'
        self.assertTrue(output_file.exists())
        
        # Should have headers but no data
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 1)  # Only header


if __name__ == '__main__':
    unittest.main()
