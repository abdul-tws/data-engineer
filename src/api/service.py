"""
API Service Layer
Bridges API layer with core business logic
"""

from typing import List, Dict, Tuple
from pathlib import Path
from decimal import Decimal
from datetime import datetime

from src.core import (
    ReconciliationEngine,
    AnalyticsEngine,
    CSVProcessor,
    Position,
    PricePoint,
    PriceSnapshot,
)


class ReconciliationService:
    """Service for reconciliation operations"""
    
    def __init__(self):
        self.engine = ReconciliationEngine()
        self.analytics_engine = AnalyticsEngine()
        self.csv_processor = CSVProcessor()
        
        # In-memory storage
        self.positions: List[Position] = []
        self.reference_prices: List[PricePoint] = []
        self.reconciliation_results = []
        self.monthly_returns = []
    
    def add_position(self, 
                    fund_id: str,
                    position_date: datetime,
                    position_price: Decimal,
                    quantity: Decimal = None) -> Dict:
        """Add a fund position"""
        position = Position(
            fund_id=fund_id,
            date=position_date,
            price=position_price,
            quantity=quantity
        )
        self.positions.append(position)
        return {"status": "added", "fund_id": fund_id}
    
    def add_reference_price(self,
                           fund_id: str,
                           price_date: datetime,
                           price: Decimal) -> Dict:
        """Add a reference price"""
        ref = PricePoint(
            fund_id=fund_id,
            date=price_date,
            price=price
        )
        self.reference_prices.append(ref)
        return {"status": "added", "fund_id": fund_id}
    
    def process_csv(self, file_path: Path) -> Dict:
        """Process a CSV file"""
        parsed_funds = self.csv_processor.process_file(file_path)
        
        for pf in parsed_funds:
            self.add_position(pf.fund_id, pf.date, pf.price, pf.quantity)
        
        return {"status": "processed", "count": len(parsed_funds)}
    
    def reconcile_all(self) -> Dict:
        """Reconcile all positions"""
        if not self.positions or not self.reference_prices:
            return {
                "status": "no_data",
                "total": 0,
                "exact_matches": 0,
                "variance_matches": 0,
                "no_reference": 0
            }
        
        # Reconcile
        self.reconciliation_results = self.engine.reconcile_positions(
            self.positions,
            self.reference_prices
        )
        
        # Calculate stats
        exact = sum(1 for r in self.reconciliation_results if r.status == "EXACT_MATCH")
        variance = sum(1 for r in self.reconciliation_results if "VARIANCE" in r.status)
        no_ref = sum(1 for r in self.reconciliation_results if r.status == "NO_REFERENCE_DATA")
        
        return {
            "status": "reconciled",
            "total": len(self.reconciliation_results),
            "exact_matches": exact,
            "variance_matches": variance,
            "no_reference": no_ref,
            "flagged": sum(1 for r in self.reconciliation_results if r.is_flagged)
        }
    
    def calculate_analytics(self) -> Dict:
        """Calculate analytics"""
        if not self.positions:
            return {"status": "no_data", "monthly_returns": 0}
        
        # Group positions by fund
        fund_prices: Dict[str, Tuple] = {}
        
        for position in self.positions:
            if position.fund_id not in fund_prices:
                fund_prices[position.fund_id] = ("Fund_" + position.fund_id, [])
            
            snapshot = PriceSnapshot(
                fund_id=position.fund_id,
                date=position.date,
                price=position.price
            )
            fund_prices[position.fund_id][1].append(snapshot)
        
        # Calculate returns
        self.monthly_returns = self.analytics_engine.calculate_all_returns(fund_prices)
        
        best_performers = sum(1 for r in self.monthly_returns if r.is_best_performer)
        
        return {
            "status": "calculated",
            "monthly_returns": len(self.monthly_returns),
            "best_performers": best_performers
        }
    
    def get_reconciliation_report(self) -> Dict:
        """Get reconciliation report"""
        if not self.reconciliation_results:
            return {
                "total_records": 0,
                "exact_matches": 0,
                "variance_matches": 0,
                "no_reference": 0,
                "flagged": 0,
                "avg_variance_pct": 0.0
            }
        
        exact = sum(1 for r in self.reconciliation_results if r.status == "EXACT_MATCH")
        variance = sum(1 for r in self.reconciliation_results if "VARIANCE" in r.status)
        no_ref = sum(1 for r in self.reconciliation_results if r.status == "NO_REFERENCE_DATA")
        flagged = sum(1 for r in self.reconciliation_results if r.is_flagged)
        
        avg_variance = 0.0
        if self.reconciliation_results:
            variances = [abs(r.variance_pct or 0) for r in self.reconciliation_results]
            avg_variance = sum(variances) / len(variances)
        
        return {
            "total_records": len(self.reconciliation_results),
            "exact_matches": exact,
            "variance_matches": variance,
            "no_reference": no_ref,
            "flagged": flagged,
            "avg_variance_pct": avg_variance
        }
    
    def get_best_performers(self) -> List[Dict]:
        """Get best performers"""
        best = [r for r in self.monthly_returns if r.is_best_performer]
        
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        return [
            {
                "year": perf.year,
                "month": perf.month,
                "month_label": f"{month_names[perf.month]} {perf.year}",
                "fund_id": perf.fund_id,
                "monthly_return_pct": perf.monthly_return_pct,
                "opening_price": str(perf.opening_price),
                "closing_price": str(perf.closing_price)
            }
            for perf in best
        ]
    
    def clear_data(self) -> Dict:
        """Clear all data"""
        self.positions.clear()
        self.reference_prices.clear()
        self.reconciliation_results.clear()
        self.monthly_returns.clear()
        return {"status": "cleared"}


# Global service instance
_service = None


def get_service() -> ReconciliationService:
    """Get or create service instance"""
    global _service
    if _service is None:
        _service = ReconciliationService()
    return _service
