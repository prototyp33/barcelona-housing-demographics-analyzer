
import sys
import os
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.services.model_service import ModelService

def main():
    print("🚀 Preparing valuation data using ML model...")
    
    service = ModelService()
    
    # Override data path if necessary, but it defaults to data/barcelona_ml_valuation.csv
    # based on PROJECT_ROOT logic in model_service.py
    
    success = service.load_model()
    
    if not success:
        print("❌ Failed to load or train the model.")
        return

    df = service.get_all_neighborhoods()
    
    output_path = Path("data/barcelona_ml_valuation.csv")
    df.to_csv(output_path, index=False)
    
    print(f"✅ Valuation data updated with ML predictions at {output_path}")
    print(f"   Samples: {len(df)}")
    print(f"   Columns added: precio_estimado, desviacion_valor")

if __name__ == "__main__":
    main()
