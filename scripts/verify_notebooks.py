"""
Script para verificar que los notebooks se pueden ejecutar correctamente.

Este script:
1. Verifica que todas las dependencias están instaladas
2. Comprueba la conexión a la base de datos
3. Valida que los datos necesarios existen
4. Genera un reporte de compatibilidad

Autor: Barcelona Housing Demographics Analyzer
Fecha: 2026-01-06
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_dependencies():
    """Verifica que todas las dependencias están instaladas."""
    print("\n" + "=" * 80)
    print("1. VERIFICANDO DEPENDENCIAS")
    print("=" * 80)
    
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'scipy': 'scipy',
        'geopandas': 'geopandas',
        'folium': 'folium',
        'sklearn': 'scikit-learn'
    }
    
    missing = []
    installed = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            installed.append(package_name)
            print(f"✅ {package_name}")
        except ImportError:
            missing.append(package_name)
            print(f"❌ {package_name} - NO INSTALADO")
    
    print(f"\n📊 Resumen:")
    print(f"  • Instalados: {len(installed)}/{len(required_packages)}")
    print(f"  • Faltantes: {len(missing)}")
    
    if missing:
        print(f"\n⚠️  Para instalar los paquetes faltantes:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def check_database():
    """Verifica la conexión a la base de datos."""
    print("\n" + "=" * 80)
    print("2. VERIFICANDO BASE DE DATOS")
    print("=" * 80)
    
    try:
        from src.database import DatabaseManager
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        print("✅ Conexión establecida")
        
        # Verificar tablas clave
        cursor = conn.cursor()
        
        required_tables = [
            'dim_barrios',
            'fact_precios',
            'fact_demografia',
            'fact_desempleo',
            'fact_presion_turistica'
        ]
        
        missing_tables = []
        
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone()[0] == 0:
                missing_tables.append(table)
                print(f"❌ {table} - NO EXISTE")
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table} - {count:,} registros")
        
        conn.close()
        
        if missing_tables:
            print(f"\n❌ Faltan tablas: {', '.join(missing_tables)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_geometries():
    """Verifica que existen geometrías para análisis geoespacial."""
    print("\n" + "=" * 80)
    print("3. VERIFICANDO GEOMETRÍAS")
    print("=" * 80)
    
    try:
        from src.database import DatabaseManager
        import pandas as pd
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dim_barrios WHERE geometry_json IS NOT NULL")
        geom_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_barrios")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        pct = (geom_count / total_count * 100) if total_count > 0 else 0
        
        print(f"📍 Barrios con geometría: {geom_count}/{total_count} ({pct:.1f}%)")
        
        if geom_count == 0:
            print("⚠️  Sin geometrías - El notebook 02_geospatial_analysis.ipynb no funcionará")
            print("   Solución: Ejecutar script de carga de geometrías")
            return False
        elif pct < 90:
            print(f"⚠️  Cobertura baja ({pct:.1f}%) - Algunos análisis pueden ser incompletos")
            return True
        else:
            print("✅ Cobertura excelente")
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_data_quality():
    """Verifica la calidad de los datos."""
    print("\n" + "=" * 80)
    print("4. VERIFICANDO CALIDAD DE DATOS")
    print("=" * 80)
    
    try:
        from src.database import DatabaseManager
        import pandas as pd
        
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        # Verificar precios
        df_precios = pd.read_sql("SELECT COUNT(*) as count, MIN(anio) as min_year, MAX(anio) as max_year FROM fact_precios", conn)
        print(f"📊 Precios:")
        print(f"   Registros: {df_precios['count'].iloc[0]:,}")
        print(f"   Años: {df_precios['min_year'].iloc[0]} - {df_precios['max_year'].iloc[0]}")
        
        # Verificar desempleo
        df_desempleo = pd.read_sql("SELECT COUNT(*) as count FROM fact_desempleo", conn)
        print(f"📊 Desempleo:")
        print(f"   Registros: {df_desempleo['count'].iloc[0]:,}")
        
        # Verificar turismo
        df_turismo = pd.read_sql("SELECT COUNT(*) as count FROM fact_presion_turistica", conn)
        print(f"📊 Presión Turística:")
        print(f"   Registros: {df_turismo['count'].iloc[0]:,}")
        
        conn.close()
        
        # Validar que hay datos suficientes
        if df_precios['count'].iloc[0] < 100:
            print("❌ Datos de precios insuficientes")
            return False
        
        print("\n✅ Calidad de datos: Aceptable")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def generate_report():
    """Genera un reporte de compatibilidad."""
    print("\n" + "=" * 80)
    print("REPORTE DE COMPATIBILIDAD")
    print("=" * 80)
    
    checks = {
        'Dependencias': check_dependencies(),
        'Base de Datos': check_database(),
        'Geometrías': check_geometries(),
        'Calidad de Datos': check_data_quality()
    }
    
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    
    all_passed = all(checks.values())
    
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    print("\n" + "=" * 80)
    
    if all_passed:
        print("✅ TODOS LOS CHECKS PASARON")
        print("\n🎉 Los notebooks están listos para ejecutarse!")
        print("\nPara empezar:")
        print("  jupyter notebook notebooks/01_exploratory_data_analysis.ipynb")
    else:
        print("❌ ALGUNOS CHECKS FALLARON")
        print("\n⚠️  Revisa los errores arriba y corrige antes de ejecutar los notebooks")
    
    print("=" * 80)
    
    return all_passed


def main():
    """Función principal."""
    print("=" * 80)
    print("VERIFICACIÓN DE NOTEBOOKS")
    print("Barcelona Housing Demographics Analyzer")
    print("=" * 80)
    
    success = generate_report()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
