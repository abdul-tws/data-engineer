"""
Analytics Calculator - Calculates monthly returns and identifies best performers
"""

from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Tuple
from database import DatabaseManager


class AnalyticsCalculator:
    """Calculates fund performance analytics"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize analytics calculator"""
        self.db_manager = db_manager
    
    def calculate_monthly_returns(self) -> List[Dict[str, Any]]:
        """
        Calculate monthly returns for all funds
        Return = (Closing Price - Opening Price) / Opening Price * 100
        """
        positions = self.db_manager.get_fund_positions()
        
        # Group positions by fund and month
        fund_months = defaultdict(list)
        
        for position in positions:
            fund_id = position['fund_id']
            fund_name = position['fund_name']
            position_date = position['position_date']
            price = position['position_price']
            
            # Parse date
            try:
                date_obj = datetime.strptime(position_date, '%Y-%m-%d')
                year = date_obj.year
                month = date_obj.month
            except:
                continue
            
            key = (fund_id, fund_name, year, month)
            fund_months[key].append({
                'date': date_obj,
                'price': price
            })
        
        # Calculate returns
        monthly_returns = []
        
        for (fund_id, fund_name, year, month), prices in fund_months.items():
            if len(prices) < 2:
                # Need at least opening and closing price
                continue
            
            # Sort by date
            prices.sort(key=lambda x: x['date'])
            
            opening_price = prices[0]['price']
            closing_price = prices[-1]['price']
            
            # Calculate returns
            monthly_return = closing_price - opening_price
            monthly_return_pct = (monthly_return / opening_price * 100) if opening_price != 0 else 0
            
            monthly_returns.append({
                'fund_id': fund_id,
                'fund_name': fund_name,
                'year': year,
                'month': month,
                'opening_price': opening_price,
                'closing_price': closing_price,
                'monthly_return': monthly_return,
                'monthly_return_pct': monthly_return_pct
            })
            
            # Store in database
            self.db_manager.insert_monthly_return(
                fund_id, fund_name, year, month,
                opening_price, closing_price,
                monthly_return, monthly_return_pct
            )
        
        return monthly_returns
    
    def identify_best_performers(self) -> List[Dict[str, Any]]:
        """
        Identify best performing fund for each month
        Returns highest return % per month
        """
        monthly_returns = self.db_manager.get_monthly_returns()
        
        # Group by year-month
        month_groups = defaultdict(list)
        
        for entry in monthly_returns:
            year = entry['year']
            month = entry['month']
            key = (year, month)
            month_groups[key].append(entry)
        
        # Find best for each month
        best_by_month = []
        
        for (year, month), entries in sorted(month_groups.items()):
            if entries:
                # Find best performer (highest return %)
                best_entry = max(entries, key=lambda x: x['monthly_return_pct'])
                
                best_by_month.append({
                    'year': year,
                    'month': month,
                    'month_label': self._get_month_label(year, month),
                    'fund_id': best_entry['fund_id'],
                    'fund_name': best_entry['fund_name'],
                    'monthly_return': best_entry['monthly_return'],
                    'monthly_return_pct': best_entry['monthly_return_pct'],
                    'opening_price': best_entry['opening_price'],
                    'closing_price': best_entry['closing_price']
                })
        
        return best_by_month
    
    @staticmethod
    def _get_month_label(year: int, month: int) -> str:
        """Get month label (e.g., 'January 2024')"""
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return f"{month_names[month-1]} {year}"
