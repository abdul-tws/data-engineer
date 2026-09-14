"""
Analytics Engine
Calculates fund performance metrics and returns
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PriceSnapshot:
    """Price snapshot for a specific date"""
    fund_id: str
    date: datetime
    price: Decimal


@dataclass
class MonthlyReturnData:
    """Monthly return for a fund"""
    fund_id: str
    fund_name: str
    year: int
    month: int
    opening_price: Decimal
    closing_price: Decimal
    monthly_return: Decimal
    monthly_return_pct: float
    is_best_performer: bool = False


class AnalyticsEngine:
    """
    Analytics engine
    Calculates performance metrics and returns
    """
    
    def __init__(self):
        """Initialize analytics engine"""
        pass
    
    def calculate_monthly_returns(self,
                                 fund_id: str,
                                 fund_name: str,
                                 prices: List[PriceSnapshot]) -> List[MonthlyReturnData]:
        """
        Calculate monthly returns for a fund
        
        Args:
            fund_id: Fund identifier
            fund_name: Fund name
            prices: List of price snapshots
            
        Returns:
            List of monthly return data
        """
        
        if not prices:
            return []
        
        # Group prices by year-month
        by_month: Dict[Tuple[int, int], List[PriceSnapshot]] = defaultdict(list)
        
        for price in prices:
            year = price.date.year
            month = price.date.month
            by_month[(year, month)].append(price)
        
        # Calculate returns for each month
        returns = []
        
        for (year, month), month_prices in sorted(by_month.items()):
            if not month_prices:
                continue
            
            # Sort by date
            month_prices.sort(key=lambda x: x.date)
            
            # Get opening (first) and closing (last) prices
            opening = month_prices[0].price
            closing = month_prices[-1].price
            
            # Calculate return
            monthly_return = closing - opening
            monthly_return_pct = (float(monthly_return) / float(opening) * 100) if opening else 0
            
            return_data = MonthlyReturnData(
                fund_id=fund_id,
                fund_name=fund_name,
                year=year,
                month=month,
                opening_price=opening,
                closing_price=closing,
                monthly_return=monthly_return,
                monthly_return_pct=monthly_return_pct
            )
            
            returns.append(return_data)
        
        # Identify best performers
        self._mark_best_performers(returns)
        
        return returns
    
    def calculate_all_returns(self,
                             fund_prices: Dict[str, Tuple[str, List[PriceSnapshot]]]) -> List[MonthlyReturnData]:
        """
        Calculate returns for multiple funds
        
        Args:
            fund_prices: Dict of fund_id -> (fund_name, prices)
            
        Returns:
            List of all monthly returns
        """
        
        all_returns = []
        
        for fund_id, (fund_name, prices) in fund_prices.items():
            returns = self.calculate_monthly_returns(fund_id, fund_name, prices)
            all_returns.extend(returns)
        
        return all_returns
    
    def get_best_performers(self,
                           returns: List[MonthlyReturnData]) -> List[MonthlyReturnData]:
        """
        Get best performing fund for each month
        
        Args:
            returns: List of all monthly returns
            
        Returns:
            List of best performers only
        """
        
        # Group by year-month
        by_month: Dict[Tuple[int, int], List[MonthlyReturnData]] = defaultdict(list)
        
        for ret in returns:
            by_month[(ret.year, ret.month)].append(ret)
        
        # Get best performer for each month
        best = []
        
        for (year, month), month_returns in by_month.items():
            if not month_returns:
                continue
            
            # Find highest return
            best_ret = max(month_returns, key=lambda x: x.monthly_return_pct)
            best_ret.is_best_performer = True
            best.append(best_ret)
        
        return best
    
    def _mark_best_performers(self, returns: List[MonthlyReturnData]) -> None:
        """Mark best performers in place"""
        
        # Group by year-month
        by_month: Dict[Tuple[int, int], List[MonthlyReturnData]] = defaultdict(list)
        
        for ret in returns:
            by_month[(ret.year, ret.month)].append(ret)
        
        # Mark best for each month
        for (year, month), month_returns in by_month.items():
            if month_returns:
                best = max(month_returns, key=lambda x: x.monthly_return_pct)
                best.is_best_performer = True
    
    def calculate_statistics(self,
                            returns: List[MonthlyReturnData]) -> Dict[str, any]:
        """
        Calculate aggregate statistics
        
        Args:
            returns: List of monthly returns
            
        Returns:
            Dictionary with statistics
        """
        
        if not returns:
            return {}
        
        return_percentages = [r.monthly_return_pct for r in returns]
        
        return {
            "total_records": len(returns),
            "best_performers": sum(1 for r in returns if r.is_best_performer),
            "avg_return_pct": sum(return_percentages) / len(return_percentages),
            "max_return_pct": max(return_percentages),
            "min_return_pct": min(return_percentages),
            "positive_months": sum(1 for r in return_percentages if r > 0),
            "negative_months": sum(1 for r in return_percentages if r < 0),
            "flat_months": sum(1 for r in return_percentages if r == 0),
        }
