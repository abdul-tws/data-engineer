"""
API Layer
FastAPI REST interface for fund reconciliation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from src.api.routes import router
from src.api.models import APIResponse, HealthResponse

# Create FastAPI app
app = FastAPI(
    title="Fund Reconciliation API v2.0",
    description="Production-grade fund position reconciliation REST API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "Fund Reconciliation API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "redoc": "/redoc"
    }


@app.get("/api/v1")
async def api_root():
    """API v1 root"""
    return {
        "version": "1.0",
        "endpoints": {
            "health": "GET /api/v1/health",
            "add_position": "POST /api/v1/funds/add-position",
            "add_reference_price": "POST /api/v1/reference-prices/add",
            "reconcile": "POST /api/v1/reconciliation/execute",
            "analytics": "POST /api/v1/analytics/calculate",
            "report": "GET /api/v1/reconciliation/report",
            "best_performers": "GET /api/v1/analytics/best-performers",
            "data_stats": "GET /api/v1/data/stats",
            "clear_data": "POST /api/v1/data/clear",
            "full_workflow": "POST /api/v1/workflow/full-reconciliation"
        }
    }


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("\n" + "="*60)
    print("🚀 Fund Reconciliation API v2.0 Started")
    print("="*60)
    print("📚 API Docs: http://localhost:8000/docs")
    print("💚 Health: http://localhost:8000/api/v1/health")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    print("\n" + "="*60)
    print("🛑 Fund Reconciliation API Stopped")
    print("="*60 + "\n")


__all__ = ["app"]
