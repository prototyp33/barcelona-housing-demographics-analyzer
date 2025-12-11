"""
Barrios (Neighborhoods) API Router

Endpoints for fetching barrio (neighborhood) data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlite3 import Connection
from typing import List

from api.database import get_db
from api.models import BarrioResponse

router = APIRouter()


@router.get("/barrios", response_model=List[BarrioResponse])
async def get_barrios(
    include_geometry: bool = Query(False, description="Include GeoJSON geometry"),
    db: Connection = Depends(get_db)
):
    """
    Get all barrios (neighborhoods).
    
    - **include_geometry**: If true, includes geometry_json field for mapping
    """
    if include_geometry:
        query = """
            SELECT barrio_id, barrio_nombre, distrito_nombre, geometry_json
            FROM dim_barrios
            ORDER BY barrio_nombre
        """
    else:
        query = """
            SELECT barrio_id, barrio_nombre, distrito_nombre, NULL as geometry_json
            FROM dim_barrios
            ORDER BY barrio_nombre
        """
    
    cursor = db.execute(query)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/barrios/{barrio_id}", response_model=BarrioResponse)
async def get_barrio_by_id(
    barrio_id: int,
    db: Connection = Depends(get_db)
):
    """
    Get a specific barrio by ID.
    
    - **barrio_id**: Unique barrio identifier
    """
    query = """
        SELECT barrio_id, barrio_nombre, distrito_nombre, geometry_json
        FROM dim_barrios
        WHERE barrio_id = ?
    """
    
    cursor = db.execute(query, (barrio_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Barrio {barrio_id} not found")
    
    return dict(row)
