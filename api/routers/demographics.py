"""
Demographics API Router

Endpoints for fetching demographic data.
"""
from fastapi import APIRouter, Depends, Query
from sqlite3 import Connection
from typing import List, Optional

from api.database import get_db
from api.models import DemographicsResponse

router = APIRouter()


@router.get("/demographics", response_model=List[DemographicsResponse])
async def get_demographics(
    barrio_id: Optional[int] = Query(None, description="Filter by barrio ID"),
    year: Optional[int] = Query(None, description="Filter by year"),
    year_start: Optional[int] = Query(None, description="Filter by year range start"),
    year_end: Optional[int] = Query(None, description="Filter by year range end"),
    db: Connection = Depends(get_db)
):
    """
    Get demographics data with optional filters.
    
    Returns standard demographics from fact_demografia table.
    """
    query = """
        SELECT 
            d.barrio_id,
            d.anio,
            d.poblacion_total as poblacion,
            NULL as sexo,
            NULL as grupo_edad,
            NULL as nacionalidad
        FROM fact_demografia d
        WHERE 1=1
    """
    params = []
    
    if barrio_id is not None:
        query += " AND d.barrio_id = ?"
        params.append(barrio_id)
    
    if year is not None:
        query += " AND d.anio = ?"
        params.append(year)
    
    if year_start is not None:
        query += " AND d.anio >= ?"
        params.append(year_start)
    
    if year_end is not None:
        query += " AND d.anio <= ?"
        params.append(year_end)
    
    query += " ORDER BY d.anio DESC, d.barrio_id"
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/demographics/extended", response_model=List[DemographicsResponse])
async def get_extended_demographics(
    barrio_id: Optional[int] = Query(None, description="Filter by barrio ID"),
    year: Optional[int] = Query(None, description="Filter by year"),
    year_start: Optional[int] = Query(None, description="Filter by year range start"),
    year_end: Optional[int] = Query(None, description="Filter by year range end"),
    db: Connection = Depends(get_db)
):
    """
    Get extended demographics with age groups and nationality.
    
    Returns data from fact_demografia_ampliada table.
    """
    query = """
        SELECT 
            barrio_id,
            anio,
            poblacion,
            sexo,
            grupo_edad,
            nacionalidad
        FROM fact_demografia_ampliada
        WHERE 1=1
    """
    params = []
    
    if barrio_id is not None:
        query += " AND barrio_id = ?"
        params.append(barrio_id)
    
    if year is not None:
        query += " AND anio = ?"
        params.append(year)
    
    if year_start is not None:
        query += " AND anio >= ?"
        params.append(year_start)
    
    if year_end is not None:
        query += " AND anio <= ?"
        params.append(year_end)
    
    query += " ORDER BY anio DESC, barrio_id"
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/demographics/trends/{barrio_id}", response_model=List[DemographicsResponse])
async def get_demographic_trends(
    barrio_id: int,
    year_start: Optional[int] = Query(None, description="Start year"),
    year_end: Optional[int] = Query(None, description="End year"),
    db: Connection = Depends(get_db)
):
    """
    Get demographic trends over time for a specific barrio.
    
    Returns time series of population data.
    """
    query = """
        SELECT 
            d.barrio_id,
            d.anio,
            d.poblacion_total as poblacion,
            NULL as sexo,
            NULL as grupo_edad,
            NULL as nacionalidad
        FROM fact_demografia d
        WHERE d.barrio_id = ?
    """
    params = [barrio_id]
    
    if year_start is not None:
        query += " AND d.anio >= ?"
        params.append(year_start)
    
    if year_end is not None:
        query += " AND d.anio <= ?"
        params.append(year_end)
    
    query += " ORDER BY d.anio"
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]
