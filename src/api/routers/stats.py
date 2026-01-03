"""Stats router - endpoints for aggregated data and KPIs."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from ..services import get_db_service

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/years")
async def get_available_years():
    """Get min and max years for various fact tables."""
    db = get_db_service()
    return db.get_available_years()

@router.get("/distritos")
async def get_distritos():
    """Get list of unique distritos."""
    db = get_db_service()
    return db.get_distritos()

@router.get("/precios")
async def get_precios(
    year: int = Query(2023, description="Year to fetch prices for"),
    distrito: Optional[str] = Query(None, description="Optional district filter"),
    include_geometry: bool = Query(False, description="Whether to include GeoJSON geometry")
):
    """Get average prices per barrio for a given year."""
    db = get_db_service()
    return db.get_precios(year, distrito, include_geometry)

@router.get("/renta")
async def get_renta(
    year: int = Query(2023, description="Year to fetch income for")
):
    """Get average income per barrio for a given year."""
    db = get_db_service()
    return db.get_renta(year)

@router.get("/kpis")
async def get_kpis():
    """Get global project KPIs."""
    db = get_db_service()
    return db.get_kpis()

@router.get("/investment")
async def get_investment_stats(
    year: int = Query(2023, description="Year to fetch investment metrics for")
):
    """Get specialized investment metrics (Offer Prices vs Contract Rents)."""
    db = get_db_service()
    return db.get_investment_metrics(year)
