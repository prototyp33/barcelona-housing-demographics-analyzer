"""
Script para verificar que todos los requisitos están listos para ejecutar Issue #200.

ACTUALIZADO: Verifica acceso a API SOAP oficial (sin API key)

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Añadir directorio de scripts al PYTHONPATH
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

def _read_seed_metadata(seed_path: Path) -> Dict[str, Any]:
    """
    Lee el seed CSV sin depender de pandas (evita importar numpy).

    Args:
        seed_path: Ruta al seed CSV.

    Returns:
        Métricas del seed.
    """
    if not seed_path.exists():
        return {"exists": False, "error": f"No encontrado: {seed_path}"}

    try:
        with seed_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            has_ref = "referencia_catastral" in fieldnames
            has_lat = "lat" in fieldnames
            has_lon = "lon" in fieldnames
            total_rows = 0
            unique_refs = set()
            len_counts: Dict[int, int] = {}
            coords_invalid = 0

            for row in reader:
                total_rows += 1
                rc = (row.get("referencia_catastral") or "").strip()
                if rc:
                    unique_refs.add(rc)
                    len_counts[len(rc)] = len_counts.get(len(rc), 0) + 1

                if has_lat and has_lon:
                    try:
                        float(row.get("lat") or "")
                        float(row.get("lon") or "")
                    except (TypeError, ValueError):
                        coords_invalid += 1

        return {
            "exists": True,
            "columns": fieldnames,
            "has_ref": has_ref,
            "has_lat": has_lat,
            "has_lon": has_lon,
            "total_rows": total_rows,
            "unique_refs": len(unique_refs),
            "len_counts": len_counts,
            "coords_invalid": coords_invalid,
        }
    except OSError as exc:
        return {"exists": False, "error": f"Error leyendo seed: {exc}"}


def _test_catastro_coords() -> Tuple[bool, Optional[str]]:
    """
    Smoke test del servicio que SÍ funciona: Consulta_RCCOOR via get_building_by_coordinates().

    Returns:
        (ok, message)
    """
    try:
        from catastro_soap_client import CatastroSOAPClient

        client = CatastroSOAPClient()
        # Coordenada conocida en Barcelona (Gràcia-ish). Solo valida conectividad + respuesta.
        building = client.get_building_by_coordinates(lon=2.1564, lat=41.4026)
        if not building:
            return False, "Consulta_RCCOOR no devolvió datos para la coordenada de test"
        if not building.get("referencia_catastral"):
            return False, "Consulta_RCCOOR devolvió respuesta pero sin referencia_catastral"
        return True, f"OK (ref={building.get('referencia_catastral')})"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _test_catastro_dnprc() -> Tuple[bool, Optional[str]]:
    """
    Smoke test del servicio DNPRC (actualmente fallando con error 12).

    Returns:
        (ok, message)
    """
    try:
        from catastro_soap_client import CatastroSOAPClient

        client = CatastroSOAPClient()
        # RC 20 chars dummy para provocar respuesta del servidor
        _ = client.get_building_by_rc("9539519DF2893H000000")
        return True, "OK"
    except Exception as exc:  # noqa: BLE001
        # Consideramos “known-bad” el error 12 (servicio roto).
        msg = str(exc)
        if "código 12" in msg and "LA PROVINCIA NO EXISTE" in msg:
            return False, "KNOWN_BROKEN (error 12)"
        return False, msg


def main() -> int:
    seed_path = Path("spike-data-validation/data/raw/gracia_refs_seed.csv")

    print("=" * 70)
    print("VERIFICACIÓN DE REQUISITOS PARA ISSUE #200 (Catastro Gràcia)")
    print("=" * 70)
    print(f"Python: {sys.executable}")
    print()

    # 1) Seed CSV
    seed = _read_seed_metadata(seed_path)
    if not seed.get("exists"):
        print(f"❌ Seed CSV: {seed.get('error')}")
        seed_ok = False
        seed_coords_ok = False
    else:
        print(f"✅ Seed CSV existe: {seed_path}")
        print(f"   Columnas: {seed.get('columns')}")
        print(f"   Filas: {seed.get('total_rows')} | RC únicas: {seed.get('unique_refs')}")
        print(f"   Longitudes RC: {seed.get('len_counts')}")
        print(f"   Tiene coords (lat/lon): {seed.get('has_lat') and seed.get('has_lon')} "
              f"(inválidas: {seed.get('coords_invalid')})")
        seed_ok = bool(seed.get("has_ref")) and int(seed.get("unique_refs") or 0) >= 50
        seed_coords_ok = bool(seed.get("has_lat")) and bool(seed.get("has_lon")) and int(
            seed.get("coords_invalid") or 0
        ) == 0

        if seed_ok:
            print("✅ Seed mínimo OK (≥50 referencias)")
        else:
            print("❌ Seed inválido (requiere columna referencia_catastral y ≥50 refs únicas)")

    print()

    # 2) Cliente importable
    try:
        import catastro_soap_client  # noqa: F401

        client_ok = True
        print("✅ catastro_soap_client: import OK")
    except Exception as exc:  # noqa: BLE001
        client_ok = False
        print(f"❌ catastro_soap_client: import FAIL - {exc}")

    print()

    # 3) Servicios
    coords_ok, coords_msg = _test_catastro_coords()
    print(f"{'✅' if coords_ok else '❌'} Catastro Consulta_RCCOOR: {coords_msg}")

    dnprc_ok, dnprc_msg = _test_catastro_dnprc()
    # En este sprint, consideramos acceptable que DNPRC esté roto, mientras coords funcione.
    print(f"{'✅' if dnprc_ok else '⚠️'} Catastro Consulta_DNPRC: {dnprc_msg}")

    print("\n" + "=" * 70)
    print("DECISIÓN")
    print("=" * 70)

    # Readiness para el extractor con fallback:
    ready_coords_fallback = client_ok and seed_ok and seed_coords_ok and coords_ok
    if ready_coords_fallback:
        print("✅ READY (modo coordenadas): puedes ejecutar:")
        print("   .venv-spike/bin/python spike-data-validation/scripts/extract_catastro_gracia.py")
        print("   Output esperado: spike-data-validation/data/raw/catastro_gracia_coords.csv")
        return 0

    print("❌ NOT READY: faltan requisitos para el modo coordenadas.")
    if not client_ok:
        print("   - catastro_soap_client importable")
    if not seed_ok:
        print("   - seed con ≥50 RC únicas")
    if not seed_coords_ok:
        print("   - seed con lat/lon válidos (0 inválidas)")
    if not coords_ok:
        print("   - acceso a Consulta_RCCOOR")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

