#!/bin/bash
# Script para ejecutar todas las actualizaciones de la tabla maestra
# Usa python3 (compatible con macOS)

set -e  # Salir si hay errores

echo "================================================================================"
echo "ACTUALIZACIÓN COMPLETA DE TABLA MAESTRA"
echo "================================================================================"
echo ""

# Verificar que python3 está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 no está instalado"
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"
echo ""

# 1. Crear tabla maestra base
echo "📊 Paso 1/3: Creando tabla maestra base..."
python3 scripts/create_master_table_for_looker.py
echo ""

# 2. Completar lagunas con interpolación
echo "📊 Paso 2/3: Completando lagunas de datos..."
python3 scripts/fill_data_gaps.py
echo ""

# 3. Actualizar tabla maestra con datos interpolados
echo "📊 Paso 3/3: Actualizando tabla maestra con datos interpolados..."
python3 scripts/update_master_table_with_interpolated.py
echo ""

echo "================================================================================"
echo "✅ ACTUALIZACIÓN COMPLETA"
echo "================================================================================"
echo ""
echo "📁 Archivos generados:"
echo "   • master_table_barcelona_housing.csv (original)"
echo "   • master_table_barcelona_housing_filled.csv (con datos interpolados) ✅"
echo "   • master_table_barcelona_housing_smoothed.csv (si se ejecuta add_smoothed_data_to_master.py)"
echo ""
