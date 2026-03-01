#!/usr/bin/env python3
"""Test script to trigger database operations and capture debug logs."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database_setup import create_connection, ensure_database_path
from src.etl.pipeline import run_etl

def main():
    """Run ETL pipeline to trigger database operations."""
    print("Starting ETL pipeline to test database operations...")
    print("Debug logs will be written to .cursor/debug.log\n")
    
    try:
        processed_dir = Path("data/processed")
        db_path = ensure_database_path(None, processed_dir)
        
        # Test connection
        print("1. Testing database connection...")
        conn = create_connection(db_path)
        print(f"   ✓ Connection created: {db_path}")
        conn.close()
        print("   ✓ Connection closed\n")
        
        # Try to run ETL (this will trigger all instrumentation)
        print("2. Running ETL pipeline...")
        result_path = run_etl()
        print(f"   ✓ ETL completed: {result_path}\n")
        
        print("✓ All database operations completed successfully!")
        print("Check .cursor/debug.log for detailed instrumentation logs.")
        
    except Exception as e:
        print(f"\n✗ Error during database operations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
