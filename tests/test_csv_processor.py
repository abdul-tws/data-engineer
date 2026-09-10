"""
Unit Tests for CSV Processor Module
Tests CSV format detection and normalization
"""

import unittest
import tempfile
from pathlib import Path
import csv
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from csv_processor import CSVProcessor
from database import DatabaseManager


class TestCSVDateNormalization(unittest.TestCase):
    """Test date normalization"""
    
    def test_normalize_date_iso_format(self):
        """Test ISO format date normalization"""
        result = CSVProcessor._normalize_date('2024-01-15')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_date_european_format(self):
        """Test European format date normalization"""
        result = CSVProcessor._normalize_date('15-01-2024')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_date_us_format(self):
        """Test US format date normalization"""
        result = CSVProcessor._normalize_date('01-15-2024')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_date_slash_format(self):
        """Test slash format date normalization"""
        result = CSVProcessor._normalize_date('2024/01/15')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_date_dot_format(self):
        """Test dot format date normalization"""
        result = CSVProcessor._normalize_date('15.01.2024')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_date_month_name(self):
        """Test month name format date normalization"""
        result = CSVProcessor._normalize_date('January 15, 2024')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_date_invalid(self):
        """Test invalid date handling"""
        result = CSVProcessor._normalize_date('invalid-date')
        self.assertIsNone(result)
    
    def test_normalize_date_empty(self):
        """Test empty string handling"""
        result = CSVProcessor._normalize_date('')
        self.assertIsNone(result)
    
    def test_normalize_date_none(self):
        """Test None input handling"""
        result = CSVProcessor._normalize_date(None)
        self.assertIsNone(result)


class TestCSVFloatParsing(unittest.TestCase):
    """Test float parsing"""
    
    def test_parse_float_valid(self):
        """Test valid float parsing"""
        result = CSVProcessor._parse_float('100.50')
        self.assertEqual(result, 100.50)
    
    def test_parse_float_with_comma(self):
        """Test float with comma separator"""
        result = CSVProcessor._parse_float('1,000.50')
        self.assertEqual(result, 1000.50)
    
    def test_parse_float_integer(self):
        """Test integer parsing"""
        result = CSVProcessor._parse_float('100')
        self.assertEqual(result, 100.0)
    
    def test_parse_float_negative(self):
        """Test negative number parsing"""
        result = CSVProcessor._parse_float('-50.25')
        self.assertEqual(result, -50.25)
    
    def test_parse_float_invalid(self):
        """Test invalid float handling"""
        result = CSVProcessor._parse_float('abc')
        self.assertEqual(result, 0.0)
    
    def test_parse_float_empty(self):
        """Test empty string handling"""
        result = CSVProcessor._parse_float('')
        self.assertEqual(result, 0.0)
    
    def test_parse_float_none(self):
        """Test None handling"""
        result = CSVProcessor._parse_float(None)
        self.assertEqual(result, 0.0)


class TestCSVFormatDetection(unittest.TestCase):
    """Test CSV format detection"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.processor = CSVProcessor(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_detect_format_a(self):
        """Test Format A detection"""
        row = {
            'Fund_ID': 'FUND_A',
            'Fund_Name': 'Growth Fund',
            'Date': '2024-01-15',
            'Price': '100.50',
            'Quantity': '1000',
            'Value': '100500'
        }
        result = self.processor._detect_format(row)
        self.assertEqual(result, 'format_a')
    
    def test_detect_format_b(self):
        """Test Format B detection"""
        row = {
            'FundCode': 'FUND_B',
            'FundName': 'Income Fund',
            'TradeDate': '2024-01-15',
            'Value': '50.10'
        }
        result = self.processor._detect_format(row)
        self.assertEqual(result, 'format_b')
    
    def test_detect_format_c(self):
        """Test Format C detection"""
        row = {
            'ISIN': 'IE00B4L5Y983',
            'FundName': 'Balanced Fund',
            'Date_EOM': '2024-01-31',
            'NAV': '149.80'
        }
        result = self.processor._detect_format(row)
        self.assertEqual(result, 'format_c')
    
    def test_detect_format_generic(self):
        """Test generic format detection"""
        row = {
            'fund_code': 'FUND_X',
            'price_value': '100.00'
        }
        result = self.processor._detect_format(row)
        self.assertEqual(result, 'generic')


class TestCSVProcessing(unittest.TestCase):
    """Test CSV file processing"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        self.processor = CSVProcessor(self.db_manager)
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_process_format_a_csv(self):
        """Test processing Format A CSV"""
        csv_path = Path(self.temp_dir.name) / "format_a.csv"
        
        # Create test CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price', 'Quantity', 'Value'])
            writer.writeheader()
            writer.writerow({
                'Fund_ID': 'FUND_A',
                'Fund_Name': 'Growth Fund A',
                'Date': '2024-01-15',
                'Price': '100.25',
                'Quantity': '1000',
                'Value': '100250'
            })
        
        self.processor.process_csv(csv_path)
        
        # Verify data was inserted
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['fund_id'], 'FUND_A')
        self.assertEqual(positions[0]['position_price'], 100.25)
    
    def test_process_format_b_csv(self):
        """Test processing Format B CSV"""
        csv_path = Path(self.temp_dir.name) / "format_b.csv"
        
        # Create test CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['FundCode', 'FundName', 'TradeDate', 'Value'])
            writer.writeheader()
            writer.writerow({
                'FundCode': 'FUND_B',
                'FundName': 'Income Fund B',
                'TradeDate': '2024-01-15',
                'Value': '50.10'
            })
        
        self.processor.process_csv(csv_path)
        
        # Verify data was inserted
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['fund_id'], 'FUND_B')
        self.assertEqual(positions[0]['position_price'], 50.10)
    
    def test_process_csv_with_invalid_dates(self):
        """Test processing CSV with invalid dates"""
        csv_path = Path(self.temp_dir.name) / "invalid_dates.csv"
        
        # Create test CSV with invalid date
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
            writer.writerow({
                'Fund_ID': 'FUND_A',
                'Fund_Name': 'Fund A',
                'Date': 'invalid-date',
                'Price': '100.00'
            })
        
        # Should not raise exception
        self.processor.process_csv(csv_path)
        
        # No data should be inserted due to invalid date
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 0)
    
    def test_process_empty_csv(self):
        """Test processing empty CSV"""
        csv_path = Path(self.temp_dir.name) / "empty.csv"
        
        # Create empty CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
        
        # Should not raise exception
        self.processor.process_csv(csv_path)
        
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 0)
    
    def test_process_multiple_rows(self):
        """Test processing CSV with multiple rows"""
        csv_path = Path(self.temp_dir.name) / "multiple.csv"
        
        # Create test CSV
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
            for i in range(5):
                writer.writerow({
                    'Fund_ID': f'FUND_{i}',
                    'Fund_Name': f'Fund {i}',
                    'Date': f'2024-01-{15+i:02d}',
                    'Price': str(100.00 + i)
                })
        
        self.processor.process_csv(csv_path)
        
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 5)


if __name__ == '__main__':
    unittest.main()
