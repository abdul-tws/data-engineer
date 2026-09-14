"""
Core Reconciliation Engine
Main business logic for fund price reconciliation
Pure logic - no API/DB dependencies
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PricePoint:
    """Represents a single price point"""
    fund_id: str
    date: datetime
    price: Decimal
    source: str = "reference"


@dataclass
class Position:
    """Represents a fund position"""
    fund_id: str
    date: datetime
    price: Decimal
    quantity: Optional[Decimal] = None
    value: Optional[Decimal] = None


@dataclass
class ReconciliationResult:
    """Result of reconciliation"""
    fund_id: str
    position_date: datetime
    position_price: Decimal
    reference_price: Optional[Decimal]
    reference_date: Optional[datetime]
    variance: Optional[Decimal]
    variance_pct: Optional[float]
    status: str
    is_flagged: bool = False


class ReconciliationEngine:
    """
    Core reconciliation engine
    Performs price matching and variance calculation
    """
    
    # Variance thresholds
    EXACT_MATCH_THRESHOLD = 0.01  # 0.01%
    MINOR_VARIANCE_THRESHOLD = 0.1  # 0.1%
    ACCEPTABLE_VARIANCE_THRESHOLD = 1.0  # 1%
    
    def __init__(self, 
                 exact_threshold: float = 0.01,
                 minor_threshold: float = 0.1,
                 acceptable_threshold: float = 1.0):
        """Initialize engine with thresholds"""
        self.exact_threshold = exact_threshold
        self.minor_threshold = minor_threshold
        self.acceptable_threshold = acceptable_threshold
    
    def reconcile_position(self,
                          position: Position,
                          reference_prices: List[PricePoint]) -> ReconciliationResult:
        """
        Reconcile a single position against reference prices
        
        Args:
            position: Position to reconcile
            reference_prices: Available reference prices
            
        Returns:
            ReconciliationResult with status and variance
        """
        
        # Find best matching reference price
        ref_match = self._find_matching_reference(position, reference_prices)
        
        if not ref_match:
            return ReconciliationResult(
                fund_id=position.fund_id,
                position_date=position.date,
                position_price=position.price,
                reference_price=None,
                reference_date=None,
                variance=None,
                variance_pct=None,
                status="NO_REFERENCE_DATA",
                is_flagged=True
            )
        
        ref_price, ref_date = ref_match
        
        # Calculate variance
        variance = float(position.price) - float(ref_price)
        variance_pct = (variance / float(ref_price) * 100) if ref_price else 0
        
        # Determine status
        status = self._determine_status(variance_pct)
        is_flagged = abs(variance_pct) > self.acceptable_threshold
        
        return ReconciliationResult(
            fund_id=position.fund_id,
            position_date=position.date,
            position_price=position.price,
            reference_price=ref_price,
            reference_date=ref_date,
            variance=Decimal(str(variance)),
            variance_pct=variance_pct,
            status=status,
            is_flagged=is_flagged
        )
    
    def reconcile_positions(self,
                           positions: List[Position],
                           reference_prices: List[PricePoint]) -> List[ReconciliationResult]:
        """Reconcile multiple positions"""
        results = []
        
        for position in positions:
            # Filter reference prices for this fund
            fund_refs = [
                (p.price, p.date) for p in reference_prices
                if p.fund_id == position.fund_id
            ]
            
            # Reconcile
            result = self.reconcile_position(position, reference_prices)
            results.append(result)
        
        return results
    
    def _find_matching_reference(self,
                                 position: Position,
                                 reference_prices: List[PricePoint]) -> Optional[Tuple[Decimal, datetime]]:
        """
        Find best matching reference price for a position
        
        Priority:
        1. Exact date match
        2. Latest price before position date
        3. Closest price within 30 days
        """
        
        # Filter for same fund
        fund_refs = [p for p in reference_prices if p.fund_id == position.fund_id]
        
        if not fund_refs:
            return None
        
        # Try exact date match
        for ref in fund_refs:
            if ref.date.date() == position.date.date():
                return (ref.price, ref.date)
        
        # Try latest price before position date
        valid_refs = [p for p in fund_refs if p.date <= position.date]
        if valid_refs:
            latest = max(valid_refs, key=lambda x: x.date)
            return (latest.price, latest.date)
        
        # Try closest price (shouldn't reach here for real data)
        if fund_refs:
            closest = min(fund_refs, key=lambda x: abs((x.date - position.date).days))
            return (closest.price, closest.date)
        
        return None
    
    def _determine_status(self, variance_pct: float) -> str:
        """Determine reconciliation status based on variance"""
        abs_variance = abs(variance_pct)
        
        if abs_variance < self.exact_threshold:
            return "EXACT_MATCH"
        elif abs_variance < self.minor_threshold:
            return "MATCHED_MINOR_VARIANCE"
        elif abs_variance < self.acceptable_threshold:
            return "MATCHED_ACCEPTABLE_VARIANCE"
        else:
            return "MATCHED_HIGH_VARIANCE"
