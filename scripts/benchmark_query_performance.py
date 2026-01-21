#!/usr/bin/env python3
"""
Script de benchmark para medir el rendimiento de consultas antes y después
de aplicar las mejoras de la base de datos.

Compara:
- Consultas originales vs consultas optimizadas con vistas
- Consultas con índices nuevos vs sin índices
- Rendimiento de vistas recent vs consultas completas
"""

import sys
import time
import statistics
from pathlib import Path
from typing import Dict, List, Tuple

# Añadir proyecto al path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.database import DatabaseManager
from src.app.config import DB_PATH
from src.app.data_loader import (
    load_distritos,
    load_precios,
    load_kpis,
    load_critical_kpis,
)
from src.app.data_loader_optimized import (
    load_distritos_optimized,
    load_precios_recent_optimized,
    load_kpis_by_barrio_optimized,
    load_distrito_summary_optimized,
)

def benchmark_query(
    name: str,
    func,
    *args,
    iterations: int = 10,
    warmup: int = 2
) -> Dict[str, float]:
    """
    Ejecuta un benchmark de una función.
    
    Args:
        name: Nombre del benchmark.
        func: Función a ejecutar.
        *args: Argumentos para la función.
        iterations: Número de iteraciones.
        warmup: Número de iteraciones de calentamiento.
    
    Returns:
        Diccionario con estadísticas de tiempo.
    """
    print(f"\n🔍 Benchmarking: {name}")
    
    # Warmup
    for _ in range(warmup):
        try:
            func(*args)
        except Exception as e:
            print(f"  ⚠️  Error en warmup: {e}")
            return {"error": str(e)}
    
    # Ejecutar iteraciones
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        try:
            result = func(*args)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            if i == 0:
                result_size = len(result) if isinstance(result, (list, pd.DataFrame)) else 1
                print(f"  📊 Resultado: {result_size} registros")
        except Exception as e:
            print(f"  ❌ Error en iteración {i+1}: {e}")
            return {"error": str(e)}
    
    # Calcular estadísticas
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0
    
    print(f"  ⏱️  Tiempo promedio: {avg_time*1000:.2f}ms")
    print(f"  📈 Tiempo mediano: {median_time*1000:.2f}ms")
    print(f"  ⬇️  Mínimo: {min_time*1000:.2f}ms")
    print(f"  ⬆️  Máximo: {max_time*1000:.2f}ms")
    print(f"  📊 Desviación estándar: {std_dev*1000:.2f}ms")
    
    return {
        "avg_ms": avg_time * 1000,
        "median_ms": median_time * 1000,
        "min_ms": min_time * 1000,
        "max_ms": max_time * 1000,
        "std_dev_ms": std_dev * 1000,
        "iterations": iterations,
    }


def compare_queries(
    name: str,
    original_func,
    optimized_func,
    *args,
    iterations: int = 10
) -> Dict[str, any]:
    """
    Compara dos versiones de una función (original vs optimizada).
    
    Returns:
        Diccionario con comparación de rendimiento.
    """
    print(f"\n{'='*60}")
    print(f"📊 COMPARACIÓN: {name}")
    print(f"{'='*60}")
    
    original_stats = benchmark_query(f"{name} (Original)", original_func, *args, iterations=iterations)
    optimized_stats = benchmark_query(f"{name} (Optimizada)", optimized_func, *args, iterations=iterations)
    
    if "error" in original_stats or "error" in optimized_stats:
        return {"error": "Error en benchmark"}
    
    improvement = ((original_stats["avg_ms"] - optimized_stats["avg_ms"]) / original_stats["avg_ms"]) * 100
    
    print(f"\n📈 MEJORA:")
    print(f"  ⬇️  Reducción de tiempo: {improvement:.1f}%")
    print(f"  ⚡ Tiempo original: {original_stats['avg_ms']:.2f}ms")
    print(f"  ⚡ Tiempo optimizado: {optimized_stats['avg_ms']:.2f}ms")
    print(f"  💾 Ahorro: {original_stats['avg_ms'] - optimized_stats['avg_ms']:.2f}ms")
    
    return {
        "name": name,
        "original": original_stats,
        "optimized": optimized_stats,
        "improvement_pct": improvement,
        "time_saved_ms": original_stats["avg_ms"] - optimized_stats["avg_ms"],
    }


def main():
    """Función principal del benchmark."""
    print("="*60)
    print("🚀 BENCHMARK DE RENDIMIENTO - Base de Datos")
    print("="*60)
    print(f"📁 Base de datos: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ Base de datos no encontrada: {DB_PATH}")
        return 1
    
    # Obtener año más reciente para pruebas
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    try:
        max_year_df = pd.read_sql("SELECT MAX(anio) as max_year FROM fact_precios", conn)
        max_year = int(max_year_df["max_year"].iloc[0]) if not max_year_df.empty else 2023
        print(f"📅 Año más reciente en BD: {max_year}")
    finally:
        conn.close()
    
    results = []
    
    # 1. Benchmark: load_distritos
    try:
        result = compare_queries(
            "load_distritos",
            load_distritos,
            load_distritos_optimized,
            iterations=20
        )
        if "error" not in result:
            results.append(result)
    except Exception as e:
        print(f"❌ Error en benchmark load_distritos: {e}")
    
    # 2. Benchmark: load_precios (año reciente)
    try:
        result = compare_queries(
            f"load_precios (año {max_year})",
            lambda y, d: load_precios(y, d),
            load_precios_recent_optimized,
            max_year,
            None,
            iterations=10
        )
        if "error" not in result:
            results.append(result)
    except Exception as e:
        print(f"❌ Error en benchmark load_precios: {e}")
    
    # 3. Benchmark: load_kpis_by_barrio
    try:
        # Función original equivalente (construir manualmente)
        def load_kpis_original(year: int, barrio_id=None):
            from src.app.data_loader import get_connection
            import pandas as pd
            conn = get_connection()
            try:
                barrio_filter = " AND b.barrio_id = ?" if barrio_id else ""
                params = [year, year, year, year, year, year]
                if barrio_id:
                    params.append(barrio_id)
                
                query = f"""
                    SELECT 
                        b.barrio_id, b.barrio_nombre, b.distrito_nombre,
                        p.anio, p.precio_m2_venta, p.precio_mes_alquiler,
                        d.poblacion_total, d.hogares_totales, d.densidad_hab_km2,
                        r.renta_promedio, e.total_centros_educativos,
                        c.densidad_comercial_por_1000hab,
                        s.densidad_servicios_por_1000hab
                    FROM dim_barrios b
                    LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND p.anio = ?
                    LEFT JOIN fact_demografia d ON b.barrio_id = d.barrio_id AND d.anio = ?
                    LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND r.anio = ?
                    LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.anio = ?
                    LEFT JOIN fact_comercio c ON b.barrio_id = c.barrio_id AND c.anio = ?
                    LEFT JOIN fact_servicios_salud s ON b.barrio_id = s.barrio_id AND s.anio = ?
                    WHERE p.anio IS NOT NULL {barrio_filter}
                """
                return pd.read_sql(query, conn, params=params)
            finally:
                conn.close()
        
        result = compare_queries(
            f"load_kpis_by_barrio (año {max_year})",
            load_kpis_original,
            load_kpis_by_barrio_optimized,
            max_year,
            None,
            iterations=10
        )
        if "error" not in result:
            results.append(result)
    except Exception as e:
        print(f"❌ Error en benchmark load_kpis_by_barrio: {e}")
    
    # 4. Benchmark: load_distrito_summary (solo optimizada, no hay original)
    try:
        stats = benchmark_query(
            "load_distrito_summary (Optimizada)",
            load_distrito_summary_optimized,
            iterations=20
        )
        if "error" not in stats:
            results.append({
                "name": "load_distrito_summary",
                "optimized": stats,
                "improvement_pct": None,
            })
    except Exception as e:
        print(f"❌ Error en benchmark load_distrito_summary: {e}")
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE BENCHMARKS")
    print("="*60)
    
    if results:
        total_improvement = sum(r.get("improvement_pct", 0) for r in results if r.get("improvement_pct"))
        avg_improvement = total_improvement / len([r for r in results if r.get("improvement_pct")])
        
        print(f"\n✅ Benchmarks completados: {len(results)}")
        print(f"📈 Mejora promedio: {avg_improvement:.1f}%")
        
        print("\n📋 Detalles:")
        for result in results:
            if "improvement_pct" in result and result["improvement_pct"] is not None:
                print(f"  • {result['name']}: {result['improvement_pct']:.1f}% más rápido")
            elif "optimized" in result:
                print(f"  • {result['name']}: {result['optimized']['avg_ms']:.2f}ms (solo optimizada)")
    else:
        print("⚠️  No se completaron benchmarks exitosamente")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
