#!/bin/bash
# Script para cerrar Issue #199 en GitHub
# Requiere: gh CLI autenticado (gh auth login)

set -e

ISSUE_NUMBER=199
REPO="prototyp33/barcelona-housing-demographics-analyzer"

echo "=========================================="
echo "Cerrando Issue #$ISSUE_NUMBER"
echo "=========================================="

# Comentario de cierre
COMMENT="## ✅ Issue #199 Completado

### Resumen de Resultados

- **1,268 registros** extraídos (objetivo: ≥100) ✅
- **5 barrios de Gràcia** cubiertos (IDs: 28, 29, 30, 31, 32) ✅
- **Período completo 2020-2025** ✅
- **Validación DoD**: 9/11 criterios cumplidos (81.8%) ✅

### Archivos Generados

- \`spike-data-validation/data/raw/ine_precios_gracia_notebook.csv\` (1,268 registros)
- \`spike-data-validation/data/logs/extraction_summary_199.json\`
- \`spike-data-validation/data/logs/validation_report_199.md\`

### Estadísticas

- Rango de precios: 1,036.5 - 16,952.88 €/m²
- Precio medio: 4,035.10 €/m²
- 0% valores nulos en columnas críticas

### Decisión

✅ **GO para Issue #200** - Todos los criterios mínimos cumplidos

### Próximos Pasos

Issue #200 está listo para ejecutar. Solo requiere configurar \`CATASTRO_API_KEY\`:
\`\`\`bash
export CATASTRO_API_KEY='tu_api_key'
python3 spike-data-validation/scripts/extract_catastro_gracia.py
\`\`\`

Ver detalles completos en: \`spike-data-validation/docs/ISSUE_199_CLOSURE_SUMMARY.md\`"

# Añadir comentario
echo "Añadiendo comentario a Issue #$ISSUE_NUMBER..."
gh issue comment "$ISSUE_NUMBER" --body "$COMMENT" --repo "$REPO"

# Cerrar issue
echo "Cerrando Issue #$ISSUE_NUMBER..."
gh issue close "$ISSUE_NUMBER" --repo "$REPO" --comment "Completado según DoD. Dataset listo para Issue #200"

echo "✅ Issue #$ISSUE_NUMBER cerrada exitosamente"

