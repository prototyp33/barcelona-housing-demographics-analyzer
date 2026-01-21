"""Equity router - endpoints for model fairness and equity metrics."""

from fastapi import APIRouter
from typing import List, Dict, Any
from ..services import get_db_service

router = APIRouter(prefix="/equity", tags=["equity"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_equity():
    """Get model fairness/equity metrics (MAE, R2, GES, IPR) by district.
    
    Returns:
        List of equity metrics for models
    """
    db = get_db_service()
    return db.get_equity_metrics()
