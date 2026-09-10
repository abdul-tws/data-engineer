"""
Integration Tests - Tests the complete end-to-end workflow
"""

import unittest
import tempfile
import csv
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database import DatabaseManager
from csv_processor import CSVProcessor
from reconciler import PriceReconciler
from analytics import AnalyticsCalculator
from output_generator import OutputGenerator


class TestCompleteWorkflow(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        
        # Create directories
        self.data_dir = self.project_dir / "data"
        self.data_dir.mkdir()
        
        self.send_data_dir = self.data_dir / "Send_data"
        self.send_data_dir.mkdir()
        
        self.output_dir = self.project_dir / "output"
        self.output_dir.mkdir()
        
        # Create database
        self.db_path = self.data_dir / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_complete_workflow_single_fund(self):
        """Test complete workflow with single fund"""
        
        # 1. Create sample CSV
        csv_path = self.send_data_dir / "test_fund.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
            for day in range(15, 32):
                writer.writerow({
                    'Fund_ID': 'FUND_TEST',
                    'Fund_Name': 'Test Fund',
                    'Date': f'2024-01-{day:02d}',
                    'Price': str(100.00 + day - 15)
                })
        
        # 2. Create reference prices
        self.db_manager.insert_reference_price('FUND_TEST', '2024-01-31', 115.00)
        
        # 3. Process CSV
        processor = CSVProcessor(self.db_manager)
        processor.process_csv(csv_path)
        
        positions = self.db_manager.get_fund_positions()
        self.assertGreater(len(positions), 0)
        
        # 4. Reconcile prices
        reconciler = PriceReconciler(self.db_manager)
        results = reconciler.reconcile_all_funds()
        
        self.assertGreater(len(results), 0)
        # Check that reconciliation status is set
        for result in results:
            self.assertIsNotNone(result['reconciliation_status'])
        
        # 5. Calculate returns
        analytics = AnalyticsCalculator(self.db_manager)
        returns = analytics.calculate_monthly_returns()
        
        self.assertGreater(len(returns), 0)
        
        # 6. Generate output
        output_gen = OutputGenerator(self.output_dir)
        output_gen.generate_reconciliation_csv(results)
        output_gen.generate_best_fund_csv(analytics.identify_best_performers())
        
        # 7. Verify output files exist
        self.assertTrue((self.output_dir / 'price_reconciliation.csv').exists())
        self.assertTrue((self.output_dir / 'best_fund_by_month.csv').exists())
    
    def test_complete_workflow_multiple_formats(self):
        """Test workflow with multiple CSV formats"""
        
        # Create Format A CSV
        csv_a = self.send_data_dir / "format_a.csv"
        with open(csv_a, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
            writer.writerow({
                'Fund_ID': 'FUND_A',
                'Fund_Name': 'Fund A',
                'Date': '2024-01-15',
                'Price': '100.00'
            })
            writer.writerow({
                'Fund_ID': 'FUND_A',
                'Fund_Name': 'Fund A',
                'Date': '2024-01-31',
                'Price': '105.00'
            })
        
        # Create Format B CSV
        csv_b = self.send_data_dir / "format_b.csv"
        with open(csv_b, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['FundCode', 'FundName', 'TradeDate', 'Value'])
            writer.writeheader()
            writer.writerow({
                'FundCode': 'FUND_B',
                'FundName': 'Fund B',
                'TradeDate': '2024-01-15',
                'Value': '50.00'
            })
            writer.writerow({
                'FundCode': 'FUND_B',
                'FundName': 'Fund B',
                'TradeDate': '2024-01-31',
                'Value': '51.00'
            })
        
        # Add reference prices
        self.db_manager.insert_reference_price('FUND_A', '2024-01-31', 105.00)
        self.db_manager.insert_reference_price('FUND_B', '2024-01-31', 51.00)
        
        # Process both CSVs
        processor = CSVProcessor(self.db_manager)
        processor.process_csv(csv_a)
        processor.process_csv(csv_b)
        
        # Verify data loaded
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 4)
        
        # Reconcile
        reconciler = PriceReconciler(self.db_manager)
        results = reconciler.reconcile_all_funds()
        
        self.assertEqual(len(results), 4)
        
        # Calculate returns
        analytics = AnalyticsCalculator(self.db_manager)
        returns = analytics.calculate_monthly_returns()
        
        self.assertEqual(len(returns), 2)  # One for each fund
        
        # Verify returns are calculated correctly
        fund_a_return = next(r for r in returns if r['fund_id'] == 'FUND_A')
        self.assertAlmostEqual(fund_a_return['monthly_return_pct'], 5.0, places=2)
        
        fund_b_return = next(r for r in returns if r['fund_id'] == 'FUND_B')
        self.assertAlmostEqual(fund_b_return['monthly_return_pct'], 2.0, places=2)
    
    def test_complete_workflow_multiple_months(self):
        """Test workflow across multiple months"""
        
        # Create CSV with multiple months
        csv_path = self.send_data_dir / "multi_month.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
            
            # Month 1 (Jan)
            writer.writerow({
                'Fund_ID': 'FUND_MM',
                'Fund_Name': 'Multi-Month Fund',
                'Date': '2024-01-05',
                'Price': '100.00'
            })
            writer.writerow({
                'Fund_ID': 'FUND_MM',
                'Fund_Name': 'Multi-Month Fund',
                'Date': '2024-01-31',
                'Price': '102.00'
            })
            
            # Month 2 (Feb)
            writer.writerow({
                'Fund_ID': 'FUND_MM',
                'Fund_Name': 'Multi-Month Fund',
                'Date': '2024-02-05',
                'Price': '102.00'
            })
            writer.writerow({
                'Fund_ID': 'FUND_MM',
                'Fund_Name': 'Multi-Month Fund',
                'Date': '2024-02-29',
                'Price': '105.00'
            })
            
            # Month 3 (Mar)
            writer.writerow({
                'Fund_ID': 'FUND_MM',
                'Fund_Name': 'Multi-Month Fund',
                'Date': '2024-03-05',
                'Price': '105.00'
            })
            writer.writerow({
                'Fund_ID': 'FUND_MM',
                'Fund_Name': 'Multi-Month Fund',
                'Date': '2024-03-31',
                'Price': '103.00'
            })
        
        # Add reference prices
        self.db_manager.insert_reference_price('FUND_MM', '2024-01-31', 102.00)
        self.db_manager.insert_reference_price('FUND_MM', '2024-02-29', 105.00)
        self.db_manager.insert_reference_price('FUND_MM', '2024-03-31', 103.00)
        
        # Process
        processor = CSVProcessor(self.db_manager)
        processor.process_csv(csv_path)
        
        # Reconcile
        reconciler = PriceReconciler(self.db_manager)
        reconciler.reconcile_all_funds()
        
        # Calculate returns
        analytics = AnalyticsCalculator(self.db_manager)
        returns = analytics.calculate_monthly_returns()
        best = analytics.identify_best_performers()
        
        # Should have 3 monthly returns
        self.assertEqual(len(returns), 3)
        
        # Should have 3 best performers (one per month)
        self.assertEqual(len(best), 3)
        
        # Verify monthly returns
        jan_return = next(r for r in returns if r['month'] == 1)
        self.assertAlmostEqual(jan_return['monthly_return_pct'], 2.0, places=2)
        
        feb_return = next(r for r in returns if r['month'] == 2)
        self.assertAlmostEqual(feb_return['monthly_return_pct'], 2.94, places=1)  # ~3%
        
        mar_return = next(r for r in returns if r['month'] == 3)
        self.assertAlmostEqual(mar_return['monthly_return_pct'], -1.90, places=1)  # ~-2%


class TestErrorHandling(unittest.TestCase):
    """Integration tests for error handling"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        
        self.data_dir = self.project_dir / "data"
        self.data_dir.mkdir()
        
        self.send_data_dir = self.data_dir / "Send_data"
        self.send_data_dir.mkdir()
        
        self.db_path = self.data_dir / "test.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
    
    def tearDown(self):
        """Cleanup"""
        self.db_manager.disconnect()
        self.temp_dir.cleanup()
    
    def test_missing_csv_handling(self):
        """Test handling of missing CSV files"""
        processor = CSVProcessor(self.db_manager)
        
        # Should not raise exception
        processor.process_csv(self.send_data_dir / "nonexistent.csv")
        
        # No positions should be added
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 0)
    
    def test_corrupted_csv_handling(self):
        """Test handling of corrupted CSV"""
        csv_path = self.send_data_dir / "corrupted.csv"
        
        # Create corrupted CSV
        with open(csv_path, 'w') as f:
            f.write("This is not valid CSV data\n")
            f.write("Random text without proper format\n")
        
        processor = CSVProcessor(self.db_manager)
        # Should not raise exception
        processor.process_csv(csv_path)
    
    def test_partial_data_workflow(self):
        """Test workflow with some missing data"""
        # Create CSV with some missing fields
        csv_path = self.send_data_dir / "partial.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Fund_ID', 'Fund_Name', 'Date', 'Price'])
            writer.writeheader()
            writer.writerow({
                'Fund_ID': 'FUND_P',
                'Fund_Name': 'Partial Fund',
                'Date': '2024-01-15',
                'Price': '100.00'
            })
            # Valid closing price
            writer.writerow({
                'Fund_ID': 'FUND_P',
                'Fund_Name': 'Partial Fund',
                'Date': '2024-01-31',
                'Price': '102.00'
            })
        
        processor = CSVProcessor(self.db_manager)
        processor.process_csv(csv_path)
        
        # Should still process valid rows
        positions = self.db_manager.get_fund_positions()
        self.assertEqual(len(positions), 2)


if __name__ == '__main__':
    unittest.main()
