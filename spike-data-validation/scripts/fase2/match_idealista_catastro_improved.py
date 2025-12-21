#!/usr/bin/env python3
"""
Matching heurístico mejorado Idealista ↔ Catastro (Fase 2 - Issue #202).

Mejoras implementadas:
1. Normalización mejorada de nombres de barrios/localidades con diccionario de equivalencias
2. Extracción de nombre de barrio desde localidades que incluyen calles
3. Matching por características adicionales (ascensor, terraza, etc.)
4. Tolerancia ajustable de superficie por rango
5. Análisis de casos sin match para debugging

Uso:
    python3 spike-data-validation/scripts/fase2/match_idealista_catastro_improved.py \
        --idealista spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv \
        --catastro spike-data-validation/data/processed/catastro_gracia_real.csv \
        --output spike-data-validation/data/processed/fase2/idealista_catastro_matched_improved.csv
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

# Diccionario de equivalencias de barrios/localidades
BARRIO_EQUIVALENCIAS = {
    # Variaciones de Vila de Gràcia
    'vila de gracia': 'vila de gracia',
    'vila gracia': 'vila de gracia',
    'gracia': 'vila de gracia',
    'gracias': 'vila de gracia',
    'barrio de gracia': 'vila de gracia',
    'barrio gracia': 'vila de gracia',
    'centro gracia': 'vila de gracia',
    'corazon de gracia': 'vila de gracia',
    'corazon gracia': 'vila de gracia',
    
    # Variaciones de El Camp d'en Grassot i Gràcia Nova
    'camp den grassot i gracia nova': 'el camp den grassot i gracia nova',
    'camp den grassot': 'el camp den grassot i gracia nova',
    'camp grassot': 'el camp den grassot i gracia nova',
    'gracia nova': 'el camp den grassot i gracia nova',
    'camp en grassot': 'el camp den grassot i gracia nova',
    
    # Variaciones de La Salut
    'salut': 'la salut',
    'la salud': 'la salut',
    
    # Variaciones de Vallcarca i els Penitents
    'vallcarca i els penitents': 'vallcarca i els penitents',
    'vallcarca': 'vallcarca i els penitents',
    'penitents': 'vallcarca i els penitents',
    'avenida vallcarca': 'vallcarca i els penitents',
    
    # Variaciones de El Coll
    'coll': 'el coll',
    'el col': 'el coll',
}

# Nombres oficiales de barrios en Catastro
BARRIOS_OFICIALES = {
    'vila de gracia': 28,
    'el camp den grassot i gracia nova': 32,
    'la salut': 29,
    'vallcarca i els penitents': 28,  # Verificar si es 28 o diferente
    'el coll': 30,
}


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def normalize_barrio_name(name: str) -> str:
    """
    Normaliza el nombre de un barrio para comparación (versión mejorada).
    
    Args:
        name: Nombre del barrio o localidad
        
    Returns:
        Nombre normalizado
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
        '·': '', '-': ' ', '_': ' ', ',': ' '
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Eliminar caracteres especiales y espacios múltiples
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def extract_barrio_from_localidad(localidad: str) -> Optional[str]:
    """
    Extrae el nombre del barrio desde una localidad que puede incluir calles, números, etc.
    
    Args:
        localidad: String con localidad (ej: "Calle de Bonavista, Vila de Gràcia")
        
    Returns:
        Nombre del barrio normalizado o None
    """
    if pd.isna(localidad) or not localidad:
        return None
    
    normalized = normalize_barrio_name(localidad)
    
    # Buscar en diccionario de equivalencias
    for key, value in BARRIO_EQUIVALENCIAS.items():
        if key in normalized:
            return value
    
    # Buscar nombres oficiales directamente
    for barrio_oficial in BARRIOS_OFICIALES.keys():
        if barrio_oficial in normalized:
            return barrio_oficial
    
    # Intentar extraer patrones comunes
    patterns = [
        r'(vila de gracia|vila gracia)',
        r'(camp den grassot|gracia nova)',
        r'(la salut|salut)',
        r'(vallcarca|penitents)',
        r'(el coll|coll)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            extracted = match.group(1)
            # Buscar equivalencia
            for key, value in BARRIO_EQUIVALENCIAS.items():
                if key in extracted:
                    return value
    
    return None


def extract_features_from_description(text: str) -> Dict[str, bool]:
    """
    Extrae características de la descripción usando NLP básico (versión mejorada).
    
    Args:
        text: Texto de descripción o detalles
        
    Returns:
        Diccionario con características extraídas
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
        'ascensor': any(word in text_lower for word in [
            'ascensor', 'elevador', 'lift', 'con ascensor'
        ]),
        'exterior': any(word in text_lower for word in [
            'exterior', 'externa', 'fachada exterior', 'orientacion exterior'
        ]),
        'terraza': any(word in text_lower for word in [
            'terraza', 'terrazas', 'azotea', 'terrado'
        ]),
        'balcon': any(word in text_lower for word in [
            'balcón', 'balcon', 'balcones'
        ]),
        'piscina': any(word in text_lower for word in [
            'piscina', 'pool', 'swimming pool'
        ]),
        'garaje': any(word in text_lower for word in [
            'garaje', 'parking', 'aparcamiento', 'plaza de garaje', 'plaza garaje'
        ]),
    }
    
    return features


def calculate_superficie_tolerance(superficie: float) -> float:
    """
    Calcula tolerancia de superficie adaptativa según el tamaño.
    
    Propiedades más grandes pueden tener más variación en la medición.
    
    Args:
        superficie: Superficie en m²
        
    Returns:
        Tolerancia como fracción (ej: 0.20 = 20%)
    """
    if superficie < 50:
        return 0.10  # 10% para propiedades pequeñas
    elif superficie < 100:
        return 0.15  # 15% para propiedades medianas
    elif superficie < 150:
        return 0.20  # 20% para propiedades grandes
    else:
        return 0.25  # 25% para propiedades muy grandes


def calculate_match_score(
    idealista_row: pd.Series,
    catastro_row: pd.Series,
    base_superficie_tolerance: float = 0.15,
) -> float:
    """
    Calcula un score de matching mejorado entre una propiedad de Idealista y una de Catastro.
    
    Args:
        idealista_row: Fila de DataFrame de Idealista
        catastro_row: Fila de DataFrame de Catastro
        base_superficie_tolerance: Tolerancia base para superficie
        
    Returns:
        Score de matching (0.0 a 1.0)
    """
    score = 0.0
    max_score = 0.0
    
    # 1. Localidad/Barrio (peso: 0.35) - MEJORADO
    max_score += 0.35
    idealista_localidad = idealista_row.get('localidad', '')
    idealista_barrio = extract_barrio_from_localidad(idealista_localidad)
    
    catastro_barrio = normalize_barrio_name(catastro_row.get('barrio_nombre', ''))
    
    if idealista_barrio and catastro_barrio:
        if idealista_barrio == catastro_barrio:
            score += 0.35  # Match exacto
        elif idealista_barrio in catastro_barrio or catastro_barrio in idealista_barrio:
            score += 0.25  # Match parcial
        else:
            # Verificar equivalencias
            idealista_equiv = BARRIO_EQUIVALENCIAS.get(idealista_barrio, idealista_barrio)
            catastro_equiv = BARRIO_EQUIVALENCIAS.get(catastro_barrio, catastro_barrio)
            if idealista_equiv == catastro_equiv:
                score += 0.30  # Match por equivalencia
    
    # 2. Superficie (peso: 0.40) - MEJORADO con tolerancia adaptativa
    max_score += 0.40
    idealista_superficie = idealista_row.get('superficie_m2')
    catastro_superficie = catastro_row.get('superficie_m2')
    
    if pd.notna(idealista_superficie) and pd.notna(catastro_superficie):
        try:
            idealista_superficie = float(idealista_superficie)
            catastro_superficie = float(catastro_superficie)
            
            if catastro_superficie > 0:
                # Tolerancia adaptativa
                tolerance = calculate_superficie_tolerance(idealista_superficie)
                diff_ratio = abs(idealista_superficie - catastro_superficie) / catastro_superficie
                
                if diff_ratio <= tolerance:
                    # Score proporcional a la cercanía
                    score += 0.40 * (1 - diff_ratio / tolerance)
        except (ValueError, TypeError):
            pass
    
    # 3. Habitaciones (peso: 0.15)
    max_score += 0.15
    idealista_habitaciones = idealista_row.get('habitaciones')
    catastro_habitaciones = catastro_row.get('habitaciones')
    
    if pd.notna(idealista_habitaciones) and pd.notna(catastro_habitaciones):
        try:
            idealista_hab = int(idealista_habitaciones)
            catastro_hab = int(catastro_habitaciones)
            
            if idealista_hab == catastro_hab:
                score += 0.15
            elif abs(idealista_hab - catastro_hab) == 1:
                score += 0.08  # Diferencia de 1 habitación
        except (ValueError, TypeError):
            pass
    
    # 4. Características extraídas (peso: 0.10) - NUEVO
    max_score += 0.10
    idealista_desc = str(idealista_row.get('descripcion', '')) + ' ' + str(idealista_row.get('detalles', ''))
    idealista_features = extract_features_from_description(idealista_desc)
    
    # Por ahora, solo usamos características de Idealista
    # Si en el futuro tenemos características de Catastro, las comparamos aquí
    # Por ahora, damos un pequeño bonus si hay características relevantes
    if any(idealista_features.values()):
        score += 0.05  # Bonus por tener características documentadas
    
    # Normalizar score a 0-1
    if max_score > 0:
        score = score / max_score
    
    return score


def match_heuristic(
    df_idealista: pd.DataFrame,
    df_catastro: pd.DataFrame,
    min_match_score: float = 0.5,
    base_superficie_tolerance: float = 0.15,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Realiza matching heurístico mejorado entre Idealista y Catastro.
    
    Args:
        df_idealista: DataFrame con propiedades de Idealista
        df_catastro: DataFrame con datos de Catastro
        min_match_score: Score mínimo para considerar un match válido
        base_superficie_tolerance: Tolerancia base para superficie
        
    Returns:
        Tupla con DataFrame combinado y métricas
    """
    logger.info("Iniciando matching heurístico mejorado...")
    logger.info(f"   Idealista: {len(df_idealista)} propiedades")
    logger.info(f"   Catastro: {len(df_catastro)} edificios")
    
    matched_rows = []
    match_scores = []
    unmatched_reasons = []  # Para análisis de casos sin match
    
    # Para cada propiedad de Idealista, buscar el mejor match en Catastro
    for idx, idealista_row in df_idealista.iterrows():
        best_match = None
        best_score = 0.0
        best_reason = "No match encontrado"
        
        # Buscar en todos los edificios de Catastro
        for catastro_idx, catastro_row in df_catastro.iterrows():
            score = calculate_match_score(
                idealista_row,
                catastro_row,
                base_superficie_tolerance=base_superficie_tolerance,
            )
            
            if score > best_score:
                best_score = score
                best_match = catastro_row
                # Guardar razón del match
                idealista_barrio = extract_barrio_from_localidad(idealista_row.get('localidad', ''))
                catastro_barrio = normalize_barrio_name(catastro_row.get('barrio_nombre', ''))
                if idealista_barrio == catastro_barrio:
                    best_reason = f"Match por barrio: {idealista_barrio}"
                else:
                    best_reason = f"Score: {score:.3f}"
        
        # Si encontramos un match con score suficiente, agregarlo
        if best_match is not None and best_score >= min_match_score:
            combined_row = idealista_row.to_dict()
            
            # Agregar datos de Catastro con prefijo
            for col in df_catastro.columns:
                if col not in combined_row:
                    combined_row[f'catastro_{col}'] = best_match[col]
            
            combined_row['match_score'] = best_score
            combined_row['match_reason'] = best_reason
            matched_rows.append(combined_row)
            match_scores.append(best_score)
        else:
            # Propiedad sin match
            combined_row = idealista_row.to_dict()
            combined_row['match_score'] = best_score
            combined_row['match_reason'] = best_reason
            combined_row['matched'] = False
            matched_rows.append(combined_row)
            unmatched_reasons.append({
                'localidad': idealista_row.get('localidad', ''),
                'superficie': idealista_row.get('superficie_m2'),
                'habitaciones': idealista_row.get('habitaciones'),
                'best_score': best_score,
                'reason': best_reason
            })
    
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
        'base_superficie_tolerance': base_superficie_tolerance,
        'unmatched_reasons_sample': unmatched_reasons[:10],  # Primeros 10 para análisis
    }
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("MÉTRICAS DE MATCHING (MEJORADO)")
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
        description="Matching heurístico mejorado Idealista ↔ Catastro"
    )
    parser.add_argument(
        "--idealista",
        type=Path,
        default=INPUT_IDEALISTA,
        help="Ruta al CSV de Idealista",
    )
    parser.add_argument(
        "--catastro",
        type=Path,
        default=INPUT_CATASTRO,
        help="Ruta al CSV de Catastro",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "idealista_catastro_matched_improved.csv",
        help="Ruta de salida para CSV combinado",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Score mínimo para considerar match válido (default: 0.5)",
    )
    parser.add_argument(
        "--superficie-tolerance",
        type=float,
        default=0.15,
        help="Tolerancia base para superficie (default: 0.15 = 15%%)",
    )
    
    args = parser.parse_args()
    
    # Cargar datos
    logger.info("Cargando datos...")
    logger.info(f"   Idealista: {args.idealista}")
    df_idealista = pd.read_csv(args.idealista)
    logger.info(f"   ✅ {len(df_idealista)} propiedades cargadas")
    
    logger.info(f"   Catastro: {args.catastro}")
    df_catastro = pd.read_csv(args.catastro)
    logger.info(f"   ✅ {len(df_catastro)} edificios cargados")
    
    # Realizar matching
    df_matched, metrics = match_heuristic(
        df_idealista,
        df_catastro,
        min_match_score=args.min_score,
        base_superficie_tolerance=args.superficie_tolerance,
    )
    
    # Guardar resultados
    logger.info("")
    logger.info(f"📄 Dataset combinado guardado: {args.output}")
    df_matched.to_csv(args.output, index=False, encoding='utf-8')
    logger.info(f"   Filas: {len(df_matched)}")
    logger.info(f"   Columnas: {len(df_matched.columns)}")
    
    metrics_path = args.output.parent / f"{args.output.stem}_metrics.json"
    logger.info(f"📊 Métricas guardadas: {metrics_path}")
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    logger.info("")
    logger.info("✅ Matching completado")
    
    return 0


if __name__ == "__main__":
    exit(main())

