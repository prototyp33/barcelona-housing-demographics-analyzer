#!/usr/bin/env python3
"""
Matching geográfico con parámetros relajados para aumentar match rate.

Este script es una variante con parámetros más permisivos:
- Distancia máxima: 200m (vs 50m)
- Score mínimo: 0.4 (vs 0.5)
- Peso geográfico: 0.5 (vs 0.6)

Uso:
    python3 match_idealista_catastro_geographic_relaxed.py
"""

import subprocess
import sys
from pathlib import Path

# Ejecutar script principal con parámetros relajados
script_path = Path(__file__).parent / "match_idealista_catastro_geographic.py"

cmd = [
    sys.executable,
    str(script_path),
    "--max-distance", "200",
    "--geographic-weight", "0.5",
    "--min-score", "0.4",
    "--skip-geocoding",  # Usar coordenadas ya geocodificadas
    "--output", "spike-data-validation/data/processed/fase2/idealista_catastro_matched_geographic_relaxed.csv"
]

print("=" * 70)
print("MATCHING GEOGRÁFICO - PARÁMETROS RELAJADOS")
print("=" * 70)
print(f"\nParámetros:")
print(f"  Distancia máxima: 200m (vs 50m)")
print(f"  Score mínimo: 0.4 (vs 0.5)")
print(f"  Peso geográfico: 0.5 (vs 0.6)")
print(f"\nEjecutando...\n")

subprocess.run(cmd)

