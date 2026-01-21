import json
import sys
from pathlib import Path
from datetime import datetime
import re

# Añadir el raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def fix_manifest():
    raw_dir = Path("data/raw")
    manifest_path = raw_dir / "manifest.json"
    
    # Cargar manifest existente o iniciar uno nuevo
    manifest = []
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    
    # Mapeo de IDs a tipos esperados por el ETL
    # Basado en src/extraction/opendata.py y src/etl/pipeline.py
    ID_TO_TYPE = {
        # Precios
        "bxtvnxvukh": "prices_venta",
        "u25rr7oxh6": "prices_venta",
        "b37xv8wcjh": "prices_alquiler",
        "mrslyp5pcq": "prices_venta",
        "habitatges-2na-ma": "prices_venta",
        
        # Renta
        "renda-disponible-llars-bcn": "renta",
        "atles-renda-bruta-per-llar": "income_gross_household",
        "atles-renda-index-gini": "income_gini",
        "atles-renda-p80-p20-distribucio": "income_p80_p20",
        
        # Catastro
        "est-cadastre-habitatges-superficie-mitjana": "cadastre_avg_surface",
        "est-cadastre-locals-us-desti": "cadastre_built_surface",
        "est-cadastre-habitatges-any-const": "cadastre_year_const",
        "est-cadastre-carrecs-tipus-propietari": "cadastre_owner_type",
        "est-cadastre-locals-prop": "cadastre_owner_nationality",
        "immo-edif-hab-segons-num-plantes-sobre-rasant": "cadastre_floors",
        "wjnmk82jd9": "cadastre_soil_surface",
        
        # Hogares
        "pad_dom_mdbas_n-persones": "household_crowding",
        "pad_dom_mdbas_nacionalitat": "household_nationality",
        "pad_dom_mdbas_edat-0018": "household_minors",
        "pad_dom_mdbas_dones": "household_women",
        
        # Turismo
        "intensitat-activitat-turistica": "tourism_intensity",
        "habitatges-us-turistic": "tourism_hut"
    }

    modified_count = 0
    new_count = 0
    existing_paths = {entry["file_path"] for entry in manifest}

    # 1. Corregir entradas existentes con tipo "unknown" o erróneo
    for entry in manifest:
        file_name = entry["file_path"].split('/')[-1]
        for ds_id, data_type in ID_TO_TYPE.items():
            if ds_id in file_name:
                if entry["type"] != data_type:
                    entry["type"] = data_type
                    modified_count += 1
                break

    # 2. Buscar archivos que no estén en el manifest
    for subdir in ["portaldades", "opendatabcn"]:
        dir_path = raw_dir / subdir
        if not dir_path.exists():
            continue
            
        for file in dir_path.glob("*.csv"):
            rel_path = str(file.relative_to(raw_dir))
            if rel_path in existing_paths:
                continue
                
            # Determinar tipo
            data_type = "unknown"
            for ds_id, t in ID_TO_TYPE.items():
                if ds_id in file.name:
                    data_type = t
                    break
            
            if data_type == "unknown":
                continue # No añadir si no sabemos qué es para no ensuciar
                
            entry = {
                "file_path": rel_path,
                "source": subdir,
                "type": data_type,
                "timestamp": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                "year_start": None,
                "year_end": None
            }
            
            # Extraer año
            year_match = re.search(r'(\d{4})', file.name)
            if year_match:
                entry["year_start"] = int(year_match.group(1))
                entry["year_end"] = int(year_match.group(1))
                
            manifest.append(entry)
            new_count += 1
            existing_paths.add(rel_path)

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"Manifest actualizado:")
    print(f"- {modified_count} entradas existentes corregidas.")
    print(f"- {new_count} entradas nuevas añadidas.")

if __name__ == "__main__":
    fix_manifest()
