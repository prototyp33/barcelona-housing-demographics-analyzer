#!/usr/bin/env python3
"""
Matching heurístico Idealista ↔ Catastro (Fase 2 - Issue #202).

Linkea propiedades de Idealista (extraídas con Comet AI) con datos de Catastro
usando matching heurístico basado en:
- Localidad/Barrio (normalización y comparación)
- Superficie (m²) con tolerancia
- Número de habitaciones
- Descripción/Detalles (NLP básico para extraer características)

Genera dataset combinado para modelo hedónico MICRO.

Uso:
    python3 spike-data-validation/scripts/fase2/match_idealista_catastro.py \
        --idealista spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv \
        --catastro spike-data-validation/data/processed/catastro_gracia_real.csv \
        --output spike-data-validation/data/processed/fase2/idealista_catastro_matched.csv
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Rutas por defecto
INPUT_IDEALISTA = Path("spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv")
INPUT_CATASTRO = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def normalize_barrio_name(name: str) -> str:
    """
    Normaliza el nombre de un barrio para comparación.
    
    Args:
        name: Nombre del barrio
        
    Returns:
        Nombre normalizado (minúsculas, sin acentos, sin caracteres especiales)
    """
    if pd.isna(name) or not name:
        return ""
    
    # Convertir a minúsculas
    normalized = str(name).lower().strip()
    
    # Reemplazar acentos y caracteres especiales
    replacements = {
        'à': 'a', 'á': 'a', 'è': 'e', 'é': 'e', 'ì': 'i', 'í': 'i',
        'ò': 'o', 'ó': 'o', 'ù': 'u', 'ú': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c',
        '·': '', '-': ' ', '_': ' '
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Eliminar caracteres especiales y espacios múltiples
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def extract_features_from_description(text: str) -> Dict[str, bool]:
    """
    Extrae características de la descripción usando NLP básico.
    
    Args:
        text: Texto de descripción o detalles
        
    Returns:
        Diccionario con características extraídas (ascensor, exterior, terraza, etc.)
    """
    if pd.isna(text) or not text:
        return {
            'ascensor': False,
            'exterior': False,
            'terraza': False,
            'balcon': False,
            'piscina': False,
            'garaje': False,
        }
    
    text_lower = str(text).lower()
    
    features = {
        'ascensor': any(word in text_lower for word in ['ascensor', 'elevador', 'lift']),
        'exterior': any(word in text_lower for word in ['exterior', 'externa', 'fachada exterior']),
        'terraza': any(word in text_lower for word in ['terraza', 'terrazas', 'azotea']),
        'balcon': any(word in text_lower for word in ['balcón', 'balcon', 'balcones']),
        'piscina': any(word in text_lower for word in ['piscina', 'pool']),
        'garaje': any(word in text_lower for word in ['garaje', 'parking', 'aparcamiento', 'plaza de garaje']),
    }
    
    return features


def calculate_match_score(
    idealista_row: pd.Series,
    catastro_row: pd.Series,
    superficie_tolerance: float = 0.15,  # 15% de tolerancia
) -> float:
    """
    Calcula un score de matching entre una propiedad de Idealista y una de Catastro.
    
    Args:
        idealista_row: Fila de DataFrame de Idealista
        catastro_row: Fila de DataFrame de Catastro
        superficie_tolerance: Tolerancia para superficie (fracción, ej: 0.15 = 15%)
        
    Returns:
        Score de matching (0.0 a 1.0, donde 1.0 es match perfecto)
    """
    score = 0.0
    max_score = 0.0
    
    # 1. Localidad/Barrio (peso: 0.3)
    max_score += 0.3
    idealista_barrio = normalize_barrio_name(idealista_row.get('localidad', ''))
    catastro_barrio = normalize_barrio_name(catastro_row.get('barrio_nombre', ''))
    
    if idealista_barrio and catastro_barrio:
        if idealista_barrio == catastro_barrio:
            score += 0.3
        elif idealista_barrio in catastro_barrio or catastro_barrio in idealista_barrio:
            score += 0.2  # Match parcial
    elif not idealista_barrio and not catastro_barrio:
        score += 0.15  # Ambos vacíos, no penalizar
    
    # 2. Superficie (peso: 0.4)
    max_score += 0.4
    idealista_superficie = idealista_row.get('superficie_m2')
    catastro_superficie = catastro_row.get('superficie_m2')
    
    if pd.notna(idealista_superficie) and pd.notna(catastro_superficie):
        try:
            idealista_superficie = float(idealista_superficie)
            catastro_superficie = float(catastro_superficie)
            
            if catastro_superficie > 0:
                diff_ratio = abs(idealista_superficie - catastro_superficie) / catastro_superficie
                
                if diff_ratio <= superficie_tolerance:
                    # Score proporcional a la cercanía
                    score += 0.4 * (1 - diff_ratio / superficie_tolerance)
        except (ValueError, TypeError):
            pass
    
    # 3. Habitaciones (peso: 0.2)
    max_score += 0.2
    idealista_habitaciones = idealista_row.get('habitaciones')
    catastro_habitaciones = catastro_row.get('habitaciones')  # Si existe en Catastro
    
    if pd.notna(idealista_habitaciones) and pd.notna(catastro_habitaciones):
        try:
            if int(idealista_habitaciones) == int(catastro_habitaciones):
                score += 0.2
            elif abs(int(idealista_habitaciones) - int(catastro_habitaciones)) == 1:
                score += 0.1  # Diferencia de 1 habitación
        except (ValueError, TypeError):
            pass
    
    # 4. Características extraídas de descripción (peso: 0.1)
    max_score += 0.1
    idealista_desc = str(idealista_row.get('descripcion', '')) + ' ' + str(idealista_row.get('detalles', ''))
    idealista_features = extract_features_from_description(idealista_desc)
    
    # TODO: Extraer características de Catastro si están disponibles
    # Por ahora, solo usamos las de Idealista para el score base
    
    # Normalizar score a 0-1
    if max_score > 0:
        score = score / max_score
    
    return score


def match_heuristic(
    df_idealista: pd.DataFrame,
    df_catastro: pd.DataFrame,
    min_match_score: float = 0.5,
    superficie_tolerance: float = 0.15,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Realiza matching heurístico entre Idealista y Catastro.
    
    Args:
        df_idealista: DataFrame con propiedades de Idealista
        df_catastro: DataFrame con datos de Catastro
        min_match_score: Score mínimo para considerar un match válido
        superficie_tolerance: Tolerancia para superficie (fracción)
        
    Returns:
        Tupla con:
        - DataFrame combinado con matches exitosos
        - Diccionario con métricas de matching
    """
    logger.info("Iniciando matching heurístico...")
    logger.info(f"   Idealista: {len(df_idealista)} propiedades")
    logger.info(f"   Catastro: {len(df_catastro)} edificios")
    
    matched_rows = []
    match_scores = []
    
    # Para cada propiedad de Idealista, buscar el mejor match en Catastro
    for idx, idealista_row in df_idealista.iterrows():
        best_match = None
        best_score = 0.0
        
        # Buscar en todos los edificios de Catastro
        for catastro_idx, catastro_row in df_catastro.iterrows():
            score = calculate_match_score(
                idealista_row,
                catastro_row,
                superficie_tolerance=superficie_tolerance,
            )
            
            if score > best_score:
                best_score = score
                best_match = catastro_row
        
        # Si encontramos un match con score suficiente, agregarlo
        if best_match is not None and best_score >= min_match_score:
            # Combinar datos de Idealista y Catastro
            combined_row = idealista_row.to_dict()
            
            # Agregar datos de Catastro con prefijo
            for col in df_catastro.columns:
                if col not in combined_row:  # Evitar sobrescribir columnas de Idealista
                    combined_row[f'catastro_{col}'] = best_match[col]
            
            combined_row['match_score'] = best_score
            matched_rows.append(combined_row)
            match_scores.append(best_score)
        else:
            # Propiedad sin match (guardar solo datos de Idealista)
            combined_row = idealista_row.to_dict()
            combined_row['match_score'] = best_score if best_match is not None else 0.0
            combined_row['matched'] = False
            matched_rows.append(combined_row)
    
    df_matched = pd.DataFrame(matched_rows)
    
    # Calcular métricas
    total_idealista = len(df_idealista)
    matched_count = len([s for s in match_scores if s >= min_match_score])
    match_rate = (matched_count / total_idealista * 100) if total_idealista > 0 else 0.0
    
    metrics = {
        'total_idealista': total_idealista,
        'total_catastro': len(df_catastro),
        'matched_count': matched_count,
        'unmatched_count': total_idealista - matched_count,
        'match_rate_percent': match_rate,
        'avg_match_score': float(pd.Series(match_scores).mean()) if match_scores else 0.0,
        'min_match_score': float(min(match_scores)) if match_scores else 0.0,
        'max_match_score': float(max(match_scores)) if match_scores else 0.0,
        'min_match_threshold': min_match_score,
        'superficie_tolerance': superficie_tolerance,
    }
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("MÉTRICAS DE MATCHING")
    logger.info("=" * 70)
    logger.info(f"Propiedades Idealista: {metrics['total_idealista']}")
    logger.info(f"Edificios Catastro: {metrics['total_catastro']}")
    logger.info(f"Matches exitosos: {metrics['matched_count']} ({metrics['match_rate_percent']:.1f}%)")
    logger.info(f"Sin match: {metrics['unmatched_count']}")
    logger.info(f"Score promedio: {metrics['avg_match_score']:.3f}")
    logger.info(f"Score mínimo: {metrics['min_match_score']:.3f}")
    logger.info(f"Score máximo: {metrics['max_match_score']:.3f}")
    
    return df_matched, metrics


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Matching heurístico Idealista ↔ Catastro"
    )
    parser.add_argument(
        "--idealista",
        type=str,
        default=str(INPUT_IDEALISTA),
        help="CSV de propiedades de Idealista (Comet AI)",
    )
    parser.add_argument(
        "--catastro",
        type=str,
        default=str(INPUT_CATASTRO),
        help="CSV de datos de Catastro",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_DIR / "idealista_catastro_matched.csv"),
        help="CSV de salida con matches",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Score mínimo para considerar un match válido (0.0-1.0)",
    )
    parser.add_argument(
        "--superficie-tolerance",
        type=float,
        default=0.15,
        help="Tolerancia para superficie (fracción, ej: 0.15 = 15%%)",
    )
    parser.add_argument(
        "--metrics-output",
        type=str,
        default=None,
        help="Archivo JSON para guardar métricas de matching",
    )
    
    args = parser.parse_args()
    
    # Validar archivos de entrada
    idealista_path = Path(args.idealista)
    catastro_path = Path(args.catastro)
    
    if not idealista_path.exists():
        logger.error(f"❌ Archivo Idealista no encontrado: {idealista_path}")
        return 1
    
    if not catastro_path.exists():
        logger.error(f"❌ Archivo Catastro no encontrado: {catastro_path}")
        logger.error("   Nota: El archivo debe generarse primero con el pipeline de Catastro")
        return 1
    
    # Cargar datos
    logger.info("Cargando datos...")
    logger.info(f"   Idealista: {idealista_path}")
    df_idealista = pd.read_csv(idealista_path)
    logger.info(f"   ✅ {len(df_idealista)} propiedades cargadas")
    
    logger.info(f"   Catastro: {catastro_path}")
    df_catastro = pd.read_csv(catastro_path)
    logger.info(f"   ✅ {len(df_catastro)} edificios cargados")
    
    # Realizar matching
    df_matched, metrics = match_heuristic(
        df_idealista,
        df_catastro,
        min_match_score=args.min_score,
        superficie_tolerance=args.superficie_tolerance,
    )
    
    # Guardar resultados
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_matched.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info(f"📄 Dataset combinado guardado: {output_path}")
    logger.info(f"   Filas: {len(df_matched)}")
    logger.info(f"   Columnas: {len(df_matched.columns)}")
    
    # Guardar métricas
    if args.metrics_output:
        metrics_path = Path(args.metrics_output)
        metrics['timestamp'] = datetime.now().isoformat()
        metrics['input_files'] = {
            'idealista': str(idealista_path),
            'catastro': str(catastro_path),
        }
        metrics['output_file'] = str(output_path)
        
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        logger.info(f"📊 Métricas guardadas: {metrics_path}")
    else:
        # Guardar métricas en el mismo directorio que el output
        metrics_path = output_path.parent / f"{output_path.stem}_metrics.json"
        metrics['timestamp'] = datetime.now().isoformat()
        metrics['input_files'] = {
            'idealista': str(idealista_path),
            'catastro': str(catastro_path),
        }
        metrics['output_file'] = str(output_path)
        
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        logger.info(f"📊 Métricas guardadas: {metrics_path}")
    
    logger.info("")
    logger.info("✅ Matching completado")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

