"""Clusters router - neighborhood segmentation endpoints."""

from fastapi import APIRouter
from typing import Dict
from ..models import ClusterInfo
from ..services import get_model_service

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("/", response_model=Dict[int, ClusterInfo])
async def get_clusters():
    """Get information about all neighborhood clusters/segments.
    
    Returns:
        Dictionary mapping segment ID to cluster characteristics
    """
    model = get_model_service()
    cluster_info = model.get_cluster_info()
    
    # Convert to ClusterInfo models
    result = {}
    for seg_id, info in cluster_info.items():
        result[seg_id] = ClusterInfo(
            segmento=seg_id,
            barrios_count=info['barrios_count'],
            avg_price=info['avg_price'],
            avg_yield=info['avg_yield'],
            characteristics=info['characteristics']
        )
    
    return result
