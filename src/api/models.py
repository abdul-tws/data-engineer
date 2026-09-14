"""
API Request/Response Models
Pydantic schemas for FastAPI endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class FundCreate(BaseModel):
    """Create fund request"""
    fund_id: str = Field(..., min_length=1, max_length=50)
    fund_name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(default="USD", max_length=3)


class ReferencePriceCreate(BaseModel):
    """Create reference price request"""
    fund_id: str = Field(..., min_length=1)
    price_date: datetime
    price: Decimal = Field(..., gt=0)


class PositionCreate(BaseModel):
    """Create fund position request"""
    fund_id: str = Field(..., min_length=1)
    position_date: datetime
    position_price: Decimal = Field(..., gt=0)
    quantity: Optional[Decimal] = None


# ============================================================================
# Response Models
# ============================================================================

class FundResponse(FundCreate):
    """Fund response"""
    id: int
    created_at: datetime


class ReferencePriceResponse(BaseModel):
    """Reference price response"""
    fund_id: str
    price_date: datetime
    price: Decimal


class ReconciliationResultResponse(BaseModel):
    """Reconciliation result response"""
    fund_id: str
    position_date: datetime
    position_price: Decimal
    reference_price: Optional[Decimal]
    variance_pct: Optional[float]
    status: str
    is_flagged: bool


class ReconciledReport(BaseModel):
    """Reconciliation report"""
    total_records: int
    exact_matches: int
    variance_matches: int
    no_reference: int
    flagged: int
    avg_variance_pct: float


class MonthlyReturnResponse(BaseModel):
    """Monthly return response"""
    fund_id: str
    year: int
    month: int
    monthly_return_pct: float
    opening_price: Decimal
    closing_price: Decimal
    is_best_performer: bool


class BestPerformerResponse(BaseModel):
    """Best performer response"""
    year: int
    month: int
    month_label: str
    fund_id: str
    monthly_return_pct: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str = "2.0.0"


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
