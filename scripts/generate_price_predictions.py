#!/usr/bin/env python3
"""
Generate Price Predictions for 2026-2027 using ARIMA Model.

This script:
1. Loads cleaned fact_precios data from the database
2. Trains ARIMA models for each barrio with sufficient historical data
3. Generates forecasts for 2026-2027 with confidence intervals
4. Calculates volatility index per barrio/district
5. Exports predictions to CSV for the Intelligence View dashboard

Output: notebooks/exports/predicciones_precios_2026_2027.csv
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import sqlite3

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import DEFAULT_DB_NAME, create_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check for ARIMA availability
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False
    logger.error("statsmodels no está instalado. Instala con: pip install statsmodels")
    sys.exit(1)


def get_historical_prices(conn: sqlite3.Connection, barrio_id: Optional[int] = None) -> pd.DataFrame:
    """
    Obtiene datos históricos de precios desde fact_precios (usando datos limpios).
    
    Args:
        conn: Conexión a la base de datos.
        barrio_id: ID del barrio (None para todos).
    
    Returns:
        DataFrame con columnas: barrio_id, barrio_nombre, distrito_nombre, anio, precio_m2_venta
    """
    query = """
        SELECT 
            p.barrio_id,
            b.barrio_nombre,
            b.distrito_nombre,
            p.anio,
            AVG(p.precio_m2_venta) as precio_m2_venta
        FROM fact_precios p
        JOIN dim_barrios b ON p.barrio_id = b.barrio_id
        WHERE p.precio_m2_venta IS NOT NULL 
          AND p.precio_m2_venta > 0
    """
    
    params = []
    if barrio_id:
        query += " AND p.barrio_id = ?"
        params.append(barrio_id)
    
    query += """
        GROUP BY p.barrio_id, p.anio
        ORDER BY p.barrio_id, p.anio
    """
    
    df = pd.read_sql_query(query, conn, params=params)
    return df


def optimize_arima_order(ts: pd.Series, max_p: int = 3, max_d: int = 2, max_q: int = 3) -> Tuple[int, int, int]:
    """
    Optimiza los parámetros (p, d, q) del modelo ARIMA usando AIC.
    
    Args:
        ts: Serie temporal.
        max_p: Máximo valor de p.
        max_d: Máximo valor de d.
        max_q: Máximo valor de q.
    
    Returns:
        Tupla (p, d, q) con los mejores parámetros.
    """
    best_aic = np.inf
    best_order = (1, 1, 1)  # Default
    
    # Verificar estacionariedad
    try:
        adf_result = adfuller(ts.dropna())
        is_stationary = adf_result[1] < 0.05
        d_start = 0 if is_stationary else 1
    except:
        d_start = 1
    
    for p in range(max_p + 1):
        for d in range(d_start, max_d + 1):
            for q in range(max_q + 1):
                try:
                    model = ARIMA(ts, order=(p, d, q))
                    fitted = model.fit()
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_order = (p, d, q)
                except:
                    continue
    
    return best_order


def forecast_barrio_prices(
    df_historical: pd.DataFrame,
    barrio_id: int,
    forecast_years: List[int] = [2026, 2027],
    optimize: bool = True
) -> Optional[Dict]:
    """
    Genera predicciones ARIMA para un barrio específico.
    
    Args:
        df_historical: DataFrame con datos históricos del barrio.
        barrio_id: ID del barrio.
        forecast_years: Lista de años a predecir.
        optimize: Si True, optimiza parámetros ARIMA.
    
    Returns:
        Diccionario con predicciones o None si no hay suficientes datos.
    """
    # Filtrar datos del barrio
    df_barrio = df_historical[df_historical['barrio_id'] == barrio_id].copy()
    
    if len(df_barrio) < 3:
        logger.debug(f"Barrio {barrio_id}: Insuficientes datos históricos ({len(df_barrio)} años)")
        return None
    
    # Ordenar por año
    df_barrio = df_barrio.sort_values('anio')
    
    # Crear serie temporal con índice de fecha (ARIMA requiere DatetimeIndex o RangeIndex)
    # Usamos RangeIndex empezando en 0 para evitar problemas con años
    ts_values = df_barrio['precio_m2_venta'].dropna().values
    
    if len(ts_values) < 3:
        logger.debug(f"Barrio {barrio_id}: Serie temporal muy corta después de limpiar")
        return None
    
    # Guardar años originales para referencia
    years = df_barrio['anio'].values
    
    try:
        # Optimizar parámetros o usar default
        if optimize and len(ts_values) >= 5:
            # Crear serie temporal para optimización
            ts_for_opt = pd.Series(ts_values, index=pd.RangeIndex(len(ts_values)))
            order = optimize_arima_order(ts_for_opt)
            logger.debug(f"Barrio {barrio_id}: Parámetros ARIMA optimizados: {order}")
        else:
            order = (1, 1, 1)  # Default
        
        # Crear serie temporal con RangeIndex para ARIMA
        ts = pd.Series(ts_values, index=pd.RangeIndex(len(ts_values)))
        
        # Entrenar modelo
        model = ARIMA(ts, order=order)
        fitted_model = model.fit()
        
        # Calcular horizonte (años a predecir)
        last_year = int(years[-1])
        horizon = len(forecast_years)
        
        # Generar predicciones
        forecast = fitted_model.forecast(steps=horizon)
        conf_int = fitted_model.get_forecast(steps=horizon).conf_int()
        
        # Preparar resultados
        predictions = []
        for i, year in enumerate(forecast_years):
            predictions.append({
                'barrio_id': barrio_id,
                'barrio_nombre': df_barrio['barrio_nombre'].iloc[0],
                'distrito_nombre': df_barrio['distrito_nombre'].iloc[0],
                'anio': year,
                'precio_predicho': float(forecast.iloc[i]),
                'intervalo_inferior': float(conf_int.iloc[i, 0]),
                'intervalo_superior': float(conf_int.iloc[i, 1]),
                'model_aic': float(fitted_model.aic),
                'historical_years': len(ts_values),
                'last_historical_year': last_year,
                'last_historical_price': float(ts_values[-1]),
            })
        
        return {
            'barrio_id': barrio_id,
            'predictions': predictions,
            'model_order': order,
            'model_aic': float(fitted_model.aic),
        }
        
    except Exception as e:
        logger.warning(f"Error en forecasting para barrio {barrio_id}: {e}")
        return None


def calculate_volatility_index(df_historical: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula índice de volatilidad por barrio y distrito.
    
    Args:
        df_historical: DataFrame con datos históricos.
    
    Returns:
        DataFrame con métricas de volatilidad.
    """
    volatility_results = []
    
    # Por barrio
    for barrio_id, group in df_historical.groupby('barrio_id'):
        if len(group) < 3:
            continue
        
        prices = group['precio_m2_venta'].values
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        coef_variation = (std_price / mean_price) * 100 if mean_price > 0 else 0
        
        volatility_results.append({
            'barrio_id': barrio_id,
            'barrio_nombre': group['barrio_nombre'].iloc[0],
            'distrito_nombre': group['distrito_nombre'].iloc[0],
            'volatilidad_coef_variacion': coef_variation,
            'precio_medio': mean_price,
            'precio_std': std_price,
            'precio_min': np.min(prices),
            'precio_max': np.max(prices),
            'rango_precios': np.max(prices) - np.min(prices),
            'anios_disponibles': len(group),
        })
    
    df_volatility = pd.DataFrame(volatility_results)
    
    # Agregar ranking
    if not df_volatility.empty:
        df_volatility['volatilidad_rank'] = df_volatility['volatilidad_coef_variacion'].rank(ascending=False)
        df_volatility['volatilidad_categoria'] = pd.cut(
            df_volatility['volatilidad_coef_variacion'],
            bins=[0, 10, 20, 30, 100],
            labels=['Muy Estable', 'Estable', 'Moderado', 'Volátil']
        )
    
    return df_volatility


def generate_all_predictions(
    db_path: Optional[Path] = None,
    forecast_years: List[int] = [2026, 2027],
    min_years: int = 3
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Genera predicciones para todos los barrios con datos suficientes.
    
    Args:
        db_path: Ruta a la base de datos.
        forecast_years: Años a predecir.
        min_years: Mínimo de años históricos requeridos.
    
    Returns:
        Tupla con (DataFrame de predicciones, DataFrame de volatilidad).
    """
    if db_path is None:
        db_path = PROJECT_ROOT / "data" / "processed" / DEFAULT_DB_NAME
    
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    
    conn = create_connection(db_path)
    
    try:
        logger.info("Cargando datos históricos de precios...")
        df_historical = get_historical_prices(conn)
        
        if df_historical.empty:
            raise ValueError("No se encontraron datos históricos de precios")
        
        logger.info(f"Datos cargados: {len(df_historical)} registros, {df_historical['barrio_id'].nunique()} barrios")
        
        # Filtrar barrios con suficientes datos
        barrios_with_data = df_historical.groupby('barrio_id').size()
        valid_barrios = barrios_with_data[barrios_with_data >= min_years].index.tolist()
        
        logger.info(f"Barrios con suficientes datos (≥{min_years} años): {len(valid_barrios)}")
        
        # Generar predicciones para cada barrio
        all_predictions = []
        successful = 0
        failed = 0
        
        for barrio_id in valid_barrios:
            result = forecast_barrio_prices(
                df_historical,
                barrio_id,
                forecast_years=forecast_years,
                optimize=True
            )
            
            if result:
                all_predictions.extend(result['predictions'])
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Predicciones generadas: {successful} exitosas, {failed} fallidas")
        
        if not all_predictions:
            raise ValueError("No se pudieron generar predicciones para ningún barrio")
        
        df_predictions = pd.DataFrame(all_predictions)
        
        # Calcular volatilidad
        logger.info("Calculando índice de volatilidad...")
        df_volatility = calculate_volatility_index(df_historical)
        
        return df_predictions, df_volatility
        
    finally:
        conn.close()


def main() -> int:
    """Función principal."""
    logger.info("=" * 60)
    logger.info("🔮 Generación de Predicciones de Precios 2026-2027")
    logger.info("=" * 60)
    
    # Verificar dependencias
    if not HAS_ARIMA:
        logger.error("statsmodels no está instalado. Instala con: pip install statsmodels")
        return 1
    
    # Generar predicciones
    try:
        df_predictions, df_volatility = generate_all_predictions(
            forecast_years=[2026, 2027],
            min_years=3
        )
        
        # Crear directorio de exports
        output_dir = PROJECT_ROOT / "notebooks" / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Exportar predicciones
        output_file = output_dir / "predicciones_precios_2026_2027.csv"
        df_predictions.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"\n✅ Predicciones exportadas: {output_file}")
        logger.info(f"   Registros: {len(df_predictions)}")
        logger.info(f"   Barrios: {df_predictions['barrio_id'].nunique()}")
        logger.info(f"   Años: {sorted(df_predictions['anio'].unique())}")
        
        # Exportar volatilidad
        volatility_file = output_dir / "indice_volatilidad_precios.csv"
        df_volatility.to_csv(volatility_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"\n✅ Índice de volatilidad exportado: {volatility_file}")
        logger.info(f"   Registros: {len(df_volatility)}")
        
        # Resumen estadístico
        logger.info("\n" + "=" * 60)
        logger.info("📊 RESUMEN ESTADÍSTICO")
        logger.info("=" * 60)
        logger.info(f"Predicciones 2026:")
        pred_2026 = df_predictions[df_predictions['anio'] == 2026]
        logger.info(f"   Precio medio predicho: {pred_2026['precio_predicho'].mean():.2f} €/m²")
        logger.info(f"   Rango: {pred_2026['precio_predicho'].min():.2f} - {pred_2026['precio_predicho'].max():.2f} €/m²")
        
        logger.info(f"\nPredicciones 2027:")
        pred_2027 = df_predictions[df_predictions['anio'] == 2027]
        logger.info(f"   Precio medio predicho: {pred_2027['precio_predicho'].mean():.2f} €/m²")
        logger.info(f"   Rango: {pred_2027['precio_predicho'].min():.2f} - {pred_2027['precio_predicho'].max():.2f} €/m²")
        
        logger.info(f"\nVolatilidad:")
        logger.info(f"   Barrio más volátil: {df_volatility.loc[df_volatility['volatilidad_rank'].idxmin(), 'barrio_nombre']}")
        logger.info(f"   Barrio más estable: {df_volatility.loc[df_volatility['volatilidad_rank'].idxmax(), 'barrio_nombre']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Generación de predicciones completada")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generando predicciones: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
