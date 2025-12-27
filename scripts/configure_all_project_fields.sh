#!/bin/bash
# Script para configurar TODOS los campos del GitHub Project Board
# Barcelona Housing Demographics Analyzer - Q1 2026 Data Expansion

set -e

REPO="prototyp33/barcelona-housing-demographics-analyzer"
PROJECT_NAME="SPIKE BCN Housing - product"

# Limpiar GITHUB_TOKEN inválido del entorno si existe
unset GITHUB_TOKEN

echo "🔧 Configurando TODOS los campos del Project Board..."
echo "📦 Repositorio: $REPO"
echo "📊 Project: $PROJECT_NAME"
echo ""

# Obtener Project ID
echo "🔍 Obteniendo Project ID..."
PROJECT_ID=$(gh project list --owner prototyp33 --format json | jq -r ".[] | select(.title==\"$PROJECT_NAME\") | .id" 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: No se encontró el project '$PROJECT_NAME'"
  echo "💡 Lista de projects disponibles:"
  gh project list --owner prototyp33
  exit 1
fi

echo "✅ Project ID: $PROJECT_ID"
echo ""

# Función para obtener field ID por nombre
get_field_id() {
  local field_name="$1"
  gh api graphql -f query="
    query {
      node(id: \"$PROJECT_ID\") {
        ... on ProjectV2 {
          field(name: \"$field_name\") {
            ... on ProjectV2Field {
              id
              name
            }
            ... on ProjectV2IterationField {
              id
              name
            }
            ... on ProjectV2SingleSelectField {
              id
              name
            }
            ... on ProjectV2DateField {
              id
              name
            }
            ... on ProjectV2NumberField {
              id
              name
            }
            ... on ProjectV2TextField {
              id
              name
            }
          }
        }
      }
    }
  " --jq '.data.node.field.id' 2>/dev/null || echo ""
}

# Función para obtener option ID de un single select field
get_option_id() {
  local field_name="$1"
  local option_name="$2"
  gh api graphql -f query="
    query {
      node(id: \"$PROJECT_ID\") {
        ... on ProjectV2 {
          field(name: \"$field_name\") {
            ... on ProjectV2SingleSelectField {
              options {
                id
                name
              }
            }
          }
        }
      }
    }
  " --jq ".data.node.field.options[] | select(.name==\"$option_name\") | .id" 2>/dev/null || echo ""
}

# Función para obtener item ID de una issue
get_item_id() {
  local issue_num="$1"
  gh api graphql -f query="
    query {
      repository(owner: \"prototyp33\", name: \"barcelona-housing-demographics-analyzer\") {
        issue(number: $issue_num) {
          id
          projectItems(first: 10) {
            nodes {
              id
              project {
                id
              }
            }
          }
        }
      }
    }
  " --jq ".data.repository.issue.projectItems.nodes[] | select(.project.id==\"$PROJECT_ID\") | .id" 2>/dev/null || echo ""
}

# Función para añadir issue al project si no está
add_issue_to_project() {
  local issue_num="$1"
  echo "  📌 Añadiendo Issue #$issue_num al project..."
  gh project item-add "$PROJECT_ID" --owner prototyp33 --url "https://github.com/$REPO/issues/$issue_num" 2>/dev/null || true
  sleep 1
}

# Función para actualizar campo Single Select
update_single_select() {
  local item_id="$1"
  local field_name="$2"
  local option_name="$3"
  
  FIELD_ID=$(get_field_id "$field_name")
  if [ -z "$FIELD_ID" ]; then
    echo "    ⚠️  Campo '$field_name' no encontrado"
    return 1
  fi
  
  OPTION_ID=$(get_option_id "$field_name" "$option_name")
  if [ -z "$OPTION_ID" ]; then
    echo "    ⚠️  Opción '$option_name' no encontrada en '$field_name'"
    return 1
  fi
  
  gh api graphql -f query="
    mutation {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: \"$PROJECT_ID\"
          itemId: \"$item_id\"
          fieldId: \"$FIELD_ID\"
          value: {
            singleSelectOptionId: \"$OPTION_ID\"
          }
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
  " 2>/dev/null && return 0 || return 1
}

# Función para actualizar campo Number
update_number() {
  local item_id="$1"
  local field_name="$2"
  local value="$3"
  
  FIELD_ID=$(get_field_id "$field_name")
  if [ -z "$FIELD_ID" ]; then
    echo "    ⚠️  Campo '$field_name' no encontrado"
    return 1
  fi
  
  gh api graphql -f query="
    mutation {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: \"$PROJECT_ID\"
          itemId: \"$item_id\"
          fieldId: \"$FIELD_ID\"
          value: {
            number: $value
          }
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
  " 2>/dev/null && return 0 || return 1
}

# Función para actualizar campo Date
update_date() {
  local item_id="$1"
  local field_name="$2"
  local date_value="$3"
  
  FIELD_ID=$(get_field_id "$field_name")
  if [ -z "$FIELD_ID" ]; then
    echo "    ⚠️  Campo '$field_name' no encontrado"
    return 1
  fi
  
  gh api graphql -f query="
    mutation {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: \"$PROJECT_ID\"
          itemId: \"$item_id\"
          fieldId: \"$FIELD_ID\"
          value: {
            date: \"$date_value\"
          }
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
  " 2>/dev/null && return 0 || return 1
}

# Función para actualizar campo Text
update_text() {
  local item_id="$1"
  local field_name="$2"
  local text_value="$3"
  
  FIELD_ID=$(get_field_id "$field_name")
  if [ -z "$FIELD_ID" ]; then
    echo "    ⚠️  Campo '$field_name' no encontrado"
    return 1
  fi
  
  gh api graphql -f query="
    mutation {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: \"$PROJECT_ID\"
          itemId: \"$item_id\"
          fieldId: \"$FIELD_ID\"
          value: {
            text: \"$text_value\"
          }
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
  " 2>/dev/null && return 0 || return 1
}

# Configuración de issues (Priority|Size|Estimate|Start Date|Target Date|Phase|Outcome|Epic|Release|Quarter|Effort)
declare -A ISSUE_CONFIG

# Sprint 1
ISSUE_CONFIG[245]="High|M|3|2026-01-07|2026-01-14|Development|73 barrios con datos educativos. Visualización: Mapa de calor educación vs precio m²|Data Expansion Q1 2026|v0.3.0-alpha.1|Q1 2026|1.0"
ISSUE_CONFIG[246]="High|L|5|2026-01-15|2026-01-24|Development|400+ estaciones Bicing + tiempo medio al centro. KPI: Identificar barrios con mejor accesibilidad|Data Expansion Q1 2026|v0.3.0-alpha.1|Q1 2026|1.5"
ISSUE_CONFIG[247]="Medium|M|3|2026-01-27|2026-02-07|Development|Renta media alquiler 2015-2025 por barrio (estimada). Métrica: Índice de Asequibilidad|Data Expansion Q1 2026|v0.3.0-alpha.2|Q1 2026|1.0"

# Sprint 2
ISSUE_CONFIG[248]="Medium|S|2|2026-02-03|2026-02-14|Development|m² zonas verdes por habitante por barrio. Análisis: Calidad de vida ambiental|Data Expansion Q1 2026|v0.3.0-alpha.2|Q1 2026|0.5"
ISSUE_CONFIG[249]="Medium|S|2|2026-02-03|2026-02-10|Development|≥100 centros salud + ≥200 farmacias mapeados. Métrica: Accesibilidad servicios sanitarios|Data Expansion Q1 2026|v0.3.0-alpha.2|Q1 2026|0.5"
ISSUE_CONFIG[250]="Medium|M|5|2026-02-03|2026-02-14|Development|Datos NO₂, PM10, PM2.5 por barrio. Cobertura ≥2020-2024|Data Expansion Q1 2026|v0.3.0-alpha.2|Q1 2026|1.0"

# Sprint 3
ISSUE_CONFIG[251]="Medium|M|2.5|2026-02-17|2026-02-21|Development|≥1000 locales comerciales + terrazas. Métrica: Dinamismo económico|Data Expansion Q1 2026|v0.3.0-beta.1|Q1 2026|0.5"
ISSUE_CONFIG[252]="Critical|L|5|2026-02-24|2026-03-07|Enhancement|Dashboard con 9 dimensiones integradas. Engagement: 80% usuarios exploran ≥3 visualizaciones|Data Expansion Q1 2026|v0.3.0-beta.1|Q1 2026|1.5"
ISSUE_CONFIG[253]="High|M|5|2026-02-24|2026-03-07|Development|ETL automatizado con GitHub Actions. Ejecución semanal sin intervención manual|Data Expansion Q1 2026|v0.3.0-beta.1|Q1 2026|1.0"

# Sprint 4
ISSUE_CONFIG[254]="Low|XL|8|2026-03-10|2026-03-24|Development|Evaluación de viabilidad Catastro. Si viable: datos detallados inmuebles|Data Expansion Q1 2026|v0.3.0|Q1 2026|2.0"
ISSUE_CONFIG[255]="High|M|3|2026-03-24|2026-03-31|Documentation|README actualizado + 9 guías de fuente. Onboarding: Nuevo dev puede extraer datos en <30 min|Data Expansion Q1 2026|v0.3.0|Q1 2026|1.0"

echo "📋 Añadiendo issues al project..."
for issue_num in 245 246 247 248 249 250 251 252 253 254 255; do
  add_issue_to_project "$issue_num"
done

echo ""
echo "⏳ Esperando 3 segundos para que GitHub procese..."
sleep 3
echo ""

echo "🔧 Configurando campos de cada issue..."
echo ""

for issue_num in 245 246 247 248 249 250 251 252 253 254 255; do
  config="${ISSUE_CONFIG[$issue_num]}"
  IFS='|' read -r priority size estimate start_date target_date phase outcome epic release quarter effort <<< "$config"
  
  echo "📝 Configurando Issue #$issue_num..."
  
  # Obtener Item ID
  ITEM_ID=$(get_item_id "$issue_num")
  if [ -z "$ITEM_ID" ]; then
    echo "  ⚠️  Issue #$issue_num no está en el project, saltando..."
    echo ""
    continue
  fi
  
  echo "  ✅ Item ID: $ITEM_ID"
  
  # Priority
  echo "  🔧 Priority: $priority"
  update_single_select "$ITEM_ID" "Priority" "$priority" && echo "    ✅ Priority actualizado" || echo "    ⚠️  Error Priority"
  
  # Size
  echo "  🔧 Size: $size"
  update_single_select "$ITEM_ID" "Size" "$size" && echo "    ✅ Size actualizado" || echo "    ⚠️  Error Size"
  
  # Estimate
  echo "  🔧 Estimate: $estimate"
  update_number "$ITEM_ID" "Estimate" "$estimate" && echo "    ✅ Estimate actualizado" || echo "    ⚠️  Error Estimate"
  
  # Start Date
  echo "  🔧 Start Date: $start_date"
  update_date "$ITEM_ID" "Start date" "$start_date" && echo "    ✅ Start Date actualizado" || echo "    ⚠️  Error Start Date"
  
  # Target Date
  echo "  🔧 Target Date: $target_date"
  update_date "$ITEM_ID" "Target date" "$target_date" && echo "    ✅ Target Date actualizado" || echo "    ⚠️  Error Target Date"
  
  # Phase
  echo "  🔧 Phase: $phase"
  update_single_select "$ITEM_ID" "Phase" "$phase" && echo "    ✅ Phase actualizado" || echo "    ⚠️  Error Phase"
  
  # Outcome
  echo "  🔧 Outcome: $outcome"
  update_text "$ITEM_ID" "Outcome" "$outcome" && echo "    ✅ Outcome actualizado" || echo "    ⚠️  Error Outcome"
  
  # Epic
  echo "  🔧 Epic: $epic"
  update_single_select "$ITEM_ID" "Epic" "$epic" && echo "    ✅ Epic actualizado" || echo "    ⚠️  Error Epic"
  
  # Release
  echo "  🔧 Release: $release"
  update_single_select "$ITEM_ID" "Release" "$release" && echo "    ✅ Release actualizado" || echo "    ⚠️  Error Release"
  
  # Quarter
  echo "  🔧 Quarter: $quarter"
  update_single_select "$ITEM_ID" "Quarter" "$quarter" && echo "    ✅ Quarter actualizado" || echo "    ⚠️  Error Quarter"
  
  # Effort (weeks)
  echo "  🔧 Effort (weeks): $effort"
  update_number "$ITEM_ID" "Effort (weeks)" "$effort" && echo "    ✅ Effort actualizado" || echo "    ⚠️  Error Effort"
  
  echo ""
done

echo "✅ Configuración completada"
echo ""
echo "💡 Verifica en GitHub:"
echo "   https://github.com/users/prototyp33/projects"

