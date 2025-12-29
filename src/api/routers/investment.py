"""Investment router - investment recommendations endpoints."""

from fastapi import APIRouter, HTTPException
from ..models import InvestmentRequest, InvestmentResponse, InvestmentRecommendation
from ..services import get_model_service

router = APIRouter(prefix="/investment", tags=["investment"])


@router.post("/recommend", response_model=InvestmentResponse)
async def get_recommendations(request: InvestmentRequest):
    """Get investment recommendations based on budget and strategy.
    
    Args:
        request: Investment request with budget, strategy, and max_results
        
    Returns:
        List of recommended neighborhoods for investment
        
    Raises:
        HTTPException: If no recommendations found
    """
    model = get_model_service()
    
    recommendations_df = model.get_investment_recommendations(
        budget=request.budget,
        strategy=request.strategy,
        max_results=request.max_results
    )
    
    if recommendations_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No investment opportunities found for budget €{request.budget:,.0f}"
        )
    
    # Convert to list of recommendations
    recommendations = []
    for idx, row in recommendations_df.iterrows():
        recommendations.append(
            InvestmentRecommendation(
                barrio_nombre=row['barrio_nombre'],
                avg_venta_23=row['avg_venta_23'],
                gross_yield=row['gross_yield'],
                desviacion_valor=row['desviacion_valor'],
                segmento=int(row['segmento']) if pd.notna(row['segmento']) else 0,
                estimated_total_cost=row['estimated_total_cost'],
                rank=len(recommendations) + 1
            )
        )
    
    return InvestmentResponse(
        budget=request.budget,
        strategy=request.strategy,
        recommendations=recommendations
    )


import pandas as pd
