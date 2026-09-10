"""
CSV Processor - Reads and normalizes different fund CSV formats
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from database import DatabaseManager


class CSVProcessor:
    """Processes and normalizes fund CSV reports from various sources"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize CSV processor"""
        self.db_manager = db_manager
    
    def process_csv(self, csv_path: Path):
        """Process a fund CSV file and normalize its format"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                print(f"    Warning: Empty CSV file {csv_path.name}")
                return
            
            # Detect format and normalize
            detected_format = self._detect_format(rows[0])
            print(f"    Detected format: {detected_format}")
            
            # Process based on detected format
            if detected_format == "format_a":
                self._process_format_a(rows, csv_path.name)
            elif detected_format == "format_b":
                self._process_format_b(rows, csv_path.name)
            elif detected_format == "format_c":
                self._process_format_c(rows, csv_path.name)
            else:
                self._process_generic(rows, csv_path.name)
        
        except Exception as e:
            print(f"    Error processing CSV: {e}")
    
    def _detect_format(self, row: Dict[str, str]) -> str:
        """Detect CSV format based on column headers"""
        headers = set(row.keys())
        
        # Format A: Standard format with Fund_ID, Price, Date
        if {'Fund_ID', 'Price', 'Date'}.issubset(headers):
            return "format_a"
        
        # Format B: Alternative with FundCode, Value, TradeDate
        if {'FundCode', 'Value', 'TradeDate'}.issubset(headers):
            return "format_b"
        
        # Format C: Extended format with ISIN, NAV, Date_EOM
        if {'ISIN', 'NAV', 'Date_EOM'}.issubset(headers):
            return "format_c"
        
        return "generic"
    
    def _process_format_a(self, rows: List[Dict], source: str):
        """
        Process Format A CSV
        Expected columns: Fund_ID, Fund_Name, Date, Price, Quantity, Value
        """
        for row in rows:
            try:
                fund_id = row.get('Fund_ID', '').strip()
                fund_name = row.get('Fund_Name', fund_id).strip()
                date_str = self._normalize_date(row.get('Date', ''))
                price = self._parse_float(row.get('Price', '0'))
                quantity = self._parse_float(row.get('Quantity'))
                value = self._parse_float(row.get('Value'))
                
                if fund_id and date_str and price:
                    self.db_manager.insert_fund_position(
                        fund_id, fund_name, date_str, price, quantity, value, source
                    )
            except Exception as e:
                print(f"    Error processing row: {e}")
    
    def _process_format_b(self, rows: List[Dict], source: str):
        """
        Process Format B CSV
        Expected columns: FundCode, FundName, TradeDate, Value (NAV)
        """
        for row in rows:
            try:
                fund_id = row.get('FundCode', '').strip()
                fund_name = row.get('FundName', fund_id).strip()
                date_str = self._normalize_date(row.get('TradeDate', ''))
                price = self._parse_float(row.get('Value', '0'))
                
                if fund_id and date_str and price:
                    self.db_manager.insert_fund_position(
                        fund_id, fund_name, date_str, price, source=source
                    )
            except Exception as e:
                print(f"    Error processing row: {e}")
    
    def _process_format_c(self, rows: List[Dict], source: str):
        """
        Process Format C CSV
        Expected columns: ISIN, FundName, Date_EOM, NAV
        """
        for row in rows:
            try:
                fund_id = row.get('ISIN', '').strip()
                fund_name = row.get('FundName', fund_id).strip()
                date_str = self._normalize_date(row.get('Date_EOM', ''))
                price = self._parse_float(row.get('NAV', '0'))
                
                if fund_id and date_str and price:
                    self.db_manager.insert_fund_position(
                        fund_id, fund_name, date_str, price, source=source
                    )
            except Exception as e:
                print(f"    Error processing row: {e}")
    
    def _process_generic(self, rows: List[Dict], source: str):
        """
        Process generic CSV format
        Attempts to map columns generically
        """
        for row in rows:
            try:
                # Find columns flexibly
                headers = row.keys()
                
                # Look for fund identifier
                fund_id_col = next((h for h in headers if 'id' in h.lower() or 'code' in h.lower()), None)
                fund_name_col = next((h for h in headers if 'name' in h.lower()), None)
                date_col = next((h for h in headers if 'date' in h.lower()), None)
                price_col = next((h for h in headers if 'price' in h.lower() or 'nav' in h.lower() or 'value' in h.lower()), None)
                
                if fund_id_col and date_col and price_col:
                    fund_id = row.get(fund_id_col, '').strip()
                    fund_name = row.get(fund_name_col, fund_id).strip() if fund_name_col else fund_id
                    date_str = self._normalize_date(row.get(date_col, ''))
                    price = self._parse_float(row.get(price_col, '0'))
                    
                    if fund_id and date_str and price:
                        self.db_manager.insert_fund_position(
                            fund_id, fund_name, date_str, price, source=source
                        )
            except Exception as e:
                print(f"    Error processing row: {e}")
    
    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize various date formats to YYYY-MM-DD"""
        if not date_str or not date_str.strip():
            return None
        
        date_str = date_str.strip()
        
        # Common date formats to try
        formats = [
            '%Y-%m-%d',      # 2024-01-15
            '%d-%m-%Y',      # 15-01-2024
            '%m-%d-%Y',      # 01-15-2024
            '%Y/%m/%d',      # 2024/01/15
            '%d/%m/%Y',      # 15/01/2024
            '%m/%d/%Y',      # 01/15/2024
            '%d.%m.%Y',      # 15.01.2024
            '%Y.%m.%d',      # 2024.01.15
            '%B %d, %Y',     # January 15, 2024
            '%d %B %Y',      # 15 January 2024
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format matched, try pandas as fallback (if available)
        try:
            import pandas as pd
            parsed = pd.to_datetime(date_str)
            return parsed.strftime('%Y-%m-%d')
        except:
            return None
    
    @staticmethod
    def _parse_float(value: Any) -> float:
        """Safely parse float value"""
        if not value:
            return 0.0
        
        try:
            # Handle strings with commas
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value)
        except (ValueError, TypeError):
            return 0.0
