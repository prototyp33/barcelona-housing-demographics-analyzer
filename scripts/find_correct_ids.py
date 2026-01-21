import sys
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.opendata import OpenDataBCNExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    od = OpenDataBCNExtractor()
    
    print("--- BUSCANDO ID CORRECTO PARA ALQUILER ---")
    od.search_datasets_by_keyword("lloguer mitjà mensual")
    
    print("\n--- BUSCANDO ID CORRECTO PARA USOS CATASTRO ---")
    od.search_datasets_by_keyword("cadastre locals usos")
    
    print("\n--- BUSCANDO ID CORRECTO PARA TRANSMISIONES (VENTA REAL) ---")
    od.search_datasets_by_keyword("venda superficie")

if __name__ == "__main__":
    main()
