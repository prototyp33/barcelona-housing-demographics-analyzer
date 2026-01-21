import json
from pathlib import Path
from datetime import datetime

def update_manifest():
    manifest_path = Path("data/raw/manifest.json")
    if not manifest_path.exists():
        return
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 1. Eliminar entradas antiguas de turismo corruptas
    manifest = [e for entry in [manifest] for e in entry if "intensitat-activitat-turistica" not in e["file_path"]]
    
    # 2. Añadir la nueva entrada para el CSV de HUTs
    hut_path = "opendatabcn/opendatabcn_habitatges-us-turistic.csv"
    hut_full_path = Path("data/raw") / hut_path
    
    if hut_full_path.exists():
        # Evitar duplicados
        manifest = [e for e in manifest if e["file_path"] != hut_path]
        
        manifest.append({
            "file_path": hut_path,
            "source": "opendatabcn",
            "type": "tourism_hut",
            "timestamp": datetime.fromtimestamp(hut_full_path.stat().st_mtime).isoformat(),
            "year_start": 2024,
            "year_end": 2024
        })
    
    # 3. Asegurar que Catastro Usos tiene el tipo correcto para el pipeline
    for entry in manifest:
        if "est-cadastre-locals-us-desti" in entry["file_path"]:
            entry["type"] = "cadastre_built_surface"

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print("Manifest actualizado con el nuevo CSV de HUTs y corrección de tipos.")

if __name__ == "__main__":
    update_manifest()
