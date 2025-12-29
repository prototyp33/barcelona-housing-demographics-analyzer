"""Pydantic models for API request/response validation."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class BarrioBase(BaseModel):
    """Base barrio information."""
    barrio_id: int
    barrio_nombre: str
    distrito_nombre: str


class BarrioDetail(BarrioBase):
    """Detailed barrio information with metrics."""
    avg_venta_23: Optional[float] = None
    gross_yield: Optional[float] = None
    renta_bruta_llar: Optional[float] = None
    poblacion_total: Optional[int] = None
    segmento: Optional[int] = None
    
    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    """Request for price prediction."""
    barrio_id: int
    features: Optional[Dict[str, float]] = None


class PredictionResponse(BaseModel):
    """Price prediction response."""
    barrio_id: int
    barrio_nombre: str
    current_price: float
    predicted_price: float
    deviation_pct: float
    confidence_interval: Optional[List[float]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class InvestmentRequest(BaseModel):
    """Investment recommendation request."""
    budget: float = Field(gt=0, description="Investment budget in euros")
    strategy: str = Field(default="yield", pattern="^(yield|safe|growth)$")
    max_results: int = Field(default=5, ge=1, le=20)


class InvestmentRecommendation(BaseModel):
    """Single investment recommendation."""
    barrio_nombre: str
    avg_venta_23: float
    gross_yield: float
    desviacion_valor: float
    segmento: int
    estimated_total_cost: float
    rank: int


class InvestmentResponse(BaseModel):
    """Investment recommendations response."""
    budget: float
    strategy: str
    recommendations: List[InvestmentRecommendation]
    timestamp: datetime = Field(default_factory=datetime.now)


class ClusterInfo(BaseModel):
    """Cluster/segment information."""
    segmento: int
    barrios_count: int
    avg_price: float
    avg_yield: float
    characteristics: Dict[str, Any]


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    database_connected: bool
    model_loaded: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
