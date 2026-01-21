"""Accessibility router - endpoints for social infrastructure and safety."""

from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from ..services import get_db_service

router = APIRouter(prefix="/accessibility", tags=["accessibility"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_accessibility(
    year: int = Query(2023, description="Year of data"),
    distrito: Optional[str] = Query(None, description="Filter by distrito name")
):
    """Get accessibility metrics (Education & Public Housing) by neighborhood.
    
    Returns:
        List of neighborhoods with education and housing metrics
    """
    db = get_db_service()
    return db.get_accessibility_metrics(year=year, distrito=distrito)


@router.get("/safety", response_model=List[Dict[str, Any]])
async def get_safety_and_tourism(
    year: int = Query(2023, description="Year of data"),
    distrito: Optional[str] = Query(None, description="Filter by distrito name")
):
    """Get safety and tourism pressure metrics by neighborhood.
    
    Returns:
        List of neighborhoods with crime and tourism metrics
    """
    db = get_db_service()
    return db.get_safety_and_tourism(year=year, distrito=distrito)
