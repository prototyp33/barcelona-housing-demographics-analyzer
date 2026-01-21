#!/usr/bin/env python3
"""
Identificación y Reemplazo de Datos Estimados

Identifica todos los registros que fueron rellenados con estimaciones
y proporciona guía para obtener datos reales.
"""

import sys
from pathlib import Path
import sqlite3
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager


def identify_estimated_data():
    """Identifica todos los datos estimados en la base de datos."""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    print("=" * 120)
    print("IDENTIFICACIÓN DE DATOS ESTIMADOS")
    print("=" * 120)
    print()
    
    # Tables that might have estimated data
    tables_to_check = [
        'fact_servicios_salud',
        'fact_comercio',
        'fact_medio_ambiente',
        'fact_presion_turistica'
    ]
    
    estimated_data = {}
    total_estimated = 0
    
    for table in tables_to_check:
        # Check if table has source or dataset_id columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        has_source = 'source' in columns
        has_dataset_id = 'dataset_id' in columns
        
        if not (has_source or has_dataset_id):
            continue
        
        # Build WHERE clause based on available columns
        where_conditions = []
        if has_source:
            where_conditions.append("source = 'coverage_fill_script'")
        if has_dataset_id:
            where_conditions.append("dataset_id = 'estimated'")
        
        where_clause = " OR ".join(where_conditions)
        
        # Check for estimated data
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM {table} 
            WHERE {where_clause}
        """)
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Get details
            select_cols = "barrio_id, anio"
            if has_source:
                select_cols += ", source"
            if has_dataset_id:
                select_cols += ", dataset_id"
            
            cursor.execute(f"""
                SELECT {select_cols}
                FROM {table}
                WHERE {where_clause}
                ORDER BY barrio_id, anio
            """)
            records = cursor.fetchall()
            
            # Get barrio names
            barrio_ids = list(set(r[0] for r in records))
            cursor.execute(f"""
                SELECT barrio_id, barrio_nombre, distrito_nombre
                FROM dim_barrios
                WHERE barrio_id IN ({','.join('?' * len(barrio_ids))})
            """, barrio_ids)
            barrios = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
            
            estimated_data[table] = {
                'count': count,
                'barrios': barrios,
                'records': records
            }
            total_estimated += count
    
    # Report
    print(f"📊 Total de registros estimados: {total_estimated}")
    print()
    
    if not estimated_data:
        print("✅ No hay datos estimados en la base de datos")
        conn.close()
        return
    
    # Detailed report
    for table, data in estimated_data.items():
        print("=" * 120)
        print(f"📋 {table.upper()}")
        print("=" * 120)
        print()
        print(f"Registros estimados: {data['count']}")
        print(f"Barrios afectados: {len(data['barrios'])}")
        print()
        
        print("Barrios:")
        for barrio_id, (barrio_nombre, distrito_nombre) in data['barrios'].items():
            # Count records for this barrio
            barrio_records = [r for r in data['records'] if r[0] == barrio_id]
            print(f"  • {barrio_nombre} ({distrito_nombre}): {len(barrio_records)} registros")
        print()
    
    conn.close()
    
    # Recommendations for getting real data
    print("=" * 120)
    print("💡 GUÍA PARA OBTENER DATOS REALES")
    print("=" * 120)
    print()
    
    recommendations = {
        'fact_servicios_salud': {
            'fuentes': [
                'Open Data BCN - Equipaments sanitaris',
                'CatSalut - Mapa de centres sanitaris',
                'Google Maps API - Búsqueda de farmacias/centros de salud'
            ],
            'url': 'https://opendata-ajuntament.barcelona.cat/data/es/dataset/equipaments-sanitaris',
            'metodo': 'Geocodificar direcciones y contar por barrio',
            'dificultad': 'Media',
            'tiempo_estimado': '2-3 días'
        },
        'fact_comercio': {
            'fuentes': [
                'Open Data BCN - Cens d\'activitats econòmiques',
                'Open Data BCN - Terrasses',
                'Registro Mercantil'
            ],
            'url': 'https://opendata-ajuntament.barcelona.cat/data/es/dataset/cens-activitats-comercials',
            'metodo': 'Descargar censo y agregar por barrio',
            'dificultad': 'Baja',
            'tiempo_estimado': '1 día'
        },
        'fact_medio_ambiente': {
            'fuentes': [
                'Open Data BCN - Zones verdes',
                'Open Data BCN - Arbrat',
                'Open Data BCN - Mapa de soroll'
            ],
            'url': 'https://opendata-ajuntament.barcelona.cat/data/es/dataset/zones-verdes',
            'metodo': 'Calcular áreas verdes y contar árboles por barrio',
            'dificultad': 'Media',
            'tiempo_estimado': '2 días'
        },
        'fact_presion_turistica': {
            'fuentes': [
                'Inside Airbnb - Barcelona',
                'Open Data BCN - Allotjaments turístics'
            ],
            'url': 'http://insideairbnb.com/get-the-data/',
            'metodo': 'Descargar listings y geocodificar por barrio',
            'dificultad': 'Baja',
            'tiempo_estimado': '1 día'
        }
    }
    
    for table, data in estimated_data.items():
        if table in recommendations:
            rec = recommendations[table]
            print(f"📋 {table.upper()}")
            print(f"   Dificultad: {rec['dificultad']}")
            print(f"   Tiempo estimado: {rec['tiempo_estimado']}")
            print()
            print(f"   Fuentes de datos:")
            for fuente in rec['fuentes']:
                print(f"      • {fuente}")
            print()
            print(f"   URL principal: {rec['url']}")
            print(f"   Método: {rec['metodo']}")
            print()
    
    # Generate action plan
    print("=" * 120)
    print("📝 PLAN DE ACCIÓN")
    print("=" * 120)
    print()
    
    print("FASE 1: Datos Fáciles (1-2 días)")
    print("  1. fact_comercio - Descargar censo de actividades económicas")
    print("  2. fact_presion_turistica - Descargar datos de Inside Airbnb")
    print()
    
    print("FASE 2: Datos Medios (3-5 días)")
    print("  3. fact_servicios_salud - Geocodificar equipamientos sanitarios")
    print("  4. fact_medio_ambiente - Calcular zonas verdes y árboles")
    print()
    
    print("FASE 3: Validación (1 día)")
    print("  5. Comparar datos reales vs estimados")
    print("  6. Actualizar registros en la base de datos")
    print("  7. Marcar source='real_data' y dataset_id con la fuente real")
    print()
    
    # Export estimated data for reference
    export_path = project_root / "data" / "processed" / "monitoring" / "estimated_data_report.json"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    
    export_data = {}
    for table, data in estimated_data.items():
        export_data[table] = {
            'count': data['count'],
            'barrios': {
                str(bid): {'nombre': bname, 'distrito': distrito}
                for bid, (bname, distrito) in data['barrios'].items()
            }
        }
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Reporte exportado a: {export_path}")
    print()
    
    print("=" * 120)
    print("✅ IDENTIFICACIÓN COMPLETADA")
    print("=" * 120)
    print()
    
    return estimated_data


if __name__ == "__main__":
    identify_estimated_data()
