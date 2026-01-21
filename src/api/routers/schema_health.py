"""
Schema Health Monitoring API Router

Provides endpoints for monitoring database schema health and metrics.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.monitoring.schema_health import SchemaHealthMonitor, SchemaHealthSnapshot
from src.database import DatabaseManager

router = APIRouter(prefix="/schema-health", tags=["Schema Health"])


@router.get("/current", response_model=dict)
async def get_current_health():
    """
    Get current schema health snapshot.
    
    Returns:
        Current schema health metrics including:
        - Table and view counts
        - Data coverage statistics
        - Health score
        - Broken views
        - Empty tables
    """
    try:
        db_manager = DatabaseManager()
        db_path = db_manager.db_path
        
        with SchemaHealthMonitor(db_path) as monitor:
            snapshot = monitor.collect_snapshot()
            health_score = monitor.get_health_score(snapshot)
            
            # Convert to dict and add health score
            result = {
                **snapshot.__dict__,
                'health_score': round(health_score, 2)
            }
            
            return result
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting schema health: {str(e)}")


@router.get("/history", response_model=List[dict])
async def get_health_history(limit: int = Query(default=10, ge=1, le=100)):
    """
    Get historical schema health snapshots.
    
    Args:
        limit: Maximum number of snapshots to return (1-100)
        
    Returns:
        List of historical schema health snapshots, newest first
    """
    try:
        db_manager = DatabaseManager()
        db_path = db_manager.db_path
        
        with SchemaHealthMonitor(db_path) as monitor:
            snapshots = monitor.get_historical_snapshots(limit=limit)
            
            # Convert to dicts and add health scores
            results = []
            for snapshot in snapshots:
                health_score = monitor.get_health_score(snapshot)
                results.append({
                    **snapshot.__dict__,
                    'health_score': round(health_score, 2)
                })
            
            return results
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading health history: {str(e)}")


@router.post("/snapshot", response_model=dict)
async def create_snapshot():
    """
    Create and save a new schema health snapshot.
    
    Returns:
        The created snapshot with file path
    """
    try:
        db_manager = DatabaseManager()
        db_path = db_manager.db_path
        
        with SchemaHealthMonitor(db_path) as monitor:
            snapshot = monitor.collect_snapshot()
            file_path = monitor.save_snapshot(snapshot)
            health_score = monitor.get_health_score(snapshot)
            
            return {
                **snapshot.__dict__,
                'health_score': round(health_score, 2),
                'saved_to': str(file_path)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating snapshot: {str(e)}")


@router.get("/tables/{table_name}", response_model=dict)
async def get_table_metrics(table_name: str):
    """
    Get detailed metrics for a specific table or view.
    
    Args:
        table_name: Name of the table or view
        
    Returns:
        Detailed metrics for the specified table
    """
    try:
        db_manager = DatabaseManager()
        db_path = db_manager.db_path
        
        with SchemaHealthMonitor(db_path) as monitor:
            # Verify table exists
            all_tables = monitor.get_all_tables()
            table_info = next((t for t in all_tables if t[0] == table_name), None)
            
            if not table_info:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            table_type = table_info[1]
            metrics = monitor.get_table_metrics(table_name, table_type)
            
            return metrics.__dict__
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table metrics: {str(e)}")


@router.get("/summary", response_model=dict)
async def get_health_summary():
    """
    Get a quick summary of schema health.
    
    Returns:
        Simplified health summary with key metrics
    """
    try:
        db_manager = DatabaseManager()
        db_path = db_manager.db_path
        
        with SchemaHealthMonitor(db_path) as monitor:
            snapshot = monitor.collect_snapshot()
            health_score = monitor.get_health_score(snapshot)
            
            # Calculate health status
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 75:
                status = "good"
            elif health_score >= 60:
                status = "fair"
            else:
                status = "poor"
            
            return {
                'timestamp': snapshot.timestamp,
                'health_score': round(health_score, 2),
                'status': status,
                'total_tables': snapshot.total_tables,
                'total_views': snapshot.total_views,
                'broken_views': snapshot.broken_views,
                'empty_tables': snapshot.empty_tables,
                'total_rows': snapshot.total_rows,
                'barrio_coverage_avg': round(snapshot.barrio_coverage_avg, 2),
                'temporal_coverage_years': snapshot.temporal_coverage_years
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting health summary: {str(e)}")


@router.get("/alerts", response_model=List[dict])
async def get_health_alerts():
    """
    Get current health alerts and warnings.
    
    Returns:
        List of alerts based on current schema health
    """
    try:
        db_manager = DatabaseManager()
        db_path = db_manager.db_path
        
        with SchemaHealthMonitor(db_path) as monitor:
            snapshot = monitor.collect_snapshot()
            alerts = []
            
            # Check for broken views
            if snapshot.broken_views > 0:
                alerts.append({
                    'severity': 'error',
                    'category': 'views',
                    'message': f'{snapshot.broken_views} broken view(s) detected',
                    'details': snapshot.view_errors
                })
            
            # Check for empty tables
            if snapshot.empty_tables > 0:
                empty_fact_tables = [
                    m for m in snapshot.table_metrics 
                    if m['table_name'].startswith('fact_') and m['row_count'] == 0
                ]
                if empty_fact_tables:
                    alerts.append({
                        'severity': 'warning',
                        'category': 'data_coverage',
                        'message': f'{len(empty_fact_tables)} empty fact table(s)',
                        'details': [t['table_name'] for t in empty_fact_tables]
                    })
            
            # Check for low barrio coverage
            low_coverage_tables = [
                m for m in snapshot.table_metrics
                if m.get('barrio_coverage_pct') is not None 
                and m['barrio_coverage_pct'] < 95
                and m['row_count'] > 0
            ]
            if low_coverage_tables:
                alerts.append({
                    'severity': 'warning',
                    'category': 'barrio_coverage',
                    'message': f'{len(low_coverage_tables)} table(s) with low barrio coverage (<95%)',
                    'details': [
                        {
                            'table': t['table_name'],
                            'coverage': round(t['barrio_coverage_pct'], 1)
                        }
                        for t in low_coverage_tables
                    ]
                })
            
            # Check for stale data (no data from current year)
            current_year = 2026  # Based on the report
            stale_tables = [
                m for m in snapshot.table_metrics
                if m.get('max_year') is not None 
                and m['max_year'] < current_year - 1
                and m['row_count'] > 0
            ]
            if stale_tables:
                alerts.append({
                    'severity': 'info',
                    'category': 'data_freshness',
                    'message': f'{len(stale_tables)} table(s) with potentially stale data',
                    'details': [
                        {
                            'table': t['table_name'],
                            'latest_year': t['max_year']
                        }
                        for t in stale_tables[:5]  # Limit to 5 examples
                    ]
                })
            
            return alerts
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting health alerts: {str(e)}")
