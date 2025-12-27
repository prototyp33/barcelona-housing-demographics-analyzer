import sqlite3
import pandas as pd
from typing import Dict, List

def run_audit():
    db_path = "data/processed/database.db"
    conn = sqlite3.connect(db_path)
    
    print("=== AUDIT DE DATOS: BARCELONA HOUSING DEMOGRAPHICS ===\n")
    
    # 1. Barrios
    barrios_count = pd.read_sql("SELECT COUNT(*) as count FROM dim_barrios", conn).iloc[0]['count']
    barrios_with_geo = pd.read_sql("SELECT COUNT(*) as count FROM dim_barrios WHERE geometry_json IS NOT NULL", conn).iloc[0]['count']
    print(f"--- ENTIDADES BASE ---")
    print(f"Barrios totales: {barrios_count}/73")
    print(f"Barrios con Geometría (Mapas): {barrios_with_geo}/73\n")
    
    # 2. Fact Tables Audit
    tables = [
        "fact_precios", "fact_oferta_idealista", "fact_demografia", 
        "fact_renta", "fact_comercio", "fact_servicios_salud",
        "fact_medio_ambiente", "fact_ruido", "fact_presion_turistica",
        "fact_vivienda_publica", "fact_educacion"
    ]
    
    audit_data = []
    
    for table in tables:
        try:
            # Check if table exists
            exists = pd.read_sql(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'", conn)
            if exists.empty:
                audit_data.append({"Tabla": table, "Estado": "❌ No existe", "Registros": 0, "Años": "-", "Cobertura": "0%"})
                continue
                
            # Count records
            count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
            
            if count == 0:
                audit_data.append({"Tabla": table, "Estado": "⚠️ Vacía", "Registros": 0, "Años": "-", "Cobertura": "0%"})
                continue
            
            # Get years
            year_col = "anio" if "anio" in pd.read_sql(f"PRAGMA table_info({table})", conn)['name'].values else "year"
            years = pd.read_sql(f"SELECT MIN({year_col}) as min_y, MAX({year_col}) as max_y FROM {table}", conn).iloc[0]
            
            # Coverage in latest year
            latest_year = years['max_y']
            coverage = pd.read_sql(f"SELECT COUNT(DISTINCT barrio_id) as count FROM {table} WHERE {year_col} = {latest_year}", conn).iloc[0]['count']
            coverage_pct = (coverage / 73) * 100
            
            audit_data.append({
                "Tabla": table,
                "Estado": "✅ OK" if coverage_pct > 90 else "🟠 Parcial",
                "Registros": count,
                "Años": f"{years['min_y']}-{years['max_y']}",
                "Cobertura": f"{coverage}/73 ({coverage_pct:.1f}%)"
            })
        except Exception as e:
            audit_data.append({"Tabla": table, "Estado": f"❌ Error: {str(e)[:20]}", "Registros": 0, "Años": "-", "Cobertura": "0%"})
            
    df_audit = pd.DataFrame(audit_data)
    print(df_audit.to_string(index=False))
    
    # 3. Campos Críticos Missing
    print("\n--- AUDIT DE CAMPOS CRÍTICOS (Último Año) ---")
    
    # Precios Alquiler Real
    rent_real = pd.read_sql("SELECT COUNT(*) as count FROM fact_precios WHERE precio_mes_alquiler > 0 AND anio = 2023", conn).iloc[0]['count']
    print(f"Precios Alquiler (Fuente Oficial 2023): {rent_real}/73 barrios")
    
    # Precios Alquiler Oferta
    try:
        rent_offer = pd.read_sql("SELECT COUNT(*) as count FROM fact_oferta_idealista WHERE operacion = 'rent' AND (anio = 2023 OR anio = 2024)", conn).iloc[0]['count']
        print(f"Precios Alquiler (Oferta/Idealista 2023-24): {rent_offer} registros totales")
    except:
        print("Precios Alquiler (Oferta/Idealista): Error al consultar (columnas operacion/anio)")
    
    # Servicios
    try:
        services = pd.read_sql("SELECT COUNT(*) as count FROM fact_comercio WHERE anio = 2025", conn).iloc[0]['count']
        print(f"Datos de Comercio/Servicios (2025): {services} registros")
    except:
        print("Datos de Comercio/Servicios: No encontrados para 2025")

    conn.close()

if __name__ == "__main__":
    run_audit()

