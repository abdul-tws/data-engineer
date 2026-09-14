"""
API Routes
FastAPI endpoint definitions
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from datetime import datetime
from decimal import Decimal
from typing import List

from src.api.models import (
    FundCreate, FundResponse,
    ReferencePriceCreate, ReferencePriceResponse,
    PositionCreate,
    ReconciliationResultResponse,
    ReconciledReport,
    MonthlyReturnResponse,
    BestPerformerResponse,
    HealthResponse,
    APIResponse
)
from src.api.service import get_service

# Create router
router = APIRouter(prefix="/api/v1", tags=["reconciliation"])


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check"""
    return HealthResponse(
        status="HEALTHY",
        timestamp=datetime.utcnow(),
        version="2.0.0"
    )


# ============================================================================
# Fund Operations
# ============================================================================

@router.post("/funds/add-position")
async def add_position(position: PositionCreate):
    """Add fund position"""
    service = get_service()
    result = service.add_position(
        fund_id=position.fund_id,
        position_date=position.position_date,
        position_price=position.position_price,
        quantity=position.quantity
    )
    return APIResponse(
        success=True,
        message="Position added successfully",
        data=result
    )


@router.post("/reference-prices/add")
async def add_reference_price(price: ReferencePriceCreate):
    """Add reference price"""
    service = get_service()
    result = service.add_reference_price(
        fund_id=price.fund_id,
        price_date=price.price_date,
        price=price.price
    )
    return APIResponse(
        success=True,
        message="Reference price added successfully",
        data=result
    )


# ============================================================================
# Reconciliation Operations
# ============================================================================

@router.post("/reconciliation/execute")
async def execute_reconciliation():
    """Execute reconciliation"""
    service = get_service()
    result = service.reconcile_all()
    
    if result["status"] == "no_data":
        raise HTTPException(
            status_code=400,
            detail="No positions or reference prices loaded"
        )
    
    return APIResponse(
        success=True,
        message="Reconciliation completed successfully",
        data=result
    )


@router.get("/reconciliation/report")
async def get_reconciliation_report():
    """Get reconciliation report"""
    service = get_service()
    report = service.get_reconciliation_report()
    
    return APIResponse(
        success=True,
        message="Report generated successfully",
        data=report
    )


# ============================================================================
# Analytics Operations
# ============================================================================

@router.post("/analytics/calculate")
async def calculate_analytics():
    """Calculate analytics"""
    service = get_service()
    result = service.calculate_analytics()
    
    if result["status"] == "no_data":
        raise HTTPException(
            status_code=400,
            detail="No positions loaded"
        )
    
    return APIResponse(
        success=True,
        message="Analytics calculated successfully",
        data=result
    )


@router.get("/analytics/best-performers")
async def get_best_performers():
    """Get best performing funds"""
    service = get_service()
    best = service.get_best_performers()
    
    return APIResponse(
        success=True,
        message="Best performers retrieved successfully",
        data={"performers": best}
    )


# ============================================================================
# Data Management
# ============================================================================

@router.post("/data/clear")
async def clear_all_data():
    """Clear all loaded data"""
    service = get_service()
    result = service.clear_data()
    
    return APIResponse(
        success=True,
        message="All data cleared successfully",
        data=result
    )


@router.get("/data/stats")
async def get_data_stats():
    """Get current data statistics"""
    service = get_service()
    
    return APIResponse(
        success=True,
        message="Data statistics retrieved successfully",
        data={
            "positions": len(service.positions),
            "reference_prices": len(service.reference_prices),
            "reconciliation_results": len(service.reconciliation_results),
            "monthly_returns": len(service.monthly_returns)
        }
    )


# ============================================================================
# Full Workflow
# ============================================================================

@router.post("/workflow/full-reconciliation")
async def full_workflow():
    """Execute full reconciliation workflow"""
    service = get_service()
    
    try:
        # Step 1: Reconcile
        recon_result = service.reconcile_all()
        if recon_result["status"] == "no_data":
            raise HTTPException(
                status_code=400,
                detail="No data loaded. Add positions and reference prices first."
            )
        
        # Step 2: Calculate analytics
        analytics_result = service.calculate_analytics()
        
        # Step 3: Get report
        report = service.get_reconciliation_report()
        best = service.get_best_performers()
        
        return APIResponse(
            success=True,
            message="Full workflow completed successfully",
            data={
                "reconciliation": recon_result,
                "analytics": analytics_result,
                "report": report,
                "best_performers": best
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
