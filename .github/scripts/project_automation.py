#!/usr/bin/env python3
"""
Automatización de GitHub Projects v2 para Barcelona Housing Analyzer
Sincroniza issues con el tablero del proyecto y actualiza campos personalizados

Uso:
    python .github/scripts/project_automation.py --issue 24 --impact High --fuente IDESCAT --sprint "Sprint 1"
    python .github/scripts/project_automation.py --issue 24 --auto-detect
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

# Añadir el directorio raíz al path para imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.github_graphql import GitHubGraphQL

# Configuración
ORG_NAME = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
PROJECT_NUMBER = int(os.environ.get("PROJECT_NUMBER", "1"))  # Ajustar según tu proyecto
PROJECT_OWNER = os.environ.get("PROJECT_OWNER", ORG_NAME)  # Owner del Project V2 (user u org)

logger = logging.getLogger(__name__)


class ProjectCache:
    """Cache simple en memoria para project info y items."""

    _project_info: Dict[Tuple[int, str], Dict[str, Any]] = {}
    _items_cache: Dict[str, Dict[int, str]] = {}

    @classmethod
    def get_project_info(cls, key: Tuple[int, str]) -> Optional[Dict[str, Any]]:
        return cls._project_info.get(key)

    @classmethod
    def set_project_info(cls, key: Tuple[int, str], info: Dict[str, Any]) -> None:
        cls._project_info[key] = info

    @classmethod
    def get_items(cls, project_id: str) -> Optional[Dict[int, str]]:
        return cls._items_cache.get(project_id)

    @classmethod
    def set_items(cls, project_id: str, mapping: Dict[int, str]) -> None:
        cls._items_cache[project_id] = mapping


def get_project_info(
    gh: GitHubGraphQL,
    project_number: Optional[int] = None,
    project_owner: Optional[str] = None,
    cached_fields: Optional[Dict[str, Any]] = None
) -> Dict:
    """
    Obtiene ID del proyecto y campos personalizados.
    
    Args:
        gh: Cliente GraphQL
        project_number: Número del proyecto (default: PROJECT_NUMBER)
        project_owner: Owner del proyecto (user u org, default: PROJECT_OWNER)
    
    Returns:
        Dict con project_id, title y fields mapeados
    """
    proj_num = project_number or PROJECT_NUMBER
    proj_owner = project_owner or PROJECT_OWNER
    cache_key = (proj_num, proj_owner)

    cached = ProjectCache.get_project_info(cache_key)
    if cached and not cached_fields:
        return cached
    
    try:
        if cached_fields:
            project = {
                "id": cached_fields.get("project_id"),
                "title": cached_fields.get("title", "Unknown"),
                "fields": {"nodes": cached_fields.get("raw_fields", [])},
            }
        else:
            project = gh.get_project_v2_any(
                owner=ORG_NAME,
                repo=REPO_NAME,
                project_owner=proj_owner,
                project_number=proj_num
            )

        if not project:
            raise ValueError(f"Proyecto #{proj_num} no encontrado")
    except Exception as e:
        error_msg = str(e)
        if "Could not resolve" in error_msg or "not found" in error_msg.lower() or "404" in error_msg:
            logger.error(f"❌ Proyecto #{proj_num} no encontrado")
            logger.error("   Posibles causas:")
            logger.error(f"   1. El proyecto no existe o el número es incorrecto")
            logger.error(f"   2. El proyecto está en una organización diferente")
            logger.error(f"   3. El token no tiene permisos 'project'")
            logger.error("")
            logger.error("   Soluciones:")
            logger.error(f"   - Verifica el número del proyecto en la URL: https://github.com/users/{proj_owner}/projects")
            logger.error(f"   - Especifica el número correcto: export PROJECT_NUMBER=2")
            logger.error(f"   - O usa: python .github/scripts/project_automation.py --issue 24 --project-number 2")
            logger.error(f"   - Si el proyecto es de otra organización/usuario, especifica: --project-owner <owner>")
            logger.error(f"   - Confirma scopes del token: debe incluir 'project' (no solo read:project)")
            logger.error(f"   - Si el proyecto es privado, el token debe tener acceso a proyectos privados del owner")
        raise
    
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
        # Para Iteration, mapear iteraciones
        if field.get("dataType") == "ITERATION" and "configuration" in field:
            iterations = field.get("configuration", {}).get("iterations", [])
            field_data["iterations"] = {
                it["title"]: it["id"] for it in iterations if it.get("title") and it.get("id")
            }
        
        fields[field_name] = field_data
    
    result_info = {
        "project_id": project["id"],
        "title": project.get("title", "Unknown"),
        "fields": fields
    }
    if not cached_fields:
        ProjectCache.set_project_info(cache_key, result_info)
    return result_info


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
    elif field_type == "iteration":
        value_payload = f'iterationId: "{value}"'
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
    
    # execute_query ya devuelve el nodo "data"; aquí esperamos "repository"
    if not isinstance(result, dict):
        raise ValueError(f"No se pudo obtener datos de GraphQL para issue #{issue_number}")
    
    repo_node = result.get("repository") or {}
    issue = repo_node.get("issue")
    
    if not issue:
        raise ValueError(
            f"Issue #{issue_number} no encontrado en {ORG_NAME}/{REPO_NAME}. "
            "Verifica que el número es correcto y que el token tiene scope repo."
        )
    
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


def _resolve_option(value: Optional[str], options: Dict[str, str]) -> Optional[str]:
    """
    Devuelve el option_id haciendo match case-insensitive por nombre.
    """
    if not value:
        return None
    for name, opt_id in options.items():
        if name.lower() == value.lower():
            return opt_id
    return options.get(value)


def sync_issue_with_project(
    gh: GitHubGraphQL,
    issue_number: int,
    impact: Optional[str] = None,
    fuente: Optional[str] = None,
    sprint: Optional[str] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    kpi_objetivo: Optional[str] = None,
    dqc_status: Optional[str] = None,
    project_number: Optional[int] = None,
    project_owner: Optional[str] = None,
    auto_detect: bool = False,
    skip_add: bool = False,
    items_map: Optional[Dict[int, str]] = None
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
        project_number: Número del proyecto (default: PROJECT_NUMBER)
        project_owner: Owner del proyecto (user u org, default: PROJECT_OWNER)
        auto_detect: Si True, detecta automáticamente campos desde el issue
    """
    logger.info(f"Sincronizando issue #{issue_number}...")
    
    # 1. Obtener info del proyecto
    project_info = get_project_info(
        gh,
        project_number=project_number,
        project_owner=project_owner
    )
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
    
    # 4. Añadir al proyecto (o reutilizar item_id cacheado)
    item_id = None
    cached_items = items_map or ProjectCache.get_items(project_id)
    if cached_items:
        item_id = cached_items.get(issue_number)

    if item_id is None and not skip_add:
        try:
            item_id = add_issue_to_project(gh, project_id, issue_id)
            logger.info(f"✓ Issue añadido al proyecto (item_id: {item_id[:20]}...)")
        except Exception as e:
            logger.warning(f"No se pudo añadir issue (puede que ya esté): {e}")

    if item_id is None:
        items_data = gh.get_project_items(project_id=project_id, limit=200)
        mapping = {
            itm.get("content", {}).get("number"): itm["id"]
            for itm in items_data.get("items", [])
            if itm.get("content") and itm.get("content", {}).get("number")
        }
        ProjectCache.set_items(project_id, mapping)
        item_id = mapping.get(issue_number)
        if item_id:
            logger.info(f"✓ Issue ya está en el proyecto (item_id: {item_id[:20]}...)")
        else:
            raise ValueError("No se pudo añadir ni encontrar el issue en el proyecto")
    
    # 5. Configurar campos personalizados
    updated_fields = []
    
    if impact and "Impacto" in fields:
        impact_field = fields["Impacto"]
        if impact_field.get("dataType") == "SINGLE_SELECT":
            impact_options = impact_field.get("options", {})
            impact_option_id = _resolve_option(impact, impact_options)
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
            fuente_option_id = _resolve_option(fuente, fuente_options)
            if fuente_option_id:
                update_field(gh, project_id, item_id, fuente_field["id"],
                            fuente_option_id, "single_select")
                updated_fields.append(f"Fuente: {fuente}")
            else:
                logger.warning(f"Opción '{fuente}' no encontrada en campo Fuente de Datos")
    
    # Iteration (usando argumento --sprint)
    if sprint and "Iteration" in fields:
        iteration_field = fields["Iteration"]
        if iteration_field.get("dataType") == "ITERATION":
            iter_options = iteration_field.get("iterations", {})
            iter_id = _resolve_option(sprint, iter_options)
            if iter_id:
                update_field(gh, project_id, item_id, iteration_field["id"],
                            iter_id, "iteration")
                updated_fields.append(f"Iteration: {sprint}")
            else:
                logger.warning(f"Opción '{sprint}' no encontrada en campo Iteration")
    
    if kpi_objetivo and "KPI objetivo" in fields:
        kpi_field = fields["KPI objetivo"]
        update_field(gh, project_id, item_id, kpi_field["id"],
                    kpi_objetivo, "text")
        updated_fields.append("KPI objetivo")
    
    if dqc_status and "Estado DQC" in fields:
        dqc_field = fields["Estado DQC"]
        if dqc_field.get("dataType") == "SINGLE_SELECT":
            dqc_options = dqc_field.get("options", {})
            dqc_option_id = _resolve_option(dqc_status, dqc_options)
            if dqc_option_id:
                update_field(gh, project_id, item_id, dqc_field["id"],
                            dqc_option_id, "single_select")
                updated_fields.append(f"Estado DQC: {dqc_status}")
            else:
                logger.warning(f"Opción '{dqc_status}' no encontrada en campo Estado DQC. Opciones disponibles: {list(dqc_options.keys())}")

    if status and "Status" in fields:
        status_field = fields["Status"]
        if status_field.get("dataType") == "SINGLE_SELECT":
            status_options = status_field.get("options", {})
            status_option_id = _resolve_option(status, status_options)
            if status_option_id:
                update_field(gh, project_id, item_id, status_field["id"],
                            status_option_id, "single_select")
                updated_fields.append(f"Status: {status}")
            else:
                logger.warning(f"Opción '{status}' no encontrada en campo Status. Opciones: {list(status_options.keys())}")

    if owner and "Owner" in fields:
        owner_field = fields["Owner"]
        if owner_field.get("dataType") == "SINGLE_SELECT":
            owner_options = owner_field.get("options", {})
            owner_option_id = _resolve_option(owner, owner_options)
            if owner_option_id:
                update_field(gh, project_id, item_id, owner_field["id"],
                            owner_option_id, "single_select")
                updated_fields.append(f"Owner: {owner}")
            else:
                logger.warning(f"Opción '{owner}' no encontrada en campo Owner. Opciones: {list(owner_options.keys())}")
    
    if updated_fields:
        logger.info(f"✓ Campos actualizados: {', '.join(updated_fields)}")
    else:
        logger.warning("No se actualizaron campos (verificar que existan en el proyecto)")
    
    logger.info(f"✅ Issue #{issue_number} sincronizado correctamente\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza issues con GitHub Projects v2 (optimizado batch)"
    )
    parser.add_argument("--issue", type=int, help="Número del issue (usar --issues para batch)")
    parser.add_argument("--issues", nargs="+", type=int, help="Lista de issues a procesar")
    parser.add_argument("--impact", help="Impacto (High, Medium, Low, Critical)")
    parser.add_argument("--fuente", help="Fuente de datos (IDESCAT, Incasòl, OpenData BCN, Portal Dades, Internal)")
    parser.add_argument("--sprint", help="Sprint/Iteration (ej: Sprint 1 (Idescat))")
    parser.add_argument("--status", help="Status (Backlog, Ready, In Progress, Review/QA, Blocked..., Done)")
    parser.add_argument("--owner", help="Owner (Data Engineering, Data Analysis, Product, Infraestructure)")
    parser.add_argument("--kpi-objetivo", dest="kpi_objetivo", help="Descripción del KPI objetivo")
    parser.add_argument(
        "--dqc-status",
        choices=["Passed", "Failed", "Pending", "N/A"],
        help="Estado DQC (Passed, Failed, Pending, N/A)"
    )
    parser.add_argument("--project-number", type=int, default=None, help=f"Número del proyecto (default: {PROJECT_NUMBER})")
    parser.add_argument("--project-owner", type=str, default=None, help=f"Owner del proyecto (default: {PROJECT_OWNER})")
    parser.add_argument("--skip-add", action="store_true", help="No intentar añadir al proyecto (más rápido si ya está)")
    parser.add_argument("--rate-limit-delay", type=float, default=0.5, help="Delay entre issues (default: 0.5s)")
    parser.add_argument("--quiet", action="store_true", help="Solo warnings/errores")
    parser.add_argument("--get-fields-only", action="store_true", help="Imprime campos del proyecto en JSON y termina")
    parser.add_argument("--use-cached-fields", help="Ruta a JSON con campos cacheados")
    parser.add_argument("--auto-detect", action="store_true", help="Detectar campos desde el issue (desactivado por defecto)")
    parser.add_argument("--verbose", action="store_true", help="Log DEBUG")
    
    args = parser.parse_args()

    if not args.issue and not args.issues and not args.get_fields_only:
        parser.error("Debes indicar --issue, --issues o --get-fields-only")

    logging_level = logging.DEBUG if args.verbose else (logging.WARNING if args.quiet else logging.INFO)
    logging.basicConfig(level=logging_level, format="%(asctime)s - %(levelname)s - %(message)s")

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            import subprocess
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True
            )
            token = result.stdout.strip()
            logger.info("✓ Token obtenido desde gh CLI")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("GITHUB_TOKEN no encontrado en variables de entorno")
            sys.exit(1)

    gh = GitHubGraphQL(token=token)
    project_num = args.project_number if args.project_number is not None else PROJECT_NUMBER
    project_owner = args.project_owner if args.project_owner else PROJECT_OWNER

    cached_fields = None
    if args.use_cached_fields:
        with open(args.use_cached_fields, "r", encoding="utf-8") as f:
            cached_fields = json.load(f)

    if args.get_fields_only:
        info = get_project_info(gh, project_number=project_num, project_owner=project_owner, cached_fields=cached_fields)
        out = {
            "project_id": info["project_id"],
            "title": info["title"],
            "raw_fields": info["fields"].get("nodes", []),
        }
        print(json.dumps(out, indent=2))
        sys.exit(0)

    project_info = get_project_info(gh, project_number=project_num, project_owner=project_owner, cached_fields=cached_fields)
    project_id = project_info["project_id"]

    issues_to_process: List[int] = []
    if args.issue:
        issues_to_process.append(args.issue)
    if args.issues:
        issues_to_process.extend(args.issues)

    start_time = time.time()

    items_cache = ProjectCache.get_items(project_id)

    for idx, issue_num in enumerate(issues_to_process, start=1):
        try:
            sync_issue_with_project(
                gh=gh,
                issue_number=issue_num,
                impact=args.impact,
                fuente=args.fuente,
                sprint=args.sprint,
                status=args.status,
                owner=args.owner,
                kpi_objetivo=args.kpi_objetivo,
                dqc_status=args.dqc_status,
                project_number=project_num,
                project_owner=project_owner,
                auto_detect=args.auto_detect,
                skip_add=args.skip_add,
                items_map=items_cache
            )
        except Exception as e:
            logger.error(f"Error sincronizando issue {issue_num}: {e}", exc_info=args.verbose)
        if len(issues_to_process) > 1 and idx < len(issues_to_process):
            time.sleep(args.rate_limit_delay)

    duration = time.time() - start_time
    logger.info("Tiempo total: %.2fs (%.2fs por issue)", duration, duration / max(1, len(issues_to_process)))


if __name__ == "__main__":
    main()

