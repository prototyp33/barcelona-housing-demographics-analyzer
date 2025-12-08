#!/usr/bin/env python3
"""
Automatización de GitHub Projects v2 para Barcelona Housing Analyzer
Sincroniza issues con el tablero del proyecto y actualiza campos personalizados

Uso:
    python .github/scripts/project_automation.py --issue 24 --impact High --fuente IDESCAT --sprint "Sprint 1"
    python .github/scripts/project_automation.py --issue 24 --auto-detect
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Añadir el directorio raíz al path para imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.github_graphql import GitHubGraphQL

# Configuración
ORG_NAME = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
PROJECT_NUMBER = 1  # Ajustar según tu proyecto

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_project_info(gh: GitHubGraphQL) -> Dict:
    """
    Obtiene ID del proyecto y campos personalizados.
    
    Returns:
        Dict con project_id, title y fields mapeados
    """
    project = gh.get_project_v2(
        owner=ORG_NAME,
        repo=REPO_NAME,
        project_number=PROJECT_NUMBER
    )
    
    if not project:
        raise ValueError(f"Proyecto #{PROJECT_NUMBER} no encontrado")
    
    # Mapear campos para fácil acceso
    fields = {}
    for field in project.get("fields", {}).get("nodes", []):
        field_name = field.get("name")
        if not field_name:
            continue
            
        field_data = {
            "id": field.get("id"),
            "dataType": field.get("dataType"),
        }
        
        # Para campos single select, mapear opciones
        if field.get("dataType") == "SINGLE_SELECT" and "options" in field:
            field_data["options"] = {
                opt["name"]: opt["id"] 
                for opt in field.get("options", [])
            }
        
        fields[field_name] = field_data
    
    return {
        "project_id": project["id"],
        "title": project.get("title", "Unknown"),
        "fields": fields
    }


def add_issue_to_project(gh: GitHubGraphQL, project_id: str, issue_id: str) -> str:
    """
    Añade un issue al proyecto y retorna el item_id.
    
    Args:
        gh: Cliente GraphQL
        project_id: ID del proyecto
        issue_id: Node ID del issue
    
    Returns:
        item_id del item creado en el proyecto
    """
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {
        projectId: $projectId
        contentId: $contentId
      }) {
        item {
          id
        }
      }
    }
    """
    
    result = gh.execute_query(mutation, {
        "projectId": project_id,
        "contentId": issue_id
    })
    
    if "errors" in result:
        # Si el issue ya está en el proyecto, obtener su item_id
        logger.warning("Issue ya está en el proyecto, obteniendo item_id existente...")
        items_data = gh.get_project_items(project_id=project_id, limit=100)
        for item in items_data.get("items", []):
            content = item.get("content", {})
            if content:
                # Obtener el node ID del issue desde el content
                issue_node_id = get_issue_node_id(gh, content.get("number", 0))
                if issue_node_id == issue_id:
                    return item["id"]
        raise ValueError("No se pudo añadir ni encontrar el issue en el proyecto")
    
    return result["data"]["addProjectV2ItemById"]["item"]["id"]


def update_field(gh: GitHubGraphQL, project_id: str, item_id: str, 
                 field_id: str, value: str, field_type: str = "single_select"):
    """
    Actualiza un campo del item en el proyecto.
    
    Args:
        gh: Cliente GraphQL
        project_id: ID del proyecto
        item_id: ID del item en el proyecto
        field_id: ID del campo a actualizar
        value: Valor a establecer
        field_type: Tipo de campo (single_select, text, number)
    """
    if field_type == "single_select":
        value_payload = f'singleSelectOptionId: "{value}"'
    elif field_type == "text":
        value_payload = f'text: "{value}"'
    elif field_type == "number":
        value_payload = f'number: {value}'
    else:
        raise ValueError(f"Tipo de campo no soportado: {field_type}")
    
    mutation = f"""
    mutation {{
      updateProjectV2ItemFieldValue(input: {{
        projectId: "{project_id}"
        itemId: "{item_id}"
        fieldId: "{field_id}"
        value: {{
          {value_payload}
        }}
      }}) {{
        projectV2Item {{
          id
        }}
      }}
    }}
    """
    
    result = gh.execute_query(mutation)
    if "errors" in result:
        logger.error(f"Error actualizando campo: {result['errors']}")
        raise ValueError(f"No se pudo actualizar el campo: {result['errors']}")


def get_issue_node_id(gh: GitHubGraphQL, issue_number: int) -> str:
    """
    Obtiene el node ID de un issue por su número.
    
    Args:
        gh: Cliente GraphQL
        issue_number: Número del issue
    
    Returns:
        Node ID del issue
    """
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          id
          title
          state
        }
      }
    }
    """
    
    result = gh.execute_query(query, {
        "owner": ORG_NAME,
        "repo": REPO_NAME,
        "number": issue_number
    })
    
    issue = result["data"]["repository"]["issue"]
    if not issue:
        raise ValueError(f"Issue #{issue_number} no encontrado")
    
    return issue["id"]


def detect_fuente_from_title(title: str) -> str:
    """Detecta la fuente de datos desde el título del issue."""
    title_lower = title.lower()
    
    if "idescat" in title_lower:
        return "IDESCAT"
    elif "incasol" in title_lower or "incasòl" in title_lower:
        return "Incasòl"
    elif "opendata" in title_lower or "open data" in title_lower:
        return "OpenData BCN"
    elif "portal" in title_lower and "dades" in title_lower:
        return "Portal Dades"
    else:
        return "Internal"


def detect_impact_from_labels(labels: list) -> str:
    """Detecta el impacto desde los labels del issue."""
    label_names = [label.get("name", "").lower() for label in labels]
    
    if any("critical" in label or "high" in label for label in label_names):
        return "High"
    elif any("medium" in label for label in label_names):
        return "Medium"
    else:
        return "Low"


def sync_issue_with_project(
    gh: GitHubGraphQL,
    issue_number: int,
    impact: Optional[str] = None,
    fuente: Optional[str] = None,
    sprint: Optional[str] = None,
    kpi_objetivo: Optional[str] = None,
    dqc_status: Optional[str] = None,
    auto_detect: bool = False
):
    """
    Sincroniza un issue con el proyecto y configura sus campos.
    
    Args:
        gh: Cliente GraphQL
        issue_number: Número del issue
        impact: "High", "Medium", "Low"
        fuente: "IDESCAT", "Incasòl", "OpenData BCN", etc.
        sprint: "Sprint 1", "Sprint 2", etc.
        kpi_objetivo: Descripción del KPI objetivo
        dqc_status: "Passed", "Failed", "Pending" (Estado DQC)
        auto_detect: Si True, detecta automáticamente campos desde el issue
    """
    logger.info(f"Sincronizando issue #{issue_number}...")
    
    # 1. Obtener info del proyecto
    project_info = get_project_info(gh)
    project_id = project_info["project_id"]
    fields = project_info["fields"]
    
    logger.info(f"Proyecto: {project_info['title']} (ID: {project_id[:20]}...)")
    
    # 2. Obtener node ID del issue
    issue_id = get_issue_node_id(gh, issue_number)
    
    # 3. Obtener detalles del issue para auto-detección
    if auto_detect:
        issue_details = gh.get_issues_with_details(
            owner=ORG_NAME,
            repo=REPO_NAME,
            state="OPEN",
            limit=1
        )
        # Buscar el issue específico
        for issue in issue_details.get("issues", []):
            if issue.get("number") == issue_number:
                if not fuente:
                    fuente = detect_fuente_from_title(issue.get("title", ""))
                if not impact:
                    impact = detect_impact_from_labels(issue.get("labels", []))
                break
    
    # 4. Añadir al proyecto
    try:
        item_id = add_issue_to_project(gh, project_id, issue_id)
        logger.info(f"✓ Issue añadido al proyecto (item_id: {item_id[:20]}...)")
    except Exception as e:
        logger.warning(f"No se pudo añadir issue (puede que ya esté): {e}")
        # Intentar obtener item_id existente
        items_data = gh.get_project_items(project_id=project_id, limit=100)
        item_id = None
        for item in items_data.get("items", []):
            content = item.get("content", {})
            if content:
                # Obtener el node ID del issue desde el content
                issue_node_id = get_issue_node_id(gh, content.get("number", 0))
                if issue_node_id == issue_id:
                    item_id = item["id"]
                    logger.info(f"✓ Issue ya está en el proyecto (item_id: {item_id[:20]}...)")
                    break
        
        if not item_id:
            raise ValueError("No se pudo añadir ni encontrar el issue en el proyecto")
    
    # 5. Configurar campos personalizados
    updated_fields = []
    
    if impact and "Impacto" in fields:
        impact_field = fields["Impacto"]
        if impact_field.get("dataType") == "SINGLE_SELECT":
            impact_options = impact_field.get("options", {})
            impact_option_id = impact_options.get(impact)
            if impact_option_id:
                update_field(gh, project_id, item_id, impact_field["id"], 
                            impact_option_id, "single_select")
                updated_fields.append(f"Impacto: {impact}")
            else:
                logger.warning(f"Opción '{impact}' no encontrada en campo Impacto")
    
    if fuente and "Fuente de Datos" in fields:
        fuente_field = fields["Fuente de Datos"]
        if fuente_field.get("dataType") == "SINGLE_SELECT":
            fuente_options = fuente_field.get("options", {})
            fuente_option_id = fuente_options.get(fuente)
            if fuente_option_id:
                update_field(gh, project_id, item_id, fuente_field["id"],
                            fuente_option_id, "single_select")
                updated_fields.append(f"Fuente: {fuente}")
            else:
                logger.warning(f"Opción '{fuente}' no encontrada en campo Fuente de Datos")
    
    if sprint and "Sprint" in fields:
        sprint_field = fields["Sprint"]
        if sprint_field.get("dataType") == "SINGLE_SELECT":
            sprint_options = sprint_field.get("options", {})
            sprint_option_id = sprint_options.get(sprint)
            if sprint_option_id:
                update_field(gh, project_id, item_id, sprint_field["id"],
                            sprint_option_id, "single_select")
                updated_fields.append(f"Sprint: {sprint}")
            else:
                logger.warning(f"Opción '{sprint}' no encontrada en campo Sprint")
    
    if kpi_objetivo and "KPI objetivo" in fields:
        kpi_field = fields["KPI objetivo"]
        update_field(gh, project_id, item_id, kpi_field["id"],
                    kpi_objetivo, "text")
        updated_fields.append("KPI objetivo")
    
    if dqc_status and "Estado DQC" in fields:
        dqc_field = fields["Estado DQC"]
        if dqc_field.get("dataType") == "SINGLE_SELECT":
            dqc_options = dqc_field.get("options", {})
            dqc_option_id = dqc_options.get(dqc_status)
            if dqc_option_id:
                update_field(gh, project_id, item_id, dqc_field["id"],
                            dqc_option_id, "single_select")
                updated_fields.append(f"Estado DQC: {dqc_status}")
            else:
                logger.warning(f"Opción '{dqc_status}' no encontrada en campo Estado DQC. Opciones disponibles: {list(dqc_options.keys())}")
    
    if updated_fields:
        logger.info(f"✓ Campos actualizados: {', '.join(updated_fields)}")
    else:
        logger.warning("No se actualizaron campos (verificar que existan en el proyecto)")
    
    logger.info(f"✅ Issue #{issue_number} sincronizado correctamente\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza issues con GitHub Projects v2"
    )
    parser.add_argument(
        "--issue",
        type=int,
        required=True,
        help="Número del issue a sincronizar"
    )
    parser.add_argument(
        "--impact",
        choices=["High", "Medium", "Low"],
        help="Impacto del issue"
    )
    parser.add_argument(
        "--fuente",
        help="Fuente de datos (IDESCAT, Incasòl, OpenData BCN, Portal Dades, Internal)"
    )
    parser.add_argument(
        "--sprint",
        help="Sprint (Sprint 1, Sprint 2, etc.)"
    )
    parser.add_argument(
        "--kpi-objetivo",
        dest="kpi_objetivo",
        help="Descripción del KPI objetivo"
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Detectar automáticamente campos desde el issue"
    )
    parser.add_argument(
        "--dqc-status",
        choices=["Passed", "Failed", "Pending"],
        help="Estado DQC (Passed, Failed, Pending)"
    )
    
    args = parser.parse_args()
    
    # Obtener token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN no encontrado en variables de entorno")
        sys.exit(1)
    
    # Inicializar cliente GraphQL
    gh = GitHubGraphQL(token=token)
    
    # Sincronizar issue
    try:
        sync_issue_with_project(
            gh=gh,
            issue_number=args.issue,
            impact=args.impact,
            fuente=args.fuente,
            sprint=args.sprint,
            kpi_objetivo=args.kpi_objetivo,
            dqc_status=args.dqc_status,
            auto_detect=args.auto_detect
        )
    except Exception as e:
        logger.error(f"Error sincronizando issue: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

