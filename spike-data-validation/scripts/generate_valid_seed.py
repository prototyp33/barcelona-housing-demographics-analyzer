#!/usr/bin/env python3
"""
Genera seed de referencias catastrales VÁLIDAS para Gràcia.

Estrategia:
1. Obtener direcciones reales de Gràcia
2. Consultar Catastro SOAP por cada dirección usando Consulta_DNPLOC
3. Guardar referencias encontradas como seed

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

# Añadir directorio de scripts al PYTHONPATH
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from catastro_soap_client import CatastroSOAPClient, CatastroSOAPError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Direcciones conocidas de Gràcia (muestra inicial)
# Formato: tipo_via, nombre_via, numero
DIRECCIONES_GRACIA = [
    {"tipo_via": "CL", "nombre": "GRAN DE GRACIA", "numero": "1"},
    {"tipo_via": "CL", "nombre": "GRAN DE GRACIA", "numero": "50"},
    {"tipo_via": "CL", "nombre": "GRAN DE GRACIA", "numero": "100"},
    {"tipo_via": "CL", "nombre": "GRAN DE GRACIA", "numero": "150"},
    {"tipo_via": "CL", "nombre": "GRAN DE GRACIA", "numero": "200"},
    {"tipo_via": "CL", "nombre": "TORRIJOS", "numero": "1"},
    {"tipo_via": "CL", "nombre": "TORRIJOS", "numero": "25"},
    {"tipo_via": "CL", "nombre": "TORRIJOS", "numero": "50"},
    {"tipo_via": "PZ", "nombre": "SOL", "numero": "1"},
    {"tipo_via": "PZ", "nombre": "SOL", "numero": "2"},
    {"tipo_via": "PZ", "nombre": "RIUS I TAULET", "numero": "1"},
    {"tipo_via": "CL", "nombre": "VERDI", "numero": "1"},
    {"tipo_via": "CL", "nombre": "VERDI", "numero": "50"},
    {"tipo_via": "CL", "nombre": "VERDI", "numero": "100"},
    {"tipo_via": "CL", "nombre": "FRATERNITAT", "numero": "1"},
    {"tipo_via": "CL", "nombre": "FRATERNITAT", "numero": "50"},
    {"tipo_via": "CL", "nombre": "ASTURIES", "numero": "1"},
    {"tipo_via": "CL", "nombre": "ASTURIES", "numero": "50"},
    {"tipo_via": "CL", "nombre": "PERLA", "numero": "1"},
    {"tipo_via": "CL", "nombre": "PERLA", "numero": "50"},
    {"tipo_via": "CL", "nombre": "PROVENCA", "numero": "200"},
    {"tipo_via": "CL", "nombre": "PROVENCA", "numero": "250"},
    {"tipo_via": "CL", "nombre": "PROVENCA", "numero": "300"},
    {"tipo_via": "CL", "nombre": "SANT DOMENEC", "numero": "1"},
    {"tipo_via": "CL", "nombre": "SANT DOMENEC", "numero": "50"},
    {"tipo_via": "CL", "nombre": "ROS DE OLANO", "numero": "1"},
    {"tipo_via": "CL", "nombre": "ROS DE OLANO", "numero": "50"},
    {"tipo_via": "CL", "nombre": "MONTSENY", "numero": "1"},
    {"tipo_via": "CL", "nombre": "MONTSENY", "numero": "50"},
    {"tipo_via": "CL", "nombre": "PUJADES", "numero": "1"},
    {"tipo_via": "CL", "nombre": "PUJADES", "numero": "50"},
    # Añadir más direcciones según necesidad
]


def generate_seed(
    output_path: Path,
    max_refs: int = 60,
    provincia: str = "08",
    municipio: str = "019",
) -> int:
    """
    Genera seed de referencias válidas consultando por dirección.

    Args:
        output_path: Ruta CSV de salida
        max_refs: Número máximo de referencias a obtener
        provincia: Código provincia (08 = Barcelona)
        municipio: Código municipio (019 = Barcelona ciudad)

    Returns:
        Número de referencias encontradas
    """
    client = CatastroSOAPClient()

    referencias: List[Dict[str, str]] = []
    total_direcciones = len(DIRECCIONES_GRACIA)

    logger.info(
        f"Iniciando generación de seed válido para Gràcia "
        f"(objetivo: {max_refs} referencias, {total_direcciones} direcciones a probar)"
    )

    for idx, direccion in enumerate(DIRECCIONES_GRACIA, start=1):
        if len(referencias) >= max_refs:
            logger.info(f"Objetivo alcanzado: {len(referencias)} referencias")
            break

        try:
            logger.info(
                f"({idx}/{total_direcciones}) Consultando: "
                f"{direccion['tipo_via']} {direccion['nombre']} {direccion['numero']}"
            )

            rc = client.get_rc_by_address(
                provincia=provincia,
                municipio=municipio,
                tipo_via=direccion["tipo_via"],
                nombre_via=direccion["nombre"],
                numero=direccion["numero"],
            )

            if rc:
                referencias.append(
                    {
                        "referencia_catastral": rc,
                        "tipo_via": direccion["tipo_via"],
                        "nombre_via": direccion["nombre"],
                        "numero": direccion["numero"],
                        "barrio": "Gràcia",  # Se puede refinar después
                        "direccion_completa": f"{direccion['tipo_via']} {direccion['nombre']} {direccion['numero']}",
                    }
                )
                logger.info(f"  ✓ Encontrada: {rc} ({len(referencias)}/{max_refs})")
            else:
                logger.warning(f"  ✗ No encontrada")

            # Rate limiting cortés (0.5 segundos entre peticiones)
            if idx < total_direcciones:
                time.sleep(0.5)

        except CatastroSOAPError as exc:
            logger.warning(f"  ✗ Error Catastro: {exc}")
            continue
        except Exception as exc:
            logger.error(f"  ✗ Error inesperado: {exc}", exc_info=True)
            continue

    # Guardar seed
    if referencias:
        df_seed = pd.DataFrame(referencias)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_seed.to_csv(output_path, index=False, encoding="utf-8")

        logger.info(f"\n✓ Seed guardado: {output_path}")
        logger.info(f"  Referencias válidas: {len(referencias)}")
        logger.info(f"  Columnas: {list(df_seed.columns)}")
    else:
        logger.error("\n✗ No se encontró ninguna referencia válida")
        logger.error("  Verifica las direcciones o la conexión con el Catastro")

    return len(referencias)


def main() -> int:
    """Función principal."""
    output_path = Path("spike-data-validation/data/raw/gracia_refs_seed_valid.csv")

    logger.info("=" * 70)
    logger.info("GENERACIÓN DE SEED VÁLIDO - ISSUE #200")
    logger.info("=" * 70)

    num_refs = generate_seed(output_path, max_refs=60)

    if num_refs >= 50:
        logger.info("\n✅ Seed válido generado (≥50 referencias)")
        logger.info(f"   Archivo: {output_path}")
        logger.info("\nPróximos pasos:")
        logger.info("  1. Verificar seed: python -c \"import pandas as pd; df = pd.read_csv('spike-data-validation/data/raw/gracia_refs_seed_valid.csv'); print(df.head())\"")
        logger.info("  2. Probar extracción: python spike-data-validation/scripts/extract_catastro_gracia.py")
        return 0
    else:
        logger.warning(f"\n⚠️  Solo {num_refs} referencias encontradas (<50)")
        logger.warning("Considera:")
        logger.warning("  - Añadir más direcciones a DIRECCIONES_GRACIA")
        logger.warning("  - Verificar formato de direcciones (tipo_via, nombre_via)")
        logger.warning("  - Usar dataset de Portal Dades con direcciones reales")
        return 1


if __name__ == "__main__":
    sys.exit(main())

