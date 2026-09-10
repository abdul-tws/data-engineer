"""
Output Generator - Creates CSV reports from reconciliation and analytics results
"""

import csv
from pathlib import Path
from typing import List, Dict, Any


class OutputGenerator:
    """Generates output CSV files"""
    
    def __init__(self, output_dir: Path):
        """Initialize output generator"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_reconciliation_csv(self, reconciliation_results: List[Dict[str, Any]]):
        """
        Generate price reconciliation CSV
        Shows position prices vs reference prices and variance
        """
        output_path = self.output_dir / 'price_reconciliation.csv'
        
        fieldnames = [
            'Fund_ID',
            'Position_Date',
            'Position_Price',
            'Reference_Price',
            'Reference_Date',
            'Price_Variance',
            'Variance_Pct',
            'Reconciliation_Status'
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in reconciliation_results:
                    writer.writerow({
                        'Fund_ID': result['fund_id'],
                        'Position_Date': result['position_date'],
                        'Position_Price': self._format_number(result['position_price']),
                        'Reference_Price': self._format_number(result['reference_price']),
                        'Reference_Date': result['reference_date'] or 'N/A',
                        'Price_Variance': self._format_number(result['price_variance']),
                        'Variance_Pct': self._format_number(result['variance_pct']),
                        'Reconciliation_Status': result['reconciliation_status']
                    })
        
        except Exception as e:
            print(f"Error generating reconciliation CSV: {e}")
    
    def generate_best_fund_csv(self, best_by_month: List[Dict[str, Any]]):
        """
        Generate best fund by month CSV
        Shows the best performing fund for each month
        """
        output_path = self.output_dir / 'best_fund_by_month.csv'
        
        fieldnames = [
            'Year',
            'Month',
            'Month_Label',
            'Fund_ID',
            'Fund_Name',
            'Opening_Price',
            'Closing_Price',
            'Monthly_Return',
            'Monthly_Return_Pct'
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in best_by_month:
                    writer.writerow({
                        'Year': entry['year'],
                        'Month': entry['month'],
                        'Month_Label': entry['month_label'],
                        'Fund_ID': entry['fund_id'],
                        'Fund_Name': entry['fund_name'],
                        'Opening_Price': self._format_number(entry['opening_price']),
                        'Closing_Price': self._format_number(entry['closing_price']),
                        'Monthly_Return': self._format_number(entry['monthly_return']),
                        'Monthly_Return_Pct': self._format_number(entry['monthly_return_pct'], decimals=4)
                    })
        
        except Exception as e:
            print(f"Error generating best fund CSV: {e}")
    
    @staticmethod
    def _format_number(value: Any, decimals: int = 2) -> str:
        """Format number with specified decimal places"""
        if value is None:
            return 'N/A'
        
        try:
            number = float(value)
            return f"{number:.{decimals}f}"
        except (ValueError, TypeError):
            return 'N/A'
