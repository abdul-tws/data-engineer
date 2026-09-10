"""
Price Reconciler - Reconciles fund prices with reference prices
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import DatabaseManager


class PriceReconciler:
    """Reconciles fund prices with reference data"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize reconciler"""
        self.db_manager = db_manager
    
    def reconcile_all_funds(self) -> List[Dict[str, Any]]:
        """Reconcile all fund positions with reference prices"""
        positions = self.db_manager.get_fund_positions()
        reconciliation_results = []
        
        for position in positions:
            result = self.reconcile_position(position)
            if result:
                reconciliation_results.append(result)
                self._store_reconciliation(result)
        
        return reconciliation_results
    
    def reconcile_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconcile single fund position
        - Looks for exact EOM date match
        - Falls back to latest available reference price
        """
        fund_id = position['fund_id']
        position_date = position['position_date']
        position_price = position['position_price']
        
        # Get reference price
        ref_result = self.db_manager.get_reference_price(fund_id, position_date)
        
        if not ref_result:
            # No reference price found
            return {
                'fund_id': fund_id,
                'position_date': position_date,
                'position_price': position_price,
                'reference_price': None,
                'reference_date': None,
                'price_variance': None,
                'variance_pct': None,
                'reconciliation_status': 'NO_REFERENCE_DATA'
            }
        
        reference_price, reference_date = ref_result
        
        # Calculate variance
        price_variance = position_price - reference_price
        variance_pct = (price_variance / reference_price * 100) if reference_price != 0 else 0
        
        # Determine reconciliation status
        status = self._determine_status(position_date, reference_date, variance_pct)
        
        return {
            'fund_id': fund_id,
            'position_date': position_date,
            'position_price': position_price,
            'reference_price': reference_price,
            'reference_date': reference_date,
            'price_variance': price_variance,
            'variance_pct': variance_pct,
            'reconciliation_status': status
        }
    
    def _determine_status(self, position_date: str, reference_date: str, variance_pct: float) -> str:
        """
        Determine reconciliation status based on:
        - Date match (exact EOM vs fallback)
        - Price variance threshold
        """
        # Parse dates
        try:
            pos_date = datetime.strptime(position_date, '%Y-%m-%d')
            ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
        except:
            return 'ERROR'
        
        # Check if dates match exactly
        if pos_date == ref_date:
            if abs(variance_pct) < 0.01:  # Less than 0.01%
                return 'EXACT_MATCH'
            elif abs(variance_pct) < 0.1:  # Less than 0.1%
                return 'MATCHED_MINOR_VARIANCE'
            elif abs(variance_pct) < 1.0:  # Less than 1%
                return 'MATCHED_ACCEPTABLE_VARIANCE'
            else:
                return 'MATCHED_HIGH_VARIANCE'
        
        # Dates don't match - using fallback
        days_diff = abs((pos_date - ref_date).days)
        
        if days_diff <= 1:
            return 'FALLBACK_SAME_DAY'
        elif days_diff <= 7:
            return 'FALLBACK_WITHIN_WEEK'
        elif days_diff <= 31:
            return 'FALLBACK_WITHIN_MONTH'
        else:
            return 'FALLBACK_STALE_DATA'
    
    def _store_reconciliation(self, result: Dict[str, Any]):
        """Store reconciliation result in database"""
        self.db_manager.insert_reconciled_price(
            fund_id=result['fund_id'],
            position_date=result['position_date'],
            position_price=result['position_price'],
            reference_price=result['reference_price'],
            reference_date=result['reference_date'],
            price_variance=result['price_variance'],
            variance_pct=result['variance_pct'],
            status=result['reconciliation_status']
        )
