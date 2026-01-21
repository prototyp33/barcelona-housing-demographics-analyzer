#!/usr/bin/env python3
"""
Script de validación para verificar las mejoras aplicadas a data_loader.py

Ejecuta benchmarks y verificaciones para confirmar que las optimizaciones
están funcionando correctamente.

Uso:
    python3 scripts/validate_data_loader_improvements.py
"""

import sys
import time
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sqlite3
from src.app.data_loader import (
    get_connection,
    load_kpis,
    load_price_trends,
    load_available_years,
    table_exists,
)


def check_wal_mode():
    """Verifica que WAL mode esté activo."""
    print("\n🔍 Verificando WAL mode...")
    conn = get_connection()
    try:
        result = conn.execute("PRAGMA journal_mode;").fetchone()
        mode = result[0] if result else None
        if mode == 'wal':
            print("  ✅ WAL mode activo")
            return True
        else:
            print(f"  ❌ WAL mode NO activo. Modo actual: {mode}")
            return False
    finally:
        conn.close()


def check_pragma_settings():
    """Verifica que las configuraciones PRAGMA estén aplicadas."""
    print("\n🔍 Verificando configuraciones PRAGMA...")
    conn = get_connection()
    try:
        settings = {
            'busy_timeout': conn.execute("PRAGMA busy_timeout;").fetchone()[0],
            'wal_autocheckpoint': conn.execute("PRAGMA wal_autocheckpoint;").fetchone()[0],
            'cache_size': conn.execute("PRAGMA cache_size;").fetchone()[0],
            'temp_store': conn.execute("PRAGMA temp_store;").fetchone()[0],
        }
        
        all_ok = True
        if settings['busy_timeout'] == 5000:
            print("  ✅ busy_timeout: 5000ms")
        else:
            print(f"  ⚠️  busy_timeout: {settings['busy_timeout']}ms (esperado: 5000ms)")
            all_ok = False
            
        if settings['wal_autocheckpoint'] == 1000:
            print("  ✅ wal_autocheckpoint: 1000")
        else:
            print(f"  ⚠️  wal_autocheckpoint: {settings['wal_autocheckpoint']} (esperado: 1000)")
            all_ok = False
            
        if abs(settings['cache_size']) >= 64000:
            print(f"  ✅ cache_size: {abs(settings['cache_size'])}KB")
        else:
            print(f"  ⚠️  cache_size: {settings['cache_size']}KB (esperado: >=64000KB)")
            all_ok = False
            
        if settings['temp_store'] == 2:  # MEMORY = 2
            print("  ✅ temp_store: MEMORY")
        else:
            print(f"  ⚠️  temp_store: {settings['temp_store']} (esperado: 2=MEMORY)")
            all_ok = False
            
        return all_ok
    finally:
        conn.close()


def benchmark_load_kpis():
    """Benchmark de load_kpis()."""
    print("\n⏱️  Benchmark: load_kpis()")
    times = []
    for i in range(3):
        start = time.time()
        kpis = load_kpis()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        if i == 0:
            print(f"  Primera ejecución: {elapsed:.1f} ms")
    
    avg_time = sum(times) / len(times)
    print(f"  Promedio (3 ejecuciones): {avg_time:.1f} ms")
    
    if avg_time < 50:
        print("  ✅ Rendimiento excelente (< 50ms)")
        return True
    elif avg_time < 100:
        print("  ✅ Rendimiento bueno (< 100ms)")
        return True
    else:
        print("  ⚠️  Rendimiento podría mejorarse (> 100ms)")
        return False


def benchmark_load_price_trends():
    """Benchmark de load_price_trends()."""
    print("\n⏱️  Benchmark: load_price_trends()")
    times = []
    for i in range(3):
        start = time.time()
        trends = load_price_trends()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        if i == 0:
            print(f"  Primera ejecución: {elapsed:.1f} ms")
            print(f"  Registros cargados: {len(trends)}")
    
    avg_time = sum(times) / len(times)
    print(f"  Promedio (3 ejecuciones): {avg_time:.1f} ms")
    
    if avg_time < 100:
        print("  ✅ Rendimiento excelente (< 100ms)")
        return True
    elif avg_time < 200:
        print("  ✅ Rendimiento bueno (< 200ms)")
        return True
    else:
        print("  ⚠️  Rendimiento podría mejorarse (> 200ms)")
        return False


def benchmark_load_available_years():
    """Benchmark de load_available_years()."""
    print("\n⏱️  Benchmark: load_available_years()")
    times = []
    for i in range(3):
        start = time.time()
        years = load_available_years()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        if i == 0:
            print(f"  Primera ejecución: {elapsed:.1f} ms")
            print(f"  Tablas encontradas: {len(years)}")
    
    avg_time = sum(times) / len(times)
    print(f"  Promedio (3 ejecuciones): {avg_time:.1f} ms")
    
    if avg_time < 20:
        print("  ✅ Rendimiento excelente (< 20ms)")
        return True
    elif avg_time < 50:
        print("  ✅ Rendimiento bueno (< 50ms)")
        return True
    else:
        print("  ⚠️  Rendimiento podría mejorarse (> 50ms)")
        return False


def check_table_cache():
    """Verifica que el cache de table_exists() funciona."""
    print("\n🔍 Verificando cache de table_exists()...")
    
    # Primera llamada (sin cache)
    start = time.time()
    exists1 = table_exists("dim_barrios")
    time1 = (time.time() - start) * 1000
    
    # Segunda llamada (con cache)
    start = time.time()
    exists2 = table_exists("dim_barrios")
    time2 = (time.time() - start) * 1000
    
    if exists1 and exists2:
        print(f"  Primera llamada: {time1:.3f} ms (sin cache)")
        print(f"  Segunda llamada: {time2:.3f} ms (con cache)")
        
        if time2 < time1 * 0.1:  # Al menos 10x más rápido
            print("  ✅ Cache funcionando correctamente")
            return True
        else:
            print("  ⚠️  Cache podría no estar funcionando")
            return False
    else:
        print("  ❌ Error verificando existencia de tabla")
        return False


def check_recent_views():
    """Verifica que las vistas recent existen."""
    print("\n🔍 Verificando vistas optimizadas...")
    conn = get_connection()
    try:
        views_to_check = [
            "fact_precios_recent",
            "vw_kpis_por_barrio_anio",
            "vw_resumen_por_distrito",
        ]
        
        all_exist = True
        for view in views_to_check:
            exists = table_exists(view, conn)
            if exists:
                print(f"  ✅ {view} existe")
            else:
                print(f"  ⚠️  {view} no existe (opcional)")
                # No es crítico, solo informativo
        
        return True
    finally:
        conn.close()


def main():
    """Ejecuta todas las validaciones."""
    print("=" * 60)
    print("Validación de Mejoras en data_loader.py")
    print("=" * 60)
    
    results = {
        'WAL mode': check_wal_mode(),
        'PRAGMA settings': check_pragma_settings(),
        'load_kpis()': benchmark_load_kpis(),
        'load_price_trends()': benchmark_load_price_trends(),
        'load_available_years()': benchmark_load_available_years(),
        'Table cache': check_table_cache(),
        'Recent views': check_recent_views(),
    }
    
    print("\n" + "=" * 60)
    print("Resumen de Validación")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "⚠️  WARN"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} validaciones pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todas las validaciones pasaron!")
        return 0
    elif passed >= total * 0.7:
        print("\n✅ La mayoría de validaciones pasaron")
        return 0
    else:
        print("\n⚠️  Algunas validaciones fallaron. Revisar configuración.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
