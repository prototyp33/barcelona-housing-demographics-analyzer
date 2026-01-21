#!/usr/bin/env python3
"""
Investigación de Tablas Vacías

Analiza las 6 tablas sin datos para entender:
1. Por qué están vacías
2. Qué fuentes de datos necesitan
3. Cómo obtener los datos
4. Prioridad de implementación
"""

import sys
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager


# Metadata de tablas vacías
EMPTY_TABLES_INFO = {
    'fact_calidad_aire': {
        'descripcion': 'Calidad del aire (NO2, PM2.5, PM10, O3)',
        'fuente_ideal': 'Xarxa de Vigilància i Previsió de la Contaminació Atmosfèrica (XVPCA)',
        'url': 'https://analisi.transparenciacatalunya.cat/',
        'granularidad': 'Estaciones de medición (no por barrio directamente)',
        'dificultad': 'Alta',
        'razon_vacia': 'Requiere geolocalización de estaciones y asignación a barrios',
        'prioridad': 'Media',
        'alternativas': [
            'API de Open Data BCN - Calidad del aire',
            'Datos de estaciones meteorológicas cercanas'
        ],
        'columnas_clave': ['no2_mean', 'pm25_mean', 'pm10_mean', 'o3_mean']
    },
    'fact_desempleo': {
        'descripcion': 'Datos de desempleo por barrio',
        'fuente_ideal': 'SEPE (Servicio Público de Empleo Estatal)',
        'url': 'https://opendata-ajuntament.barcelona.cat/data/es/dataset/atur',
        'granularidad': 'Barrio',
        'dificultad': 'Media',
        'razon_vacia': 'Dataset disponible pero no integrado en ETL',
        'prioridad': 'Alta',
        'alternativas': [
            'Open Data BCN - Atur registrat',
            'IDESCAT - Datos de empleo'
        ],
        'columnas_clave': ['num_desempleados', 'tasa_desempleo_estimada']
    },
    'fact_hut': {
        'descripcion': 'Licencias de Viviendas de Uso Turístico (VUT/HUT)',
        'fuente_ideal': 'Generalitat de Catalunya - Registro de Turismo',
        'url': 'https://analisi.transparenciacatalunya.cat/Turisme/Habitatges-d-s-tur-stic-a-Catalunya/hbde-mpe4',
        'granularidad': 'Dirección (requiere geocodificación)',
        'dificultad': 'Alta',
        'razon_vacia': 'Requiere geocodificación y agregación por barrio',
        'prioridad': 'Media',
        'alternativas': [
            'Scraping de registros públicos',
            'Datos de Inside Airbnb (proxy)'
        ],
        'columnas_clave': ['num_licencias_vut', 'densidad_vut_por_100_viviendas']
    },
    'fact_soroll': {
        'descripcion': 'Datos de ruido (DUPLICADO de fact_ruido)',
        'fuente_ideal': 'N/A - Tabla duplicada',
        'url': 'N/A',
        'granularidad': 'N/A',
        'dificultad': 'N/A',
        'razon_vacia': 'Tabla duplicada - fact_ruido ya tiene estos datos',
        'prioridad': 'Baja',
        'alternativas': [
            'Eliminar tabla (usar fact_ruido)',
            'Consolidar con fact_medio_ambiente'
        ],
        'columnas_clave': ['lden_mean', 'pct_exposed_65db']
    },
    'fact_turismo_intensidad': {
        'descripcion': 'Índice de intensidad turística',
        'fuente_ideal': 'Observatori del Turisme a Barcelona',
        'url': 'https://opendata-ajuntament.barcelona.cat/data/es/dataset/turisme',
        'granularidad': 'Distrito (no barrio)',
        'dificultad': 'Media',
        'razon_vacia': 'Datos disponibles solo a nivel distrito',
        'prioridad': 'Baja',
        'alternativas': [
            'Usar fact_presion_turistica como proxy',
            'Calcular índice derivado de Airbnb + hoteles'
        ],
        'columnas_clave': ['indice_intensidad_turistica', 'num_establecimientos_turisticos']
    },
    'fact_visados': {
        'descripcion': 'Visados de obra nueva (construcción)',
        'fuente_ideal': 'Col·legi d\'Arquitectes de Catalunya (COAC)',
        'url': 'https://www.arquitectes.cat/ca',
        'granularidad': 'Proyecto individual (requiere geocodificación)',
        'dificultad': 'Alta',
        'razon_vacia': 'Datos no públicos o requieren acceso especial',
        'prioridad': 'Baja',
        'alternativas': [
            'Ministerio de Fomento - Estadísticas de construcción',
            'Ajuntament de Barcelona - Licencias de obra'
        ],
        'columnas_clave': ['num_visados_obra_nueva', 'num_viviendas_proyectadas']
    }
}


def analyze_empty_tables():
    """Analiza las tablas vacías y genera reporte."""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    print("=" * 120)
    print("INVESTIGACIÓN DE TABLAS VACÍAS")
    print("=" * 120)
    print()
    
    # Verify which tables are actually empty
    empty_tables = []
    for table_name in EMPTY_TABLES_INFO.keys():
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        if count == 0:
            empty_tables.append(table_name)
    
    print(f"📊 Tablas vacías confirmadas: {len(empty_tables)}/6")
    print()
    
    # Detailed analysis
    for i, table_name in enumerate(empty_tables, 1):
        info = EMPTY_TABLES_INFO[table_name]
        
        print("=" * 120)
        print(f"{i}. {table_name.upper()}")
        print("=" * 120)
        print()
        
        print(f"📝 Descripción:")
        print(f"   {info['descripcion']}")
        print()
        
        print(f"🎯 Fuente de Datos Ideal:")
        print(f"   {info['fuente_ideal']}")
        print(f"   URL: {info['url']}")
        print()
        
        print(f"📏 Granularidad:")
        print(f"   {info['granularidad']}")
        print()
        
        print(f"⚠️  Razón por la que está vacía:")
        print(f"   {info['razon_vacia']}")
        print()
        
        print(f"🔧 Dificultad de Implementación:")
        print(f"   {info['dificultad']}")
        print()
        
        print(f"⭐ Prioridad:")
        print(f"   {info['prioridad']}")
        print()
        
        print(f"🔄 Alternativas:")
        for alt in info['alternativas']:
            print(f"   • {alt}")
        print()
        
        print(f"📊 Columnas Clave:")
        print(f"   {', '.join(info['columnas_clave'])}")
        print()
        
        # Check table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"📋 Esquema de Tabla ({len(columns)} columnas):")
        for col in columns[:5]:  # Show first 5 columns
            print(f"   • {col[1]} ({col[2]})")
        if len(columns) > 5:
            print(f"   ... y {len(columns) - 5} columnas más")
        print()
    
    conn.close()
    
    # Priority summary
    print("=" * 120)
    print("📈 RESUMEN DE PRIORIDADES")
    print("=" * 120)
    print()
    
    high_priority = [t for t, info in EMPTY_TABLES_INFO.items() if info['prioridad'] == 'Alta' and t in empty_tables]
    medium_priority = [t for t, info in EMPTY_TABLES_INFO.items() if info['prioridad'] == 'Media' and t in empty_tables]
    low_priority = [t for t, info in EMPTY_TABLES_INFO.items() if info['prioridad'] == 'Baja' and t in empty_tables]
    
    print(f"🔴 ALTA PRIORIDAD ({len(high_priority)}):")
    for table in high_priority:
        print(f"   • {table}: {EMPTY_TABLES_INFO[table]['descripcion']}")
    print()
    
    print(f"🟡 MEDIA PRIORIDAD ({len(medium_priority)}):")
    for table in medium_priority:
        print(f"   • {table}: {EMPTY_TABLES_INFO[table]['descripcion']}")
    print()
    
    print(f"🟢 BAJA PRIORIDAD ({len(low_priority)}):")
    for table in low_priority:
        print(f"   • {table}: {EMPTY_TABLES_INFO[table]['descripcion']}")
    print()
    
    # Recommendations
    print("=" * 120)
    print("💡 RECOMENDACIONES")
    print("=" * 120)
    print()
    
    print("1. ACCIÓN INMEDIATA:")
    print("   • fact_desempleo: Implementar extractor de Open Data BCN - Atur registrat")
    print("   • fact_soroll: ELIMINAR tabla (duplicado de fact_ruido)")
    print()
    
    print("2. CORTO PLAZO (1-2 semanas):")
    print("   • fact_calidad_aire: Implementar geolocalización de estaciones")
    print("   • fact_hut: Usar datos de Inside Airbnb como proxy inicial")
    print()
    
    print("3. MEDIO PLAZO (1 mes):")
    print("   • fact_turismo_intensidad: Calcular índice derivado")
    print()
    
    print("4. LARGO PLAZO (3+ meses):")
    print("   • fact_visados: Investigar acceso a datos del COAC")
    print()
    
    print("=" * 120)
    print("✅ INVESTIGACIÓN COMPLETADA")
    print("=" * 120)
    print()
    
    return {
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority
    }


if __name__ == "__main__":
    analyze_empty_tables()
