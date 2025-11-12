#!/usr/bin/env python3
"""
Script para validar la calidad de los datasets descargados del Portal de Dades.

Analiza todos los archivos CSV descargados y genera un reporte de calidad.
"""

import argparse
import chardet
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
import sys

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_extraction import DATA_RAW_DIR


def detect_encoding(filepath: Path) -> Tuple[str, float]:
    """Detecta el encoding de un archivo."""
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(10000)  # Leer primeros 10KB
            result = chardet.detect(raw_data)
            return result['encoding'], result['confidence']
    except Exception as e:
        return 'unknown', 0.0


def validate_csv_file(filepath: Path) -> Dict[str, Any]:
    """
    Valida un archivo CSV y retorna un diccionario con métricas de calidad.
    
    Returns:
        Dict con métricas de calidad del archivo
    """
    result = {
        "filepath": str(filepath),
        "filename": filepath.name,
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "metrics": {}
    }
    
    # 1. Verificar que el archivo existe y no está vacío
    if not filepath.exists():
        result["status"] = "error"
        result["errors"].append("Archivo no existe")
        return result
    
    file_size = filepath.stat().st_size
    if file_size == 0:
        result["status"] = "error"
        result["errors"].append("Archivo vacío")
        return result
    
    result["metrics"]["file_size_bytes"] = file_size
    
    # 2. Detectar encoding
    encoding, confidence = detect_encoding(filepath)
    result["metrics"]["encoding"] = encoding
    result["metrics"]["encoding_confidence"] = confidence
    
    if confidence < 0.7:
        result["warnings"].append(f"Baja confianza en detección de encoding ({confidence:.2%})")
    
    # 3. Intentar leer el CSV
    df = None
    encodings_to_try = [encoding, 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(filepath, encoding=enc, low_memory=False)
            result["metrics"]["encoding_used"] = enc
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            result["errors"].append(f"Error leyendo CSV con encoding {enc}: {str(e)}")
            continue
    
    if df is None:
        result["status"] = "error"
        result["errors"].append("No se pudo leer el archivo CSV con ningún encoding")
        return result
    
    # 4. Métricas básicas
    result["metrics"]["num_rows"] = len(df)
    result["metrics"]["num_columns"] = len(df.columns)
    result["metrics"]["column_names"] = list(df.columns)
    
    if result["metrics"]["num_rows"] == 0:
        result["status"] = "error"
        result["errors"].append("DataFrame vacío (0 filas)")
        return result
    
    if result["metrics"]["num_columns"] == 0:
        result["status"] = "error"
        result["errors"].append("DataFrame sin columnas")
        return result
    
    # 5. Análisis de valores nulos
    null_counts = df.isnull().sum()
    null_percentages = (null_counts / len(df) * 100).round(2)
    
    result["metrics"]["null_counts"] = null_counts.to_dict()
    result["metrics"]["null_percentages"] = null_percentages.to_dict()
    
    # Columnas con más del 50% de valores nulos
    high_null_cols = null_percentages[null_percentages > 50].index.tolist()
    if high_null_cols:
        result["warnings"].append(
            f"Columnas con >50% valores nulos: {', '.join(high_null_cols)}"
        )
    
    # 6. Detectar columnas duplicadas
    duplicate_cols = df.columns[df.columns.duplicated()].tolist()
    if duplicate_cols:
        result["warnings"].append(f"Columnas duplicadas: {', '.join(duplicate_cols)}")
    
    # 7.  filas duplicadas
    duplicate_rows = df.duplicated().sum()
    result["metrics"]["duplicate_rows"] = int(duplicate_rows)
    if duplicate_rows > 0:
        dup_percentage = (duplicate_rows / len(df) * 100)
        result["metrics"]["duplicate_rows_percentage"] = round(dup_percentage, 2)
        if dup_percentage > 10:
            result["warnings"].append(
                f"Alto porcentaje de filas duplicadas ({dup_percentage:.2f}%)"
            )
    
    # 8. Análisis de tipos de datos
    dtypes = df.dtypes.to_dict()
    result["metrics"]["dtypes"] = {str(k): str(v) for k, v in dtypes.items()}
    
    # 9. Detectar columnas con solo un valor único (posiblemente constantes)
    constant_cols = []
    for col in df.columns:
        unique_count = df[col].nunique()
        if unique_count == 1:
            constant_cols.append(col)
        result["metrics"][f"{col}_unique_values"] = int(unique_count)
    
    if constant_cols:
        result["warnings"].append(
            f"Columnas con un solo valor único (constantes): {', '.join(constant_cols)}"
        )
    
    # 10. Detectar columnas que parecen ser fechas
    date_columns = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['fecha', 'date', 'any', 'año', 'year', 'mes', 'month']):
            date_columns.append(col)
            # Intentar convertir a datetime
            try:
                pd.to_datetime(df[col], errors='coerce')
                result["metrics"][f"{col}_is_date"] = True
            except:
                result["metrics"][f"{col}_is_date"] = False
    
    # 11. Detectar columnas numéricas con valores fuera de rango esperado
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        col_mean = df[col].mean()
        col_std = df[col].std()
        
        result["metrics"][f"{col}_min"] = float(col_min) if pd.notna(col_min) else None
        result["metrics"][f"{col}_max"] = float(col_max) if pd.notna(col_max) else None
        result["metrics"][f"{col}_mean"] = float(col_mean) if pd.notna(col_mean) else None
        result["metrics"][f"{col}_std"] = float(col_std) if pd.notna(col_std) else None
        
        # Detectar valores negativos en columnas que no deberían tenerlos
        if 'preu' in col.lower() or 'precio' in col.lower() or 'import' in col.lower():
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                result["warnings"].append(
                    f"Columna {col} tiene {negative_count} valores negativos"
                )
    
    # 12. Determinar estado final
    if result["errors"]:
        result["status"] = "error"
    elif result["warnings"]:
        result["status"] = "warning"
    else:
        result["status"] = "ok"
    
    return result


def validate_all_datasets(data_dir: Path, output_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Valida todos los archivos CSV en el directorio especificado.
    
    Args:
        data_dir: Directorio donde están los archivos CSV
        output_file: Archivo donde guardar el reporte JSON (opcional)
    
    Returns:
        Dict con el resumen de validación
    """
    portaldades_dir = data_dir / "portaldades"
    
    if not portaldades_dir.exists():
        print(f"❌ Directorio no existe: {portaldades_dir}")
        return {}
    
    # Buscar todos los archivos CSV (excluyendo el de metadatos)
    csv_files = [
        f for f in portaldades_dir.glob("*.csv")
        if f.name != "indicadores_habitatge.csv"
    ]
    
    if not csv_files:
        print(f"⚠️  No se encontraron archivos CSV en {portaldades_dir}")
        return {}
    
    print(f"📊 Validando {len(csv_files)} archivos CSV...")
    print("=" * 80)
    
    results = []
    summary = {
        "total_files": len(csv_files),
        "status_ok": 0,
        "status_warning": 0,
        "status_error": 0,
        "total_rows": 0,
        "total_errors": 0,
        "total_warnings": 0,
        "validation_date": datetime.now().isoformat()
    }
    
    for i, csv_file in enumerate(csv_files, 1):
        print(f"\n[{i}/{len(csv_files)}] Validando: {csv_file.name[:60]}...")
        result = validate_csv_file(csv_file)
        results.append(result)
        
        # Actualizar resumen
        if result["status"] == "ok":
            summary["status_ok"] += 1
        elif result["status"] == "warning":
            summary["status_warning"] += 1
        elif result["status"] == "error":
            summary["status_error"] += 1
        
        summary["total_rows"] += result["metrics"].get("num_rows", 0)
        summary["total_errors"] += len(result["errors"])
        summary["total_warnings"] += len(result["warnings"])
        
        # Mostrar estado
        status_icon = {
            "ok": "✅",
            "warning": "⚠️",
            "error": "❌"
        }.get(result["status"], "❓")
        
        print(f"  {status_icon} Estado: {result['status'].upper()}")
        print(f"  📏 Filas: {result['metrics'].get('num_rows', 0):,}, "
              f"Columnas: {result['metrics'].get('num_columns', 0)}")
        
        if result["errors"]:
            print(f"  ❌ Errores ({len(result['errors'])}):")
            for error in result["errors"][:3]:  # Mostrar solo primeros 3
                print(f"     - {error}")
        
        if result["warnings"]:
            print(f"  ⚠️  Advertencias ({len(result['warnings'])}):")
            for warning in result["warnings"][:3]:  # Mostrar solo primeros 3
                print(f"     - {warning}")
    
    # Generar reporte completo
    report = {
        "summary": summary,
        "files": results
    }
    
    # Guardar reporte JSON si se especifica
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Reporte guardado en: {output_file}")
    
    # Mostrar resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 80)
    print(f"Total archivos: {summary['total_files']}")
    print(f"✅ OK: {summary['status_ok']}")
    print(f"⚠️  WARNING: {summary['status_warning']}")
    print(f"❌ ERROR: {summary['status_error']}")
    print(f"Total filas: {summary['total_rows']:,}")
    print(f"Total errores: {summary['total_errors']}")
    print(f"Total advertencias: {summary['total_warnings']}")
    
    # Archivos con problemas
    problem_files = [r for r in results if r["status"] != "ok"]
    if problem_files:
        print(f"\n⚠️  Archivos con problemas ({len(problem_files)}):")
        for r in problem_files[:10]:  # Mostrar solo primeros 10
            print(f"   - {r['filename']}: {r['status']}")
        if len(problem_files) > 10:
            print(f"   ... y {len(problem_files) - 10} más")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Valida la calidad de los datasets descargados del Portal de Dades"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_RAW_DIR,
        help="Directorio donde están los datos (default: data/raw)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Archivo donde guardar el reporte JSON (default: data/logs/validation_report.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar información detallada de cada archivo"
    )
    
    args = parser.parse_args()
    
    # Determinar archivo de salida
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = DATA_RAW_DIR.parent / "logs" / f"validation_report_{timestamp}.json"
    
    # Ejecutar validación
    report = validate_all_datasets(args.data_dir, args.output)
    
    # Código de salida basado en errores
    if report and report.get("summary", {}).get("status_error", 0) > 0:
        sys.exit(1)
    elif report and report.get("summary", {}).get("status_warning", 0) > 0:
        sys.exit(0)  # Warnings no son críticos
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

