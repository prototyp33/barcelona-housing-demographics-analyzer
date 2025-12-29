"""Predictions router - ML model predictions endpoints."""

from fastapi import APIRouter, HTTPException
from ..models import PredictionRequest, PredictionResponse
from ..services import get_model_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/", response_model=PredictionResponse)
async def predict_price(request: PredictionRequest):
    """Get price prediction for a barrio.
    
    Args:
        request: Prediction request with barrio_id
        
    Returns:
        Price prediction with deviation from current market price
        
    Raises:
        HTTPException: If barrio not found or prediction fails
    """
    model = get_model_service()
    
    prediction = model.predict(request.barrio_id)
    
    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not generate prediction for barrio {request.barrio_id}"
        )
    
    return prediction


@router.get("/{barrio_id}", response_model=PredictionResponse)
async def get_prediction(barrio_id: int):
    """Get price prediction for a specific barrio (GET endpoint).
    
    Args:
        barrio_id: Barrio ID
        
    Returns:
        Price prediction with deviation
        
    Raises:
        HTTPException: If barrio not found
    """
    model = get_model_service()
    
    prediction = model.predict(barrio_id)
    
    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not generate prediction for barrio {barrio_id}"
        )
    
    return prediction
