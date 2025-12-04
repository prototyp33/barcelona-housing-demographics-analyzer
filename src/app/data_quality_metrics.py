"""
Módulo para calcular métricas de calidad de datos.

Proporciona funciones para calcular completeness, validity, consistency y timeliness
de los datos en la base de datos.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from src.app.config import DB_PATH
from src.app.data_loader import get_connection
from src.database_setup import validate_table_name


@st.cache_data(ttl=300)  # Cache por 5 minutos (métricas pueden cambiar)
def calculate_completeness() -> float:
    """
    Calcula el porcentaje de completitud de datos.
    
    Mide el porcentaje de campos no nulos en las tablas principales.
    
    Returns:
        Porcentaje de completitud (0-100).
    """
    conn = get_connection()
    try:
        # Calcular completitud por tabla
        tables = ["fact_precios", "fact_demografia", "fact_renta"]
        total_rows = 0
        non_null_rows = 0
        
        for table in tables:
            validated_table = validate_table_name(table)
            
            # Contar total de filas
            total_df = pd.read_sql(f"SELECT COUNT(*) as total FROM {validated_table}", conn)
            total = total_df["total"].iloc[0]
            
            # Contar filas sin campos críticos nulos
            if table == "fact_precios":
                # Campos críticos: barrio_id, anio, precio_m2
                query = f"""
                    SELECT COUNT(*) as non_null 
                    FROM {validated_table}
                    WHERE barrio_id IS NOT NULL 
                      AND anio IS NOT NULL 
                      AND precio_m2 IS NOT NULL
                """
            elif table == "fact_demografia":
                # Campos críticos: barrio_id, anio, poblacion
                query = f"""
                    SELECT COUNT(*) as non_null 
                    FROM {validated_table}
                    WHERE barrio_id IS NOT NULL 
                      AND anio IS NOT NULL 
                      AND poblacion IS NOT NULL
                """
            else:  # fact_renta
                # Campos críticos: barrio_id, anio, renta_euros
                query = f"""
                    SELECT COUNT(*) as non_null 
                    FROM {validated_table}
                    WHERE barrio_id IS NOT NULL 
                      AND anio IS NOT NULL 
                      AND renta_euros IS NOT NULL
                """
            
            non_null_df = pd.read_sql(query, conn)
            non_null = non_null_df["non_null"].iloc[0]
            
            total_rows += total
            non_null_rows += non_null
        
        if total_rows == 0:
            return 0.0
        
        completeness = (non_null_rows / total_rows) * 100
        return round(completeness, 2)
    finally:
        conn.close()


@st.cache_data(ttl=300)
def calculate_validity() -> float:
    """
    Calcula el porcentaje de validez de datos.
    
    Mide el porcentaje de datos dentro de rangos esperados.
    
    Returns:
        Porcentaje de validez (0-100).
    """
    conn = get_connection()
    try:
        total_rows = 0
        valid_rows = 0
        
        # Validar fact_precios: precio_m2 debe ser positivo y razonable (< 20,000 €/m²)
        validated_table = validate_table_name("fact_precios")
        total_df = pd.read_sql(
            f"SELECT COUNT(*) as total FROM {validated_table} WHERE precio_m2 IS NOT NULL",
            conn
        )
        total_precios = total_df["total"].iloc[0]
        
        valid_df = pd.read_sql(
            f"""
            SELECT COUNT(*) as valid 
            FROM {validated_table}
            WHERE precio_m2 > 0 AND precio_m2 < 20000
              AND anio >= 2015 AND anio <= 2025
            """,
            conn
        )
        valid_precios = valid_df["valid"].iloc[0]
        
        # Validar fact_demografia: poblacion debe ser positiva y razonable (< 200,000 por barrio)
        validated_table = validate_table_name("fact_demografia")
        total_df = pd.read_sql(
            f"SELECT COUNT(*) as total FROM {validated_table} WHERE poblacion IS NOT NULL",
            conn
        )
        total_demo = total_df["total"].iloc[0]
        
        valid_df = pd.read_sql(
            f"""
            SELECT COUNT(*) as valid 
            FROM {validated_table}
            WHERE poblacion > 0 AND poblacion < 200000
              AND anio >= 2015 AND anio <= 2025
            """,
            conn
        )
        valid_demo = valid_df["valid"].iloc[0]
        
        total_rows = total_precios + total_demo
        valid_rows = valid_precios + valid_demo
        
        if total_rows == 0:
            return 0.0
        
        validity = (valid_rows / total_rows) * 100
        return round(validity, 2)
    finally:
        conn.close()


@st.cache_data(ttl=300)
def calculate_consistency() -> float:
    """
    Calcula el porcentaje de consistencia entre fuentes.
    
    Mide la coherencia de datos entre diferentes tablas (ej: mismo barrio_id existe en todas).
    
    Returns:
        Porcentaje de consistencia (0-100).
    """
    conn = get_connection()
    try:
        # Obtener barrios únicos de cada tabla
        tables = ["fact_precios", "fact_demografia", "fact_renta"]
        barrio_sets = []
        
        for table in tables:
            validated_table = validate_table_name(table)
            df = pd.read_sql(
                f"SELECT DISTINCT barrio_id FROM {validated_table} WHERE barrio_id IS NOT NULL",
                conn
            )
            barrio_sets.append(set(df["barrio_id"].unique()))
        
        # Calcular intersección (barrios presentes en todas las tablas)
        if not barrio_sets:
            return 0.0
        
        common_barrios = set.intersection(*barrio_sets)
        
        # Obtener total de barrios únicos en todas las tablas
        all_barrios = set.union(*barrio_sets)
        
        if len(all_barrios) == 0:
            return 0.0
        
        consistency = (len(common_barrios) / len(all_barrios)) * 100
        return round(consistency, 2)
    finally:
        conn.close()


@st.cache_data(ttl=300)
def calculate_timeliness() -> int:
    """
    Calcula la antigüedad del dato más reciente en días.
    
    Returns:
        Número de días desde el dato más reciente.
    """
    conn = get_connection()
    try:
        max_dates = []
        
        # Obtener fecha máxima de cada tabla
        tables = ["fact_precios", "fact_demografia", "fact_renta"]
        for table in tables:
            validated_table = validate_table_name(table)
            # Asumimos que anio es el año del dato
            df = pd.read_sql(
                f"SELECT MAX(anio) as max_year FROM {validated_table}",
                conn
            )
            max_year = df["max_year"].iloc[0]
            if pd.notna(max_year):
                # Asumir que el dato es del 31 de diciembre de ese año
                max_date = datetime(int(max_year), 12, 31)
                max_dates.append(max_date)
        
        if not max_dates:
            return 999  # Muy antiguo si no hay datos
        
        # Obtener la fecha más reciente
        latest_date = max(max_dates)
        
        # Calcular días desde hoy
        days_ago = (datetime.now() - latest_date).days
        return max(0, days_ago)  # No negativo
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_quality_history() -> pd.DataFrame:
    """
    Obtiene historial de métricas de calidad.
    
    Por ahora retorna datos sintéticos, pero puede extenderse para
    guardar métricas históricas en una tabla.
    
    Returns:
        DataFrame con fecha, completeness, validity, consistency.
    """
    # Por ahora, retornar datos sintéticos basados en métricas actuales
    # En el futuro, esto puede leer de una tabla etl_quality_metrics
    completeness = calculate_completeness()
    validity = calculate_validity()
    consistency = calculate_consistency()
    
    # Generar últimos 24 meses con variación pequeña
    dates = pd.date_range(end=datetime.now(), periods=24, freq='M')
    
    # Simular evolución histórica (variación pequeña alrededor del valor actual)
    import numpy as np
    np.random.seed(42)  # Para reproducibilidad
    
    completeness_history = completeness - np.random.uniform(0, 4, 24)
    validity_history = validity - np.random.uniform(0, 2, 24)
    consistency_history = consistency - np.random.uniform(0, 5, 24)
    
    df = pd.DataFrame({
        'fecha': dates,
        'completeness': np.clip(completeness_history, 85, 100),
        'validity': np.clip(validity_history, 90, 100),
        'consistency': np.clip(consistency_history, 85, 100),
    })
    
    return df


@st.cache_data(ttl=300)
def detect_quality_issues() -> pd.DataFrame:
    """
    Detecta issues de calidad en los datos.
    
    Returns:
        DataFrame con barrio, issue, severidad, fecha detectado.
    """
    conn = get_connection()
    try:
        issues = []
        
        # Issue 1: Barrios con precios faltantes
        validated_table = validate_table_name("fact_precios")
        missing_precios = pd.read_sql(
            f"""
            SELECT DISTINCT b.barrio_nombre
            FROM dim_barrios b
            LEFT JOIN {validated_table} p ON b.barrio_id = p.barrio_id
            WHERE p.barrio_id IS NULL
            LIMIT 5
            """,
            conn
        )
        
        for _, row in missing_precios.iterrows():
            issues.append({
                'Barrio': row['barrio_nombre'],
                'Issue': 'Missing precio_m2',
                'Severidad': 'High',
                'Detectado': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Issue 2: Duplicados en fact_precios
        duplicates = pd.read_sql(
            f"""
            SELECT b.barrio_nombre, COUNT(*) as count
            FROM {validated_table} p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            GROUP BY p.barrio_id, p.anio, p.trimestre
            HAVING COUNT(*) > 1
            LIMIT 3
            """,
            conn
        )
        
        for _, row in duplicates.iterrows():
            issues.append({
                'Barrio': row['barrio_nombre'],
                'Issue': f'Duplicate entry ({row["count"]} rows)',
                'Severidad': 'Medium',
                'Detectado': datetime.now().strftime('%Y-%m-%d')
            })
        
        # Issue 3: Outliers en precios
        outliers = pd.read_sql(
            f"""
            SELECT b.barrio_nombre, p.precio_m2
            FROM {validated_table} p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.precio_m2 > 15000 OR p.precio_m2 < 1000
            LIMIT 3
            """,
            conn
        )
        
        for _, row in outliers.iterrows():
            issues.append({
                'Barrio': row['barrio_nombre'],
                'Issue': f'Outlier precio_m2: €{row["precio_m2"]:,.0f}/m²',
                'Severidad': 'Low',
                'Detectado': datetime.now().strftime('%Y-%m-%d')
            })
        
        if not issues:
            # Si no hay issues, retornar DataFrame vacío con columnas correctas
            return pd.DataFrame(columns=['Barrio', 'Issue', 'Severidad', 'Detectado'])
        
        return pd.DataFrame(issues)
    finally:
        conn.close()

