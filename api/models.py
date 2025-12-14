"""
Pydantic models for API responses

These models match the TypeScript types in the React frontend.
"""
from pydantic import BaseModel, Field
from typing import Optional


class BarrioResponse(BaseModel):
    """Barrio (neighborhood) response model"""
    barrio_id: int = Field(..., description="Unique barrio ID")
    barrio_nombre: str = Field(..., description="Barrio name")
    distrito_nombre: Optional[str] = Field(None, description="District name")
    geometry_json: Optional[str] = Field(None, description="GeoJSON geometry for mapping")

    class Config:
        from_attributes = True


class DemographicsResponse(BaseModel):
    """Demographics response model"""
    barrio_id: int
    anio: int = Field(..., description="Year")
    poblacion: Optional[int] = Field(None, description="Total population")
    sexo: Optional[str] = Field(None, description="Sex (H/M)")
    grupo_edad: Optional[str] = Field(None, description="Age group")
    nacionalidad: Optional[str] = Field(None, description="Nationality")

    class Config:
        from_attributes = True


class HousingPriceResponse(BaseModel):
    """Housing price response model"""
    barrio_id: int
    anio: int = Field(..., description="Year")
    trimestre: Optional[int] = Field(None, description="Quarter (1-4)")
    precio_venta_m2: Optional[float] = Field(None, description="Sale price per m²")
    precio_alquiler_m2: Optional[float] = Field(None, description="Rental price per m²")
    superficie_media: Optional[float] = Field(None, description="Average surface area")

    class Config:
        from_attributes = True


class RentResponse(BaseModel):
    """Household income (rent) response model"""
    barrio_id: int
    anio: int = Field(..., description="Year")
    renta_euros: float = Field(..., description="Average household income in euros")
    renta_mediana: Optional[float] = Field(None, description="Median household income")
    num_secciones: Optional[int] = Field(None, description="Number of census sections")

    class Config:
        from_attributes = True


class YieldResponse(BaseModel):
    """Gross yield calculation response"""
    barrio_id: int
    barrio_nombre: str
    year: int
    gross_yield_percent: Optional[float] = Field(None, description="Gross rental yield (%)")
    precio_venta_m2: Optional[float] = None
    precio_alquiler_m2: Optional[float] = None
    calculation_note: Optional[str] = None

    class Config:
        from_attributes = True
