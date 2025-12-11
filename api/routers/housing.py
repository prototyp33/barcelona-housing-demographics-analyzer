"""
Housing API Router

Endpoints for housing prices, rent data, and yield calculations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlite3 import Connection
from typing import List, Optional

from api.database import get_db
from api.models import HousingPriceResponse, RentResponse, YieldResponse

router = APIRouter()


@router.get("/housing/prices", response_model=List[HousingPriceResponse])
async def get_housing_prices(
    barrio_id: Optional[int] = Query(None, description="Filter by barrio ID"),
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Connection = Depends(get_db)
):
    """
    Get housing prices (sale and rental) per m².
    
    Returns data from fact_precios table.
    """
    query = """
        SELECT 
            barrio_id,
            anio,
            trimestre,
            precio_m2_venta as precio_venta_m2,
            precio_mes_alquiler as precio_alquiler_m2,
            NULL as superficie_media
        FROM fact_precios
        WHERE 1=1
    """
    params = []
    
    if barrio_id is not None:
        query += " AND barrio_id = ?"
        params.append(barrio_id)
    
    if year is not None:
        query += " AND anio = ?"
        params.append(year)
    
    query += " ORDER BY anio DESC, trimestre DESC"
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/housing/rent", response_model=List[RentResponse])
async def get_rent_data(
    barrio_id: Optional[int] = Query(None, description="Filter by barrio ID"),
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Connection = Depends(get_db)
):
    """
    Get household income (renta) data.
    
    Returns data from fact_renta table.
    """
    query = """
        SELECT 
            barrio_id,
            anio,
            renta_euros,
            renta_mediana,
            num_secciones
        FROM fact_renta
        WHERE 1=1
    """
    params = []
    
    if barrio_id is not None:
        query += " AND barrio_id = ?"
        params.append(barrio_id)
    
    if year is not None:
        query += " AND anio = ?"
        params.append(year)
    
    query += " ORDER BY anio DESC"
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/housing/prices/trends/{barrio_id}", response_model=List[HousingPriceResponse])
async def get_price_trends(
    barrio_id: int,
    year_start: Optional[int] = Query(None, description="Start year"),
    year_end: Optional[int] = Query(None, description="End year"),
    db: Connection = Depends(get_db)
):
    """
    Get housing price trends over time for a specific barrio.
    """
    query = """
        SELECT 
            barrio_id,
            anio,
            trimestre,
            AVG(precio_m2_venta) as precio_venta_m2,
            AVG(precio_mes_alquiler) as precio_alquiler_m2,
            NULL as superficie_media
        FROM fact_precios
        WHERE barrio_id = ?
    """
    params = [barrio_id]
    
    if year_start is not None:
        query += " AND anio >= ?"
        params.append(year_start)
    
    if year_end is not None:
        query += " AND anio <= ?"
        params.append(year_end)
    
    query += " GROUP BY barrio_id, anio, trimestre ORDER BY anio, trimestre"
    
    cursor = db.execute(query, params)
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@router.get("/housing/yield/{barrio_id}", response_model=YieldResponse)
async def get_gross_yield(
    barrio_id: int,
    year: int = Query(2024, description="Year for calculation"),
    db: Connection = Depends(get_db)
):
    """
    Calculate gross rental yield for a barrio.
    
    Formula: (Monthly Rent * 12) / Sale Price * 100
    
    Returns yield as percentage.
    """
    # Get barrio name
    barrio_query = "SELECT barrio_nombre FROM dim_barrios WHERE barrio_id = ?"
    barrio_cursor = db.execute(barrio_query, (barrio_id,))
    barrio_row = barrio_cursor.fetchone()
    
    if not barrio_row:
        raise HTTPException(status_code=404, detail=f"Barrio {barrio_id} not found")
    
    barrio_nombre = barrio_row["barrio_nombre"]
    
    # Get price data
    price_query = """
        SELECT 
            AVG(precio_m2_venta) as precio_venta,
            AVG(precio_mes_alquiler) as precio_alquiler
        FROM fact_precios
        WHERE barrio_id = ? AND anio = ?
        AND precio_m2_venta IS NOT NULL 
        AND precio_mes_alquiler IS NOT NULL
    """
    
    price_cursor = db.execute(price_query, (barrio_id, year))
    price_row = price_cursor.fetchone()
    
    if not price_row or price_row["precio_venta"] is None or price_row["precio_alquiler"] is None:
        return YieldResponse(
            barrio_id=barrio_id,
            barrio_nombre=barrio_nombre,
            year=year,
            gross_yield_percent=None,
            precio_venta_m2=None,
            precio_alquiler_m2=None,
            calculation_note="Insufficient data for yield calculation"
        )
    
    precio_venta = price_row["precio_venta"]
    precio_alquiler = price_row["precio_alquiler"]
    
    # Calculate yield (assuming 70m² average apartment)
    superficie_m2 = 70
    annual_rent = precio_alquiler * 12 * superficie_m2
    purchase_price = precio_venta * superficie_m2
    
    if purchase_price > 0:
        gross_yield = (annual_rent / purchase_price) * 100
    else:
        gross_yield = None
    
    return YieldResponse(
        barrio_id=barrio_id,
        barrio_nombre=barrio_nombre,
        year=year,
        gross_yield_percent=round(gross_yield, 2) if gross_yield else None,
        precio_venta_m2=round(precio_venta, 2),
        precio_alquiler_m2=round(precio_alquiler, 2),
        calculation_note=f"Based on {superficie_m2}m² apartment average"
    )
