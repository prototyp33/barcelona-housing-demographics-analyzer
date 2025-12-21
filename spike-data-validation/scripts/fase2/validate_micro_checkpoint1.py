#!/usr/bin/env python3
"""
Checkpoint 1: ¿Son los datos Catastro realmente MICRO?

Valida que los datos obtenidos del Catastro son realmente a nivel de edificio
(no agregados) antes de continuar con la Fase 2 (scraping Idealista).

Criterios de validación:
- Completitud: ≥50% de edificios encontrados respecto al seed
- Variabilidad intra-barrio: std(superficie) > 15 m² (indica datos micro)
- Campos críticos: superficie, año construcción con <20% nulos

Uso:
    python3 spike-data-validation/scripts/fase2/validate_micro_checkpoint1.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def checkpoint_1_validate_micro() -> str:
    """
    Validar que datos son edificio-a-edificio (MICRO).
    
    Returns:
        "GO" si los datos son válidos para continuar, "REVISAR" en caso contrario.
    """
    logger.info("\n" + "=" * 70)
    logger.info("CHECKPOINT 1: VALIDACIÓN DATOS MICRO")
    logger.info("=" * 70)

    # Rutas de datos
    csv_path = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")
    seed_path = Path("spike-data-validation/data/raw/gracia_refs_seed.csv")
    output_dir = Path("spike-data-validation/data/fase2")
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "checkpoint1_result.json"

    # Cargar datos
    if not csv_path.exists():
        logger.error("No se encuentra: %s", csv_path)
        logger.error("Ejecuta primero el parser y filtro de Catastro")
        return "ERROR"

    if not seed_path.exists():
        logger.error("No se encuentra: %s", seed_path)
        return "ERROR"

    df_catastro = pd.read_csv(csv_path)
    df_seed = pd.read_csv(seed_path)

    logger.info("\n📊 DATOS CARGADOS:")
    logger.info("   Catastro: %s edificios", len(df_catastro))
    logger.info("   Seed: %s referencias esperadas", len(df_seed))

    # CHECK 1: ¿Encontramos suficientes edificios?
    logger.info("\n[CHECK 1] Completitud:")
    # Normalizar referencias a 14 caracteres para comparar
    df_catastro["ref_base"] = df_catastro["referencia_catastral"].astype(str).str[:14]
    df_seed["ref_base"] = df_seed["referencia_catastral"].astype(str).str[:14]
    
    refs_encontradas = df_catastro["ref_base"].nunique()
    refs_esperadas = df_seed["ref_base"].nunique()
    completitud = (refs_encontradas / refs_esperadas * 100) if refs_esperadas > 0 else 0
    
    logger.info("   Referencias encontradas: %s/%s (%.1f%%)", refs_encontradas, refs_esperadas, completitud)
    logger.info("   Edificios totales: %s", len(df_catastro))

    if completitud < 50:
        logger.warning("   ⚠️  ALERTA: Completitud baja (<50%%)")

    # CHECK 2: ¿Tienen datos los edificios?
    logger.info("\n[CHECK 2] Campos críticos rellenados:")
    completitud_campos: Dict[str, float] = {}
    for col in ["superficie_m2", "ano_construccion", "plantas"]:
        if col not in df_catastro.columns:
            logger.warning("   ⚠️  Columna '%s' no encontrada", col)
            completitud_campos[col] = 0.0
            continue
            
        nulls = df_catastro[col].isna().sum()
        completitud_col = (1 - nulls / len(df_catastro)) * 100 if len(df_catastro) > 0 else 0
        completitud_campos[col] = completitud_col
        logger.info("   %s: %.1f%% (%s nulos)", col, completitud_col, nulls)

        if completitud_col < 80:
            logger.warning("   ⚠️  ALERTA: Muchos nulos en %s", col)

    # CHECK 3: ¿Hay variabilidad INTRA-BARRIO en superficie?
    logger.info("\n[CHECK 3] Variabilidad INTRA-BARRIO (CRÍTICO para MICRO):")

    # Usar barrio_id del CSV si existe, sino hacer merge con seed
    if "barrio_id" not in df_catastro.columns:
        logger.info("   Haciendo merge con seed para obtener barrio_id...")
        df_merged = df_catastro.merge(
            df_seed[["ref_base", "barrio_id"]],
            on="ref_base",
            how="left",
        )
    else:
        df_merged = df_catastro.copy()
        df_merged["ref_base"] = df_catastro["referencia_catastral"].astype(str).str[:14]

    micro_ok = True
    detalles_barrios: Dict[str, Dict[str, Any]] = {}

    for barrio in sorted(df_merged["barrio_id"].dropna().unique()):
        df_b = df_merged[df_merged["barrio_id"] == barrio].copy()

        if "superficie_m2" not in df_b.columns or df_b["superficie_m2"].isna().all():
            logger.warning("   Barrio %s: Sin datos de superficie", int(barrio))
            micro_ok = False
            continue

        std_superficie = df_b["superficie_m2"].std()
        mean_superficie = df_b["superficie_m2"].mean()
        
        if "ano_construccion" in df_b.columns:
            std_ano = df_b["ano_construccion"].std()
        else:
            std_ano = None

        n_edificios = len(df_b)

        # CRITERIO: std > 15 m² indica datos micro
        # También verificamos que haya suficiente variabilidad relativa (CV > 0.15)
        cv = (std_superficie / mean_superficie) if mean_superficie > 0 else 0
        es_micro = std_superficie > 15 and cv > 0.15
        status = "✅ MICRO" if es_micro else "⚠️  AGREGADO?"

        logger.info(
            "   Barrio %s: %s edif, std_sup=%.1f m², CV=%.2f %s",
            int(barrio),
            n_edificios,
            std_superficie,
            cv,
            status,
        )

        if not es_micro:
            micro_ok = False

        detalles_barrios[f"barrio_{int(barrio)}"] = {
            "n_edificios": int(n_edificios),
            "std_superficie": float(std_superficie),
            "mean_superficie": float(mean_superficie),
            "cv": float(cv),
            "es_micro": bool(es_micro),
        }

    # DECISIÓN GO/NO-GO
    logger.info("\n" + "=" * 70)
    logger.info("DECISIÓN CHECKPOINT 1:")
    logger.info("=" * 70)

    if micro_ok and completitud >= 50:
        logger.info("✅ GO CON FASE 2")
        logger.info("   - Datos son edificio-a-edificio (variabilidad real)")
        logger.info("   - Completitud suficiente")
        logger.info("   → Proceder con Idealista scraping")
        decision = "GO"
    else:
        logger.warning("⚠️  REVISAR ANTES DE CONTINUAR")
        if not micro_ok:
            logger.warning("   - Variabilidad baja en superficie (posible agregación)")
        if completitud < 50:
            logger.warning("   - Completitud baja (<50%%)")
        logger.warning("   → Considerar NO-GO o ajustar estrategia")
        decision = "REVISAR"

    # Guardar resultado
    result: Dict[str, Any] = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "decision": decision,
        "completitud_pct": float(completitud),
        "micro_ok": micro_ok,
        "buildings_count": int(len(df_catastro)),
        "refs_encontradas": int(refs_encontradas),
        "refs_esperadas": int(refs_esperadas),
        "details": {
            "completitud_superficie": completitud_campos.get("superficie_m2", 0.0),
            "completitud_año": completitud_campos.get("ano_construccion", 0.0),
            "completitud_plantas": completitud_campos.get("plantas", 0.0),
            "barrios": detalles_barrios,
        },
    }

    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("=" * 70)
    logger.info("\n📄 Resultado guardado: %s", result_path)

    return decision


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    decision = checkpoint_1_validate_micro()

    if decision == "GO":
        logger.info("\n✅ CONTINUANDO CON FASE 2...")
        return 0
    elif decision == "REVISAR":
        logger.warning("\n⚠️  REVISAR ANTES DE CONTINUAR")
        return 0  # No abortar, pero advertencia clara
    else:
        logger.error("\n❌ ERROR EN VALIDACIÓN")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

