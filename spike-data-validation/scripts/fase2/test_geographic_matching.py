#!/usr/bin/env python3
"""
Script de prueba rápida para matching geográfico.

Prueba el matching geográfico con una muestra pequeña (10 propiedades)
para verificar que funciona correctamente antes de ejecutar el proceso completo.

Uso:
    python3 spike-data-validation/scripts/fase2/test_geographic_matching.py
"""

import pandas as pd
from pathlib import Path
from match_idealista_catastro_geographic import (
    geocode_address,
    calculate_distance,
    calculate_geographic_score,
    match_by_coordinates
)

DATA_DIR = Path("spike-data-validation/data/processed/fase2")

print("=" * 70)
print("PRUEBA RÁPIDA - MATCHING GEOGRÁFICO")
print("=" * 70)

# Cargar datos
print("\n1. Cargando datos...")
df_idealista = pd.read_csv(DATA_DIR / "idealista_gracia_comet.csv")
df_catastro = pd.read_csv(Path("spike-data-validation/data/processed/catastro_gracia_real.csv"))

print(f"   Idealista: {len(df_idealista)} propiedades")
print(f"   Catastro: {len(df_catastro)} edificios")

# Probar geocoding con 3 direcciones
print("\n2. Probando geocoding (3 direcciones)...")
sample_addresses = df_idealista['localidad'].head(3).tolist()

for i, address in enumerate(sample_addresses, 1):
    print(f"\n   Dirección {i}: {address}")
    coords = geocode_address(address)
    if coords:
        print(f"   ✅ Coordenadas: ({coords[0]:.6f}, {coords[1]:.6f})")
    else:
        print(f"   ❌ No se pudo geocodificar")

# Probar cálculo de distancia
print("\n3. Probando cálculo de distancia...")
# Coordenadas de ejemplo (Gràcia, Barcelona)
point1 = (41.4026, 2.1561)  # Ejemplo: Plaça del Sol, Gràcia
point2 = (41.4030, 2.1565)  # Ejemplo: Cerca de Plaça del Sol

distance = calculate_distance(point1[0], point1[1], point2[0], point2[1])
print(f"   Punto 1: {point1}")
print(f"   Punto 2: {point2}")
print(f"   Distancia: {distance:.2f} m")

# Probar score geográfico
print("\n4. Probando score geográfico...")
for dist in [0, 10, 25, 50, 100]:
    score = calculate_geographic_score(dist, max_distance=50)
    print(f"   Distancia {dist:3d} m → Score: {score:.3f}")

# Verificar coordenadas en Catastro
print("\n5. Verificando coordenadas en Catastro...")
catastro_with_coords = df_catastro[df_catastro['lat'].notna() & df_catastro['lon'].notna()]
print(f"   Edificios con coordenadas: {len(catastro_with_coords)}/{len(df_catastro)} ({len(catastro_with_coords)/len(df_catastro)*100:.1f}%)")
if len(catastro_with_coords) > 0:
    print(f"   Rango lat: {catastro_with_coords['lat'].min():.6f} - {catastro_with_coords['lat'].max():.6f}")
    print(f"   Rango lon: {catastro_with_coords['lon'].min():.6f} - {catastro_with_coords['lon'].max():.6f}")

print("\n" + "=" * 70)
print("✅ Prueba completada")
print("=" * 70)
print("\nSi todas las pruebas pasan, puedes ejecutar el script completo:")
print("  python3 match_idealista_catastro_geographic.py")

