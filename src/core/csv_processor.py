"""
CSV Processor
Handles parsing and normalizing different CSV formats
"""

import csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedFund:
    """Parsed fund data from CSV"""
    fund_id: str
    fund_name: str
    date: datetime
    price: Decimal
    quantity: Optional[Decimal] = None
    value: Optional[Decimal] = None


class CSVProcessor:
    """
    CSV Processor
    Detects and processes different CSV formats
    """
    
    # Supported formats
    FORMAT_A = "format_a"  # Fund_ID, Fund_Name, Date, Price, Quantity, Value
    FORMAT_B = "format_b"  # FundCode, FundName, TradeDate, Value
    FORMAT_C = "format_c"  # ISIN, FundName, Date_EOM, NAV
    FORMAT_GENERIC = "generic"  # Flexible column matching
    
    def __init__(self):
        """Initialize CSV processor"""
        pass
    
    def process_file(self, file_path: Path) -> List[ParsedFund]:
        """
        Process a CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of parsed fund data
        """
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return []
        
        # Detect format
        detected_format = self._detect_format(rows[0])
        
        # Process based on format
        if detected_format == self.FORMAT_A:
            return self._process_format_a(rows)
        elif detected_format == self.FORMAT_B:
            return self._process_format_b(rows)
        elif detected_format == self.FORMAT_C:
            return self._process_format_c(rows)
        else:
            return self._process_generic(rows)
    
    def _detect_format(self, first_row: Dict[str, str]) -> str:
        """Detect CSV format from first row"""
        
        headers = set(first_row.keys())
        
        # Format A: Fund_ID, Fund_Name, Date, Price, Quantity, Value
        if all(h in headers for h in ['Fund_ID', 'Fund_Name', 'Date', 'Price']):
            return self.FORMAT_A
        
        # Format B: FundCode, FundName, TradeDate, Value
        if all(h in headers for h in ['FundCode', 'FundName', 'TradeDate', 'Value']):
            return self.FORMAT_B
        
        # Format C: ISIN, FundName, Date_EOM, NAV
        if all(h in headers for h in ['ISIN', 'FundName', 'Date_EOM', 'NAV']):
            return self.FORMAT_C
        
        return self.FORMAT_GENERIC
    
    def _process_format_a(self, rows: List[Dict[str, str]]) -> List[ParsedFund]:
        """Process Format A: Fund_ID, Fund_Name, Date, Price, Quantity, Value"""
        
        parsed = []
        
        for row in rows:
            try:
                fund_id = row.get('Fund_ID', '').strip()
                fund_name = row.get('Fund_Name', '').strip()
                date_str = row.get('Date', '').strip()
                price_str = row.get('Price', '').strip()
                quantity_str = row.get('Quantity', '').strip()
                value_str = row.get('Value', '').strip()
                
                if not all([fund_id, fund_name, date_str, price_str]):
                    continue
                
                date = self._parse_date(date_str)
                price = self._parse_decimal(price_str)
                quantity = self._parse_decimal(quantity_str) if quantity_str else None
                value = self._parse_decimal(value_str) if value_str else None
                
                if date and price:
                    parsed.append(ParsedFund(
                        fund_id=fund_id,
                        fund_name=fund_name,
                        date=date,
                        price=price,
                        quantity=quantity,
                        value=value
                    ))
            except Exception as e:
                # Skip rows with parsing errors
                continue
        
        return parsed
    
    def _process_format_b(self, rows: List[Dict[str, str]]) -> List[ParsedFund]:
        """Process Format B: FundCode, FundName, TradeDate, Value"""
        
        parsed = []
        
        for row in rows:
            try:
                fund_id = row.get('FundCode', '').strip()
                fund_name = row.get('FundName', '').strip()
                date_str = row.get('TradeDate', '').strip()
                value_str = row.get('Value', '').strip()
                
                if not all([fund_id, fund_name, date_str, value_str]):
                    continue
                
                date = self._parse_date(date_str)
                value = self._parse_decimal(value_str)
                
                # For Format B, price equals value (simplified)
                if date and value:
                    parsed.append(ParsedFund(
                        fund_id=fund_id,
                        fund_name=fund_name,
                        date=date,
                        price=value,
                        value=value
                    ))
            except Exception:
                continue
        
        return parsed
    
    def _process_format_c(self, rows: List[Dict[str, str]]) -> List[ParsedFund]:
        """Process Format C: ISIN, FundName, Date_EOM, NAV"""
        
        parsed = []
        
        for row in rows:
            try:
                fund_id = row.get('ISIN', '').strip()
                fund_name = row.get('FundName', '').strip()
                date_str = row.get('Date_EOM', '').strip()
                price_str = row.get('NAV', '').strip()
                
                if not all([fund_id, fund_name, date_str, price_str]):
                    continue
                
                date = self._parse_date(date_str)
                price = self._parse_decimal(price_str)
                
                if date and price:
                    parsed.append(ParsedFund(
                        fund_id=fund_id,
                        fund_name=fund_name,
                        date=date,
                        price=price
                    ))
            except Exception:
                continue
        
        return parsed
    
    def _process_generic(self, rows: List[Dict[str, str]]) -> List[ParsedFund]:
        """Process generic format with flexible column matching"""
        
        parsed = []
        
        for row in rows:
            try:
                # Find columns flexibly
                fund_id = self._find_column(row, ['fund_id', 'isin', 'fundcode', 'code', 'id'])
                fund_name = self._find_column(row, ['fund_name', 'fundname', 'name'])
                date_str = self._find_column(row, ['date', 'tradedate', 'date_eom', 'position_date'])
                price_str = self._find_column(row, ['price', 'nav', 'value', 'close'])
                
                if not all([fund_id, fund_name, date_str, price_str]):
                    continue
                
                date = self._parse_date(date_str)
                price = self._parse_decimal(price_str)
                
                if date and price:
                    parsed.append(ParsedFund(
                        fund_id=fund_id,
                        fund_name=fund_name,
                        date=date,
                        price=price
                    ))
            except Exception:
                continue
        
        return parsed
    
    @staticmethod
    def _find_column(row: Dict[str, str], possible_names: List[str]) -> Optional[str]:
        """Find column value by possible names"""
        
        row_lower = {k.lower(): v for k, v in row.items()}
        
        for name in possible_names:
            if name.lower() in row_lower:
                return row_lower[name.lower()].strip()
        
        return None
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date from various formats"""
        
        formats = [
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d.%m.%Y',
            '%Y.%m.%d',
            '%B %d, %Y',
            '%d %B %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def _parse_decimal(value_str: str) -> Optional[Decimal]:
        """Parse decimal value"""
        
        try:
            # Remove common currency symbols and spaces
            value_str = value_str.strip().replace('$', '').replace('€', '').strip()
            # Handle comma as decimal separator
            if ',' in value_str and '.' in value_str:
                # Has both, need to figure out which is decimal
                if value_str.rfind(',') > value_str.rfind('.'):
                    value_str = value_str.replace('.', '').replace(',', '.')
                else:
                    value_str = value_str.replace(',', '')
            elif ',' in value_str:
                # Only comma, might be thousands or decimal
                if value_str.count(',') == 1 and len(value_str.split(',')[1]) == 2:
                    value_str = value_str.replace(',', '.')
                else:
                    value_str = value_str.replace(',', '')
            
            return Decimal(value_str)
        except:
            return None
