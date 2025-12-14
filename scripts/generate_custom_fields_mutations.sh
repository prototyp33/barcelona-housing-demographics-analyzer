#!/bin/bash
# Generate GraphQL Mutations for Custom Fields
# ⚠️ ADVERTENCIA: Requiere obtener IDs manualmente (complejo)
# Recomendación: Usar configuración manual en UI (más rápido)

set -e

echo "⚠️  GENERACIÓN DE GRAPHQL MUTATIONS PARA CUSTOM FIELDS"
echo "========================================================"
echo ""
echo "⚠️  ADVERTENCIA:"
echo "   - GitHub CLI no soporta custom fields completamente"
echo "   - Requiere GraphQL mutations manuales"
echo "   - Necesitas obtener projectId, itemId, fieldId para cada combinación"
echo "   - Cada custom field tiene tipo diferente (text, number, date, single_select)"
echo "   - Requiere ~84 mutations separadas (7 issues × 12 campos)"
echo ""
echo "⏱️  Tiempo estimado:"
echo "   - Configuración manual en UI: 15-20 minutos"
echo "   - Debug GraphQL mutations: 2+ horas"
echo ""
echo "✅ RECOMENDACIÓN: Usar configuración manual en UI"
echo "   Ver: docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md"
echo ""
read -p "¿Continuar generando mutations? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado. Usa configuración manual en UI."
    exit 0
fi

echo ""
echo "📋 Para generar mutations necesitas:"
echo ""
echo "1. Project ID:"
echo "   gh project view 1 --owner prototyp33 --format json | jq -r '.id'"
echo ""
echo "2. Item IDs (uno por issue en el proyecto):"
echo "   gh api graphql -f query='query { organization(login: \"prototyp33\") { projectV2(number: 1) { items(first: 20) { nodes { id content { ... on Issue { number title } } } } } } }'"
echo ""
echo "3. Field IDs (uno por custom field):"
echo "   gh api graphql -f query='query { organization(login: \"prototyp33\") { projectV2(number: 1) { fields(first: 20) { nodes { id name } } } } }'"
echo ""
echo "📝 Template de mutation:"
echo ""
cat << 'EOF'
mutation {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwDONXXXXXXXXXXXX"  # Reemplazar con Project ID
      itemId: "PVTI_lADONXXXXXXXXXXXX"     # Reemplazar con Item ID del issue
      fieldId: "PVTF_lADONXXXXXXXXXXXX"    # Reemplazar con Field ID del campo
      value: { 
        text: "Backlog"  # Para campos de texto
        # O number: 49 para Estimate
        # O date: "2026-01-06" para Start Date
        # O singleSelectOptionId: "..." para single select
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
EOF

echo ""
echo ""
echo "📄 Archivo de referencia creado: custom_fields_mutations_template.graphql"
echo ""
echo "⚠️  NOTA: Este proceso es complejo y propenso a errores."
echo "   Se recomienda usar la configuración manual en UI."
echo ""

# Crear template básico
cat > custom_fields_mutations_template.graphql << 'EOF'
# GraphQL Mutations Template para Custom Fields
# ⚠️ ADVERTENCIA: Requiere obtener IDs manualmente

# Paso 1: Obtener Project ID
# gh project view 1 --owner prototyp33 --format json | jq -r '.id'

# Paso 2: Obtener Item IDs (uno por issue)
# gh api graphql -f query='query { organization(login: "prototyp33") { projectV2(number: 1) { items(first: 20) { nodes { id content { ... on Issue { number title } } } } } } }'

# Paso 3: Obtener Field IDs (uno por custom field)
# gh api graphql -f query='query { organization(login: "prototyp33") { projectV2(number: 1) { fields(first: 20) { nodes { id name } } } } }'

# Ejemplo de mutation para Status field (text)
mutation UpdateStatusEpic187 {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwDONXXXXXXXXXXXX"  # Reemplazar
      itemId: "PVTI_lADONXXXXXXXXXXXX"     # Item ID de Epic #187
      fieldId: "PVTF_lADONXXXXXXXXXXXX"    # Field ID de "Status"
      value: { 
        text: "Backlog"
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}

# Ejemplo de mutation para Estimate field (number)
mutation UpdateEstimateEpic187 {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwDONXXXXXXXXXXXX"
      itemId: "PVTI_lADONXXXXXXXXXXXX"
      fieldId: "PVTF_lADONXXXXXXXXXXXX"    # Field ID de "Estimate"
      value: { 
        number: 49
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}

# Ejemplo de mutation para Start Date (date)
mutation UpdateStartDateEpic187 {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwDONXXXXXXXXXXXX"
      itemId: "PVTI_lADONXXXXXXXXXXXX"
      fieldId: "PVTF_lADONXXXXXXXXXXXX"    # Field ID de "Start Date"
      value: { 
        date: "2026-01-06"
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}

# Ejemplo de mutation para Epic field (single select)
mutation UpdateEpicFieldEpic187 {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwDONXXXXXXXXXXXX"
      itemId: "PVTI_lADONXXXXXXXXXXXX"
      fieldId: "PVTF_lADONXXXXXXXXXXXX"    # Field ID de "Epic"
      value: { 
        singleSelectOptionId: "PVTSS_lADONXXXXXXXXXXXX"  # Option ID de "DATA"
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}

# Repetir para cada issue (#187, #188, #189, #190, #191, #192, #193)
# Y para cada campo (Status, Priority, Size, Estimate, Epic, Release, Phase, Start Date, Target Date, Quarter, Effort, Outcome)
# Total: 7 issues × 12 campos = 84 mutations
EOF

echo "✅ Template creado: custom_fields_mutations_template.graphql"
echo ""
echo "📚 Referencias:"
echo "   - Quick Copy: docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md"
echo "   - Detallado: docs/FASE1_CUSTOM_FIELDS_REFERENCE.md"
echo "   - Pendientes: docs/FASE1_PENDING_CUSTOM_FIELDS.md"

