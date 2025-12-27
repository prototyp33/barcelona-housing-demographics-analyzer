
#!/bin/bash
# Script para configurar campos del GitHub Project Board
# Barcelona Housing Demographics Analyzer - Q1 2026 Data Expansion

set -e

REPO="prototyp33/barcelona-housing-demographics-analyzer"
PROJECT_NAME="SPIKE BCN Housing - product"

# Limpiar GITHUB_TOKEN inválido del entorno si existe
unset GITHUB_TOKEN

echo "🔧 Configurando campos del Project Board..."
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
            }
            ... on ProjectV2IterationField {
              id
            }
            ... on ProjectV2SingleSelectField {
              id
            }
          }
        }
      }
    }
  " --jq '.data.node.field.id' 2>/dev/null || echo ""
}

# Función para obtener option ID de un single select field
get_option_id() {
  local field_id="$1"
  local option_name="$2"
  gh api graphql -f query="
    query {
      node(id: \"$PROJECT_ID\") {
        ... on ProjectV2 {
          field(name: \"Status\") {
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

# Función para actualizar campo Status
update_status() {
  local issue_num="$1"
  local status_value="$2"
  
  echo "  📝 Actualizando Status de Issue #$issue_num a '$status_value'..."
  
  ITEM_ID=$(get_item_id "$issue_num")
  if [ -z "$ITEM_ID" ]; then
    echo "    ⚠️  Issue #$issue_num no está en el project. Añadiendo..."
    gh project item-add "$PROJECT_ID" --owner prototyp33 --url "https://github.com/$REPO/issues/$issue_num" 2>/dev/null || true
    sleep 1
    ITEM_ID=$(get_item_id "$issue_num")
  fi
  
  if [ -z "$ITEM_ID" ]; then
    echo "    ❌ No se pudo obtener Item ID para Issue #$issue_num"
    return 1
  fi
  
  FIELD_ID=$(get_field_id "Status")
  if [ -z "$FIELD_ID" ]; then
    echo "    ⚠️  Campo 'Status' no encontrado"
    return 1
  fi
  
  OPTION_ID=$(gh api graphql -f query="
    query {
      node(id: \"$PROJECT_ID\") {
        ... on ProjectV2 {
          field(name: \"Status\") {
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
  " --jq ".data.node.field.options[] | select(.name==\"$status_value\") | .id" 2>/dev/null || echo "")
  
  if [ -z "$OPTION_ID" ]; then
    echo "    ⚠️  Opción '$status_value' no encontrada en Status"
    return 1
  fi
  
  gh api graphql -f query="
    mutation {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: \"$PROJECT_ID\"
          itemId: \"$ITEM_ID\"
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
  " 2>/dev/null && echo "    ✅ Status actualizado" || echo "    ⚠️  Error actualizando Status"
}

# Mapeo de issues a configuración
declare -A ISSUE_CONFIG

# Sprint 1
ISSUE_CONFIG[245]="Ready|High|M|3|2026-01-07|2026-01-14|Development|1.0|Q1 2026|v0.3.0-alpha.1"
ISSUE_CONFIG[246]="Ready|High|L|5|2026-01-15|2026-01-24|Development|1.5|Q1 2026|v0.3.0-alpha.1"
ISSUE_CONFIG[247]="Backlog|Medium|M|3|2026-01-27|2026-02-07|Development|1.0|Q1 2026|v0.3.0-alpha.2"

# Sprint 2
ISSUE_CONFIG[248]="Backlog|Medium|S|2|2026-02-03|2026-02-14|Development|0.5|Q1 2026|v0.3.0-alpha.2"
ISSUE_CONFIG[249]="Backlog|Medium|S|2|2026-02-03|2026-02-10|Development|0.5|Q1 2026|v0.3.0-alpha.2"
ISSUE_CONFIG[250]="Backlog|Medium|M|5|2026-02-03|2026-02-14|Development|1.0|Q1 2026|v0.3.0-alpha.2"

# Sprint 3
ISSUE_CONFIG[251]="Backlog|Medium|M|2.5|2026-02-17|2026-02-21|Development|0.5|Q1 2026|v0.3.0-beta.1"
ISSUE_CONFIG[252]="Backlog|Critical|L|5|2026-02-24|2026-03-07|Enhancement|1.5|Q1 2026|v0.3.0-beta.1"
ISSUE_CONFIG[253]="Backlog|High|M|5|2026-02-24|2026-03-07|Development|1.0|Q1 2026|v0.3.0-beta.1"

# Sprint 4
ISSUE_CONFIG[254]="Backlog|Low|XL|8|2026-03-10|2026-03-24|Development|2.0|Q1 2026|v0.3.0"
ISSUE_CONFIG[255]="Backlog|High|M|3|2026-03-24|2026-03-31|Documentation|1.0|Q1 2026|v0.3.0"

echo "📋 Configurando issues..."
echo ""

# Añadir todas las issues al project primero
for issue_num in 245 246 247 248 249 250 251 252 253 254 255; do
  echo "📌 Añadiendo Issue #$issue_num al project..."
  gh project item-add "$PROJECT_ID" --owner prototyp33 --url "https://github.com/$REPO/issues/$issue_num" 2>/dev/null || echo "  ⚠️  Issue #$issue_num ya está en el project o error"
done

echo ""
echo "⏳ Esperando 2 segundos para que GitHub procese..."
sleep 2
echo ""

# Configurar campos (solo Status por ahora, otros campos requieren más configuración)
for issue_num in 245 246 247 248 249 250 251 252 253 254 255; do
  config="${ISSUE_CONFIG[$issue_num]}"
  IFS='|' read -r status priority size estimate start_date target_date phase effort quarter release <<< "$config"
  
  echo "🔧 Configurando Issue #$issue_num..."
  echo "   Status: $status | Priority: $priority | Size: $size | Estimate: $estimate días"
  
  # Actualizar Status
  update_status "$issue_num" "$status"
  
  echo ""
done

echo "✅ Configuración completada"
echo ""
echo "💡 Nota: Algunos campos pueden requerir configuración manual en GitHub"
echo "   debido a limitaciones de la API. Verifica en:"
echo "   https://github.com/users/prototyp33/projects"

