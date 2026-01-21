#!/usr/bin/env python3
"""
Schema Health CLI Tool

Command-line interface for monitoring database schema health.
"""

import sys
from pathlib import Path
import argparse
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.monitoring.schema_health import SchemaHealthMonitor
from src.database import DatabaseManager


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_health_score(score: float):
    """Print health score with color coding."""
    if score >= 90:
        status = "EXCELLENT ✅"
        color = "\033[92m"  # Green
    elif score >= 75:
        status = "GOOD 👍"
        color = "\033[94m"  # Blue
    elif score >= 60:
        status = "FAIR ⚠️"
        color = "\033[93m"  # Yellow
    else:
        status = "POOR ❌"
        color = "\033[91m"  # Red
    
    reset = "\033[0m"
    print(f"{color}Health Score: {score:.1f}/100 - {status}{reset}")


def cmd_current(args):
    """Show current schema health."""
    db_manager = DatabaseManager()
    
    with SchemaHealthMonitor(db_manager.db_path) as monitor:
        print_header("CURRENT SCHEMA HEALTH")
        
        snapshot = monitor.collect_snapshot()
        health_score = monitor.get_health_score(snapshot)
        
        print_health_score(health_score)
        print()
        
        # Summary stats
        print(f"📊 Overview:")
        print(f"  • Total Tables: {snapshot.total_tables} ({snapshot.total_fact_tables} fact, {snapshot.total_dim_tables} dimension)")
        print(f"  • Total Views: {snapshot.total_views} ({snapshot.healthy_views} healthy, {snapshot.broken_views} broken)")
        print(f"  • Total Rows: {snapshot.total_rows:,}")
        print(f"  • Empty Tables: {snapshot.empty_tables}")
        print()
        
        # Coverage stats
        print(f"📍 Data Coverage:")
        print(f"  • Average Barrio Coverage: {snapshot.barrio_coverage_avg:.1f}%")
        print(f"  • Temporal Coverage: {snapshot.temporal_coverage_years} years")
        print()
        
        # Broken views
        if snapshot.broken_views > 0:
            print(f"⚠️  Broken Views:")
            for error in snapshot.view_errors:
                print(f"  • {error['view_name']}: {error['error']}")
            print()
        
        # Empty tables
        empty_tables = [m for m in snapshot.table_metrics if m['row_count'] == 0 and m['table_name'].startswith('fact_')]
        if empty_tables:
            print(f"📭 Empty Fact Tables:")
            for table in empty_tables:
                print(f"  • {table['table_name']}")
            print()
        
        # Low coverage tables
        low_coverage = [
            m for m in snapshot.table_metrics
            if m.get('barrio_coverage_pct') is not None 
            and m['barrio_coverage_pct'] < 95
            and m['row_count'] > 0
        ]
        if low_coverage:
            print(f"📉 Low Barrio Coverage (<95%):")
            for table in low_coverage:
                print(f"  • {table['table_name']}: {table['barrio_coverage_pct']:.1f}%")
            print()


def cmd_snapshot(args):
    """Create a new health snapshot."""
    db_manager = DatabaseManager()
    
    with SchemaHealthMonitor(db_manager.db_path) as monitor:
        print_header("CREATING SCHEMA HEALTH SNAPSHOT")
        
        snapshot = monitor.collect_snapshot()
        health_score = monitor.get_health_score(snapshot)
        
        # Save snapshot
        output_path = monitor.save_snapshot(snapshot)
        
        print(f"✅ Snapshot created successfully!")
        print(f"   Saved to: {output_path}")
        print()
        print_health_score(health_score)
        print()
        print(f"📊 Snapshot Summary:")
        print(f"  • Timestamp: {snapshot.timestamp}")
        print(f"  • Tables: {snapshot.total_tables}")
        print(f"  • Views: {snapshot.total_views}")
        print(f"  • Total Rows: {snapshot.total_rows:,}")
        print()


def cmd_history(args):
    """Show historical snapshots."""
    db_manager = DatabaseManager()
    
    with SchemaHealthMonitor(db_manager.db_path) as monitor:
        print_header("SCHEMA HEALTH HISTORY")
        
        snapshots = monitor.get_historical_snapshots(limit=args.limit)
        
        if not snapshots:
            print("No historical snapshots found.")
            print("Create your first snapshot with: python scripts/schema_health_cli.py snapshot")
            return
        
        print(f"Showing {len(snapshots)} most recent snapshot(s):\n")
        
        for i, snapshot in enumerate(snapshots, 1):
            health_score = monitor.get_health_score(snapshot)
            timestamp = datetime.fromisoformat(snapshot.timestamp)
            
            print(f"{i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Health Score: {health_score:.1f}/100")
            print(f"   Tables: {snapshot.total_tables} | Views: {snapshot.total_views} | Rows: {snapshot.total_rows:,}")
            print(f"   Broken Views: {snapshot.broken_views} | Empty Tables: {snapshot.empty_tables}")
            print()


def cmd_table(args):
    """Show detailed metrics for a specific table."""
    db_manager = DatabaseManager()
    
    with SchemaHealthMonitor(db_manager.db_path) as monitor:
        print_header(f"TABLE METRICS: {args.table_name}")
        
        # Get all tables to find the type
        all_tables = monitor.get_all_tables()
        table_info = next((t for t in all_tables if t[0] == args.table_name), None)
        
        if not table_info:
            print(f"❌ Table '{args.table_name}' not found.")
            return
        
        table_type = table_info[1]
        metrics = monitor.get_table_metrics(args.table_name, table_type)
        
        print(f"Type: {table_type.upper()}")
        print(f"Status: {'✅ Healthy' if metrics.is_healthy else '❌ Error'}")
        print()
        
        print(f"📊 Metrics:")
        print(f"  • Row Count: {metrics.row_count:,}")
        
        if metrics.min_year and metrics.max_year:
            print(f"  • Year Range: {metrics.min_year} - {metrics.max_year}")
        
        if metrics.unique_barrios is not None:
            print(f"  • Unique Barrios: {metrics.unique_barrios}/73 ({metrics.barrio_coverage_pct:.1f}%)")
        
        if metrics.has_geometry is not None:
            print(f"  • Has Geometry: {'Yes' if metrics.has_geometry else 'No'}")
        
        if metrics.error_message:
            print(f"\n❌ Error: {metrics.error_message}")
        
        print()


def cmd_export(args):
    """Export current health to JSON."""
    db_manager = DatabaseManager()
    
    with SchemaHealthMonitor(db_manager.db_path) as monitor:
        snapshot = monitor.collect_snapshot()
        health_score = monitor.get_health_score(snapshot)
        
        # Prepare export data
        export_data = {
            **snapshot.__dict__,
            'health_score': health_score
        }
        
        # Write to file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Schema health exported to: {output_path}")
        print_health_score(health_score)
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Schema Health Monitoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current health
  python scripts/schema_health_cli.py current
  
  # Create a snapshot
  python scripts/schema_health_cli.py snapshot
  
  # View history
  python scripts/schema_health_cli.py history --limit 5
  
  # Check specific table
  python scripts/schema_health_cli.py table fact_precios
  
  # Export to JSON
  python scripts/schema_health_cli.py export --output health.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Current command
    parser_current = subparsers.add_parser('current', help='Show current schema health')
    parser_current.set_defaults(func=cmd_current)
    
    # Snapshot command
    parser_snapshot = subparsers.add_parser('snapshot', help='Create a new health snapshot')
    parser_snapshot.set_defaults(func=cmd_snapshot)
    
    # History command
    parser_history = subparsers.add_parser('history', help='Show historical snapshots')
    parser_history.add_argument('--limit', type=int, default=10, help='Number of snapshots to show')
    parser_history.set_defaults(func=cmd_history)
    
    # Table command
    parser_table = subparsers.add_parser('table', help='Show metrics for a specific table')
    parser_table.add_argument('table_name', help='Name of the table')
    parser_table.set_defaults(func=cmd_table)
    
    # Export command
    parser_export = subparsers.add_parser('export', help='Export current health to JSON')
    parser_export.add_argument('--output', default='schema_health.json', help='Output file path')
    parser_export.set_defaults(func=cmd_export)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
