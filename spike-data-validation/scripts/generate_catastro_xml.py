"""
Script auxiliar para generar fichero XML de entrada para consulta masiva oficial del Catastro.

Este script genera el fichero XML necesario para usar el servicio oficial de
consulta masiva de datos NO protegidos de la D.G. del Catastro.

Uso:
    python3 generate_catastro_xml.py

El fichero XML generado debe subirse manualmente a la Sede Electrónica del Catastro.
Ver instrucciones en: docs/CATASTRO_DATA_SOURCES.md

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import sys
import csv
from pathlib import Path

# Añadir directorio de scripts al PYTHONPATH
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from catastro_oficial_client import CatastroOficialClient


def main() -> int:
    """
    Genera fichero XML de entrada para consulta masiva oficial del Catastro.

    Lee las referencias catastrales del seed CSV y genera el XML de entrada
    según el formato requerido por la D.G. del Catastro.

    Returns:
        Código de salida (0 si éxito, 1 si error).
    """
    seed_path = Path("spike-data-validation/data/raw/gracia_refs_seed.csv")

    if not seed_path.exists():
        print(f"❌ Error: No se encontró el archivo seed: {seed_path}")
        return 1

    # Cargar referencias sin pandas (evita dependencias numpy)
    with seed_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "referencia_catastral" not in reader.fieldnames:
            print("❌ Error: El CSV debe contener la columna 'referencia_catastral'")
            return 1
        referencias = []
        for row in reader:
            rc = (row.get("referencia_catastral") or "").strip()
            if rc:
                referencias.append(rc)

    # Validar formato (14 o 20 caracteres)
    referencias_validas = []
    counts = {}
    for ref in referencias:
        ref_clean = ref.strip()
        counts[len(ref_clean)] = counts.get(len(ref_clean), 0) + 1
        if len(ref_clean) in (14, 20):
            referencias_validas.append(ref_clean)
        else:
            print(
                f"⚠️  Advertencia: Referencia '{ref_clean}' no tiene 14/20 caracteres "
                f"(tiene {len(ref_clean)})",
            )

    if not referencias_validas:
        print("❌ Error: No se encontraron referencias válidas (14 o 20 caracteres)")
        return 1

    print(f"📋 Generando XML para {len(referencias_validas)} referencias catastrales...")
    print(f"Distribución longitudes: {counts}")

    # Generar XML
    client = CatastroOficialClient()
    xml_path = client.generate_input_xml(referencias_validas)

    print(f"✅ Fichero XML generado: {xml_path.absolute()}")
    print("\n" + "=" * 80)
    print(client.generate_instructions(xml_path))
    print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

