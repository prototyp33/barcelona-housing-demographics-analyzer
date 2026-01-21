#!/bin/bash
# Script para verificar encabezados de CSV antes de subir a Looker Studio

echo "=========================================="
echo "Verificación de Encabezados CSV"
echo "=========================================="
echo ""

EXPORT_DIR="data/exports/looker_studio"

if [ ! -d "$EXPORT_DIR" ]; then
    echo "❌ Directorio no encontrado: $EXPORT_DIR"
    echo "Ejecuta primero: python scripts/export_data_for_looker_studio.py"
    exit 1
fi

echo "Verificando archivos principales..."
echo ""

# dim_barrios
echo "📁 dim_barrios.csv:"
if [ -f "$EXPORT_DIR/01_dimensions/dim_barrios.csv" ]; then
    HEADER=$(head -1 "$EXPORT_DIR/01_dimensions/dim_barrios.csv")
    EXPECTED="barrio_id,barrio_nombre"
    if echo "$HEADER" | grep -q "barrio_id"; then
        echo "  ✅ Encabezados correctos"
        echo "  Primeros campos: $(echo $HEADER | cut -d',' -f1-5)"
    else
        echo "  ❌ Encabezados incorrectos"
        echo "  Encontrado: $HEADER"
    fi
else
    echo "  ❌ Archivo no encontrado"
fi

echo ""

# dim_tiempo
echo "📁 dim_tiempo.csv:"
if [ -f "$EXPORT_DIR/01_dimensions/dim_tiempo.csv" ]; then
    HEADER=$(head -1 "$EXPORT_DIR/01_dimensions/dim_tiempo.csv")
    EXPECTED="time_id,anio"
    if echo "$HEADER" | grep -q "time_id"; then
        echo "  ✅ Encabezados correctos"
        echo "  Primeros campos: $(echo $HEADER | cut -d',' -f1-5)"
    else
        echo "  ❌ Encabezados incorrectos"
        echo "  Encontrado: $HEADER"
    fi
else
    echo "  ❌ Archivo no encontrado"
fi

echo ""

# fact_precios
echo "📁 fact_precios.csv:"
if [ -f "$EXPORT_DIR/02_market/fact_precios.csv" ]; then
    HEADER=$(head -1 "$EXPORT_DIR/02_market/fact_precios.csv")
    if echo "$HEADER" | grep -q "barrio_id.*precio_m2_venta"; then
        echo "  ✅ Encabezados correctos"
        echo "  Primeros campos: $(echo $HEADER | cut -d',' -f1-5)"
    else
        echo "  ⚠️  Verificar encabezados"
        echo "  Encontrado: $(echo $HEADER | cut -d',' -f1-5)"
    fi
else
    echo "  ❌ Archivo no encontrado"
fi

echo ""
echo "=========================================="
echo "Resumen"
echo "=========================================="
echo ""
echo "Si Looker Studio detecta encabezados incorrectos:"
echo "  1. Verifica que subiste el archivo correcto"
echo "  2. Re-descarga desde: $EXPORT_DIR"
echo "  3. Verifica encabezados con: head -1 archivo.csv"
echo ""
