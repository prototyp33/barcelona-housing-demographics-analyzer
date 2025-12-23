"""
Predicción de tendencias temporales usando modelos de series temporales.

Incluye:
- Modelo ARIMA para predicción de precios
- Modelo Prophet (Facebook) para predicción avanzada
- Predicción de tendencias demográficas
- Intervalos de confianza para predicciones
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import sqlite3

from ..database_setup import DEFAULT_DB_NAME

logger = logging.getLogger(__name__)

# Intentar importar librerías de forecasting (opcionales)
try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False
    logger.warning("statsmodels no disponible. ARIMA no funcionará.")

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    logger.warning("prophet no disponible. Prophet no funcionará.")


def _get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Obtiene conexión a la base de datos.
    
    Args:
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Conexión SQLite.
    """
    if db_path is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "data" / "processed" / DEFAULT_DB_NAME
    
    return sqlite3.connect(str(db_path))


def _get_historical_data(
    barrio_id: int,
    metric: str,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Obtiene datos históricos de una métrica para un barrio.
    
    Args:
        barrio_id: ID del barrio.
        metric: Nombre de la métrica.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        DataFrame con columnas 'anio' y 'value'.
    """
    conn = _get_db_connection(db_path)
    
    try:
        metric_mapping = {
            "precio_m2_venta": ("fact_precios", "precio_m2_venta"),
            "precio_mes_alquiler": ("fact_precios", "precio_mes_alquiler"),
            "poblacion_total": ("fact_demografia", "poblacion_total"),
            "renta_mediana": ("fact_renta", "renta_mediana"),
        }
        
        if metric not in metric_mapping:
            raise ValueError(f"Métrica '{metric}' no soportada para forecasting")
        
        table, column = metric_mapping[metric]
        
        query = f"""
            SELECT anio, AVG({column}) as value
            FROM {table}
            WHERE barrio_id = ? AND {column} IS NOT NULL
            GROUP BY anio
            ORDER BY anio
        """
        
        df = pd.read_sql_query(query, conn, params=[barrio_id])
        
        return df
    
    finally:
        conn.close()


def forecast_prices_arima(
    barrio_id: int,
    horizon_months: int = 12,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Predice precios futuros usando modelo ARIMA.
    
    Args:
        barrio_id: ID del barrio.
        horizon_months: Meses hacia el futuro a predecir.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con predicciones y métricas.
    """
    if not HAS_ARIMA:
        raise ImportError("statsmodels no está instalado. Instala con: pip install statsmodels")
    
    # Obtener datos históricos
    df = _get_historical_data(barrio_id, "precio_m2_venta", db_path)
    
    if len(df) < 3:
        raise ValueError(f"Se necesitan al menos 3 años de datos históricos. Disponibles: {len(df)}")
    
    # Preparar serie temporal
    df = df.sort_values("anio")
    values = df["value"].values
    
    # Ajustar modelo ARIMA (auto-selección de parámetros simples)
    # Usar orden (1,1,1) como default, se puede optimizar
    try:
        model = ARIMA(values, order=(1, 1, 1))
        fitted_model = model.fit()
        
        # Hacer predicción
        # Convertir meses a años (aproximado)
        horizon_years = max(1, horizon_months // 12)
        forecast = fitted_model.forecast(steps=horizon_years)
        conf_int = fitted_model.get_forecast(steps=horizon_years).conf_int()
        
        # Calcular años futuros
        last_year = df["anio"].max()
        future_years = list(range(last_year + 1, last_year + 1 + horizon_years))
        
        return {
            "barrio_id": barrio_id,
            "method": "ARIMA",
            "historical_years": df["anio"].tolist(),
            "historical_values": values.tolist(),
            "forecast_years": future_years,
            "forecast_values": forecast.tolist(),
            "confidence_intervals": {
                "lower": conf_int.iloc[:, 0].tolist(),
                "upper": conf_int.iloc[:, 1].tolist(),
            },
            "model_aic": float(fitted_model.aic),
        }
    
    except Exception as e:
        logger.error("Error en forecasting ARIMA: %s", e)
        raise


def forecast_prices_prophet(
    barrio_id: int,
    horizon_months: int = 12,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Predice precios futuros usando modelo Prophet (Facebook).
    
    Args:
        barrio_id: ID del barrio.
        horizon_months: Meses hacia el futuro a predecir.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con predicciones y métricas.
    """
    if not HAS_PROPHET:
        raise ImportError("prophet no está instalado. Instala con: pip install prophet")
    
    # Obtener datos históricos
    df = _get_historical_data(barrio_id, "precio_m2_venta", db_path)
    
    if len(df) < 3:
        raise ValueError(f"Se necesitan al menos 3 años de datos históricos. Disponibles: {len(df)}")
    
    # Preparar datos para Prophet (requiere columnas 'ds' y 'y')
    df_prophet = pd.DataFrame({
        "ds": pd.to_datetime(df["anio"].astype(str) + "-01-01"),
        "y": df["value"].values,
    })
    
    # Entrenar modelo Prophet
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    model.fit(df_prophet)
    
    # Crear dataframe futuro
    future = model.make_future_dataframe(periods=horizon_months, freq="M")
    forecast = model.predict(future)
    
    # Filtrar solo predicciones futuras
    last_historical_date = df_prophet["ds"].max()
    forecast_future = forecast[forecast["ds"] > last_historical_date].copy()
    
    return {
        "barrio_id": barrio_id,
        "method": "Prophet",
        "historical_years": df["anio"].tolist(),
        "historical_values": df["value"].tolist(),
        "forecast_dates": forecast_future["ds"].dt.to_pydatetime().tolist(),
        "forecast_values": forecast_future["yhat"].tolist(),
        "confidence_intervals": {
            "lower": forecast_future["yhat_lower"].tolist(),
            "upper": forecast_future["yhat_upper"].tolist(),
        },
    }


def forecast_prices(
    barrio_id: int,
    horizon_months: int = 12,
    method: str = "auto",
    db_path: Optional[Path] = None
) -> Dict:
    """
    Predice precios futuros usando el mejor método disponible.
    
    Args:
        barrio_id: ID del barrio.
        horizon_months: Meses hacia el futuro a predecir.
        method: Método a usar ('auto', 'arima', 'prophet').
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con predicciones y métricas.
    """
    if method == "auto":
        # Seleccionar mejor método disponible
        if HAS_PROPHET:
            method = "prophet"
        elif HAS_ARIMA:
            method = "arima"
        else:
            raise ImportError(
                "No hay librerías de forecasting disponibles. "
                "Instala statsmodels o prophet: pip install statsmodels prophet"
            )
    
    if method == "prophet":
        return forecast_prices_prophet(barrio_id, horizon_months, db_path)
    elif method == "arima":
        return forecast_prices_arima(barrio_id, horizon_months, db_path)
    else:
        raise ValueError(f"Método '{method}' no soportado. Usa 'arima' o 'prophet'")


def forecast_demographics(
    barrio_id: int,
    metric: str,
    horizon_years: int = 5,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Predice tendencias demográficas futuras.
    
    Args:
        barrio_id: ID del barrio.
        metric: Métrica demográfica ('poblacion_total', 'edad_media', etc.).
        horizon_years: Años hacia el futuro a predecir.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con predicciones.
    """
    if not HAS_ARIMA:
        raise ImportError("statsmodels no está instalado. Instala con: pip install statsmodels")
    
    # Obtener datos históricos
    df = _get_historical_data(barrio_id, metric, db_path)
    
    if len(df) < 3:
        raise ValueError(f"Se necesitan al menos 3 años de datos históricos. Disponibles: {len(df)}")
    
    # Preparar serie temporal
    df = df.sort_values("anio")
    values = df["value"].values
    
    # Ajustar modelo ARIMA
    try:
        model = ARIMA(values, order=(1, 1, 1))
        fitted_model = model.fit()
        
        # Hacer predicción
        forecast = fitted_model.forecast(steps=horizon_years)
        conf_int = fitted_model.get_forecast(steps=horizon_years).conf_int()
        
        # Calcular años futuros
        last_year = df["anio"].max()
        future_years = list(range(last_year + 1, last_year + 1 + horizon_years))
        
        return {
            "barrio_id": barrio_id,
            "metric": metric,
            "method": "ARIMA",
            "historical_years": df["anio"].tolist(),
            "historical_values": values.tolist(),
            "forecast_years": future_years,
            "forecast_values": forecast.tolist(),
            "confidence_intervals": {
                "lower": conf_int.iloc[:, 0].tolist(),
                "upper": conf_int.iloc[:, 1].tolist(),
            },
        }
    
    except Exception as e:
        logger.error("Error en forecasting demográfico: %s", e)
        raise

