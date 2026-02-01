
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.idescat import IDESCATExtractor

def test_extraction():
    extractor = IDESCATExtractor()
    print("Testing IDESCATExtractor for 2015-2023...")
    df, metadata = extractor.get_renta_by_barrio(2015, 2023)
    
    print("\nMetadata:")
    print(metadata)
    
    if not df.empty:
        print(f"\nExtracted {len(df)} records.")
        print(f"Years found: {df['anio'].unique() if 'anio' in df.columns else 'No anio col'}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Check counts per year
        if 'anio' in df.columns:
            print("\nRecords per year:")
            print(df.groupby('anio').size())
    else:
        print("\nNo data extracted.")

if __name__ == "__main__":
    test_extraction()
