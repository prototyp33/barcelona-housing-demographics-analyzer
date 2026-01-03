"""Barrios router - endpoints for neighborhood data."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from ..models import BarrioBase, BarrioDetail
from ..services import get_db_service

router = APIRouter(prefix="/barrios", tags=["barrios"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_barrios(
    distrito: Optional[str] = Query(None, description="Filter by distrito name"),
    include_geometry: bool = Query(False, description="Whether to include GeoJSON geometry")
):
    """Get list of all barrios, optionally filtered by distrito.
    
    Args:
        distrito: Optional distrito name filter
        include_geometry: Whether to include GeoJSON geometry
        
    Returns:
        List of barrios with basic information
    """
    db = get_db_service()
    barrios = db.get_barrios(distrito=distrito, include_geometry=include_geometry)
    
    if not barrios:
        return []
    
    return barrios


@router.get("/{barrio_id}", response_model=BarrioDetail)
async def get_barrio(barrio_id: int):
    """Get detailed information for a specific barrio.
    
    Args:
        barrio_id: Barrio ID
        
    Returns:
        Detailed barrio information
        
    Raises:
        HTTPException: If barrio not found
    """
    db = get_db_service()
    barrio = db.get_barrio_detail(barrio_id)
    
    if barrio is None:
        raise HTTPException(status_code=404, detail=f"Barrio {barrio_id} not found")
    
    return barrio
