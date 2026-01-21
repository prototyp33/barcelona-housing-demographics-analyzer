#!/usr/bin/env python3
"""
Schema Health Monitoring Module

Tracks database schema health metrics over time including:
- Table row counts
- Data coverage (barrio coverage)
- Temporal coverage (year ranges)
- View health (broken vs working)
- Data quality metrics
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TableMetrics:
    """Metrics for a single table."""
    table_name: str
    table_type: str  # 'table' or 'view'
    row_count: int
    min_year: Optional[int]
    max_year: Optional[int]
    unique_barrios: Optional[int]
    barrio_coverage_pct: Optional[float]
    has_geometry: Optional[bool]
    is_healthy: bool
    error_message: Optional[str]
    timestamp: str


@dataclass
class SchemaHealthSnapshot:
    """Complete schema health snapshot."""
    timestamp: str
    total_tables: int
    total_views: int
    total_fact_tables: int
    total_dim_tables: int
    healthy_tables: int
    healthy_views: int
    broken_views: int
    empty_tables: int
    total_rows: int
    barrio_coverage_avg: float
    temporal_coverage_years: int
    table_metrics: List[Dict[str, Any]]
    view_errors: List[Dict[str, str]]


class SchemaHealthMonitor:
    """Monitors and tracks database schema health over time."""
    
    def __init__(self, db_path: str):
        """
        Initialize the schema health monitor.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        
    def __enter__(self):
        """Context manager entry."""
        self.conn = sqlite3.connect(str(self.db_path))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.conn:
            self.conn.close()
            
    def get_all_tables(self) -> List[Tuple[str, str]]:
        """
        Get all tables and views from the database.
        
        Returns:
            List of (name, type) tuples
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, type 
            FROM sqlite_master 
            WHERE type IN ('table', 'view')
            AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
        """)
        return cursor.fetchall()
    
    def get_table_metrics(self, table_name: str, table_type: str) -> TableMetrics:
        """
        Collect metrics for a single table or view.
        
        Args:
            table_name: Name of the table/view
            table_type: 'table' or 'view'
            
        Returns:
            TableMetrics object
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        
        # Initialize metrics
        row_count = 0
        min_year = None
        max_year = None
        unique_barrios = None
        barrio_coverage_pct = None
        has_geometry = None
        is_healthy = True
        error_message = None
        
        try:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Check for year range (if anio column exists)
            try:
                cursor.execute(f"SELECT MIN(anio), MAX(anio) FROM {table_name} WHERE anio IS NOT NULL")
                result = cursor.fetchone()
                if result and result[0] is not None:
                    min_year, max_year = result
            except sqlite3.OperationalError:
                pass  # No anio column
            
            # Check barrio coverage (if barrio_id column exists)
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT barrio_id) FROM {table_name} WHERE barrio_id IS NOT NULL")
                unique_barrios = cursor.fetchone()[0]
                if unique_barrios is not None:
                    barrio_coverage_pct = (unique_barrios / 73.0) * 100
            except sqlite3.OperationalError:
                pass  # No barrio_id column
            
            # Check for geometry (if geometry_json column exists)
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE geometry_json IS NOT NULL")
                geom_count = cursor.fetchone()[0]
                has_geometry = geom_count > 0 if row_count > 0 else None
            except sqlite3.OperationalError:
                pass  # No geometry_json column
                
        except Exception as e:
            is_healthy = False
            error_message = str(e)
            logger.error(f"Error collecting metrics for {table_name}: {e}")
        
        return TableMetrics(
            table_name=table_name,
            table_type=table_type,
            row_count=row_count,
            min_year=min_year,
            max_year=max_year,
            unique_barrios=unique_barrios,
            barrio_coverage_pct=barrio_coverage_pct,
            has_geometry=has_geometry,
            is_healthy=is_healthy,
            error_message=error_message,
            timestamp=timestamp
        )
    
    def collect_snapshot(self) -> SchemaHealthSnapshot:
        """
        Collect a complete schema health snapshot.
        
        Returns:
            SchemaHealthSnapshot object
        """
        timestamp = datetime.now().isoformat()
        
        # Get all tables and views
        all_objects = self.get_all_tables()
        
        # Collect metrics for each object
        table_metrics_list = []
        view_errors = []
        
        total_tables = 0
        total_views = 0
        total_fact_tables = 0
        total_dim_tables = 0
        healthy_tables = 0
        healthy_views = 0
        broken_views = 0
        empty_tables = 0
        total_rows = 0
        barrio_coverages = []
        all_years = set()
        
        for name, obj_type in all_objects:
            metrics = self.get_table_metrics(name, obj_type)
            table_metrics_list.append(asdict(metrics))
            
            # Update counters
            if obj_type == 'table':
                total_tables += 1
                if name.startswith('fact_'):
                    total_fact_tables += 1
                elif name.startswith('dim_'):
                    total_dim_tables += 1
                    
                if metrics.is_healthy:
                    healthy_tables += 1
                if metrics.row_count == 0:
                    empty_tables += 1
            else:  # view
                total_views += 1
                if metrics.is_healthy:
                    healthy_views += 1
                else:
                    broken_views += 1
                    view_errors.append({
                        'view_name': name,
                        'error': metrics.error_message
                    })
            
            # Aggregate metrics
            total_rows += metrics.row_count
            
            if metrics.barrio_coverage_pct is not None:
                barrio_coverages.append(metrics.barrio_coverage_pct)
            
            if metrics.min_year is not None and metrics.max_year is not None:
                for year in range(metrics.min_year, metrics.max_year + 1):
                    all_years.add(year)
        
        # Calculate aggregates
        barrio_coverage_avg = sum(barrio_coverages) / len(barrio_coverages) if barrio_coverages else 0.0
        temporal_coverage_years = len(all_years)
        
        return SchemaHealthSnapshot(
            timestamp=timestamp,
            total_tables=total_tables,
            total_views=total_views,
            total_fact_tables=total_fact_tables,
            total_dim_tables=total_dim_tables,
            healthy_tables=healthy_tables,
            healthy_views=healthy_views,
            broken_views=broken_views,
            empty_tables=empty_tables,
            total_rows=total_rows,
            barrio_coverage_avg=barrio_coverage_avg,
            temporal_coverage_years=temporal_coverage_years,
            table_metrics=table_metrics_list,
            view_errors=view_errors
        )
    
    def save_snapshot(self, snapshot: SchemaHealthSnapshot, output_path: Optional[Path] = None) -> Path:
        """
        Save a snapshot to JSON file.
        
        Args:
            snapshot: SchemaHealthSnapshot to save
            output_path: Optional custom output path
            
        Returns:
            Path where snapshot was saved
        """
        if output_path is None:
            # Default: save to data/monitoring/schema_health_TIMESTAMP.json
            monitoring_dir = self.db_path.parent / 'monitoring'
            monitoring_dir.mkdir(exist_ok=True)
            
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = monitoring_dir / f'schema_health_{timestamp_str}.json'
        
        with open(output_path, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2)
        
        logger.info(f"Schema health snapshot saved to {output_path}")
        return output_path
    
    def get_historical_snapshots(self, monitoring_dir: Optional[Path] = None, limit: int = 10) -> List[SchemaHealthSnapshot]:
        """
        Load historical snapshots from monitoring directory.
        
        Args:
            monitoring_dir: Directory containing snapshot files
            limit: Maximum number of snapshots to load (most recent)
            
        Returns:
            List of SchemaHealthSnapshot objects, sorted by timestamp (newest first)
        """
        if monitoring_dir is None:
            monitoring_dir = self.db_path.parent / 'monitoring'
        
        if not monitoring_dir.exists():
            return []
        
        # Find all snapshot files
        snapshot_files = sorted(
            monitoring_dir.glob('schema_health_*.json'),
            reverse=True
        )[:limit]
        
        snapshots = []
        for file_path in snapshot_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    snapshots.append(SchemaHealthSnapshot(**data))
            except Exception as e:
                logger.error(f"Error loading snapshot {file_path}: {e}")
        
        return snapshots
    
    def get_health_score(self, snapshot: SchemaHealthSnapshot) -> float:
        """
        Calculate overall health score (0-100).
        
        Args:
            snapshot: SchemaHealthSnapshot to score
            
        Returns:
            Health score between 0 and 100
        """
        score = 100.0
        
        # Deduct points for broken views (max -20)
        if snapshot.total_views > 0:
            broken_view_penalty = (snapshot.broken_views / snapshot.total_views) * 20
            score -= broken_view_penalty
        
        # Deduct points for empty tables (max -15)
        if snapshot.total_fact_tables > 0:
            empty_table_penalty = (snapshot.empty_tables / snapshot.total_fact_tables) * 15
            score -= empty_table_penalty
        
        # Deduct points for low barrio coverage (max -15)
        if snapshot.barrio_coverage_avg < 100:
            coverage_penalty = ((100 - snapshot.barrio_coverage_avg) / 100) * 15
            score -= coverage_penalty
        
        # Bonus for good temporal coverage (max +5)
        if snapshot.temporal_coverage_years >= 10:
            score += 5
        
        return max(0.0, min(100.0, score))
