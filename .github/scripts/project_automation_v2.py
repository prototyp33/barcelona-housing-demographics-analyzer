#!/usr/bin/env python3
"""
Automatización optimizada (v2) de GitHub Projects v2 para Barcelona Housing Analyzer.

Características:
- Cache singleton de metadatos.
- Lookup O(1) de items por número de issue.
- Mutaciones batch con aliases para múltiples campos.
- CLI con rate limiting y soporte de skip-add.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).parent.parent.parent

# Asegurar imports locales
import sys

sys.path.insert(0, str(REPO_ROOT))

from scripts.github_graphql import GitHubGraphQL

logger = logging.getLogger(__name__)

ORG_NAME = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
PROJECT_OWNER = os.environ.get("PROJECT_OWNER", ORG_NAME)
PROJECT_NUMBER = int(os.environ.get("PROJECT_NUMBER", "7"))

# Mapeo explícito de argumentos CLI a nombres de campos en GitHub Project
FIELD_MAPPING = {
    "impact": "Impacto",
    "fuente": "Fuente",
    "sprint": "Sprint",
    "kpi_objetivo": "KPI",
    "status": "Status",
    "owner": "Owner",
    "dqc_status": "Estado DQC",
}


@dataclass
class FieldUpdate:
    """Representa una actualización de campo."""

    alias: str
    field_id: str
    value_payload: str


class ProjectCache:
    """
    Singleton para cachear metadatos del proyecto y el índice de items.

    Performance:
        Evita llamadas repetidas a GraphQL para proyecto y reduce O(n) de
        paginar items a búsquedas O(1) usando un índice en memoria.
    """

    _instance: Optional["ProjectCache"] = None

    def __new__(cls) -> "ProjectCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._project_info: Dict[Tuple[int, str], Dict[str, Any]] = {}
            cls._instance._item_index: Dict[str, Dict[int, str]] = {}
        return cls._instance

    def get_project_info(
        self, key: Tuple[int, str]
    ) -> Optional[Dict[str, Any]]:
        return self._project_info.get(key)

    def set_project_info(
        self, key: Tuple[int, str], info: Dict[str, Any]
    ) -> None:
        self._project_info[key] = info

    def get_item_id(self, project_id: str, issue_number: int) -> Optional[str]:
        items = self._item_index.get(project_id, {})
        return items.get(issue_number)

    def set_item_id(self, project_id: str, issue_number: int, item_id: str) -> None:
        self._item_index.setdefault(project_id, {})[issue_number] = item_id


def _map_fields(raw_nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Construye un dict de campos con opciones e iteraciones mapeadas.
    """
    fields: Dict[str, Dict[str, Any]] = {}
    for field in raw_nodes:
        field_name = field.get("name")
        if not field_name:
            continue
        entry: Dict[str, Any] = {
            "name": field_name,
            "id": field.get("id"),
            "dataType": field.get("dataType"),
        }
        if field.get("dataType") == "SINGLE_SELECT":
            entry["options"] = {
                opt["name"]: opt["id"] for opt in field.get("options", [])
            }
        if field.get("dataType") == "ITERATION":
            iterations = field.get("configuration", {}).get("iterations", [])
            entry["iterations"] = {
                it["title"]: it["id"]
                for it in iterations
                if it.get("title") and it.get("id")
            }
        fields[field_name.lower()] = entry
    return fields


def get_project_info(
    gh: GitHubGraphQL,
    project_number: Optional[int] = None,
    project_owner: Optional[str] = None,
    cached_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Obtiene info del proyecto y campos, usando cache si está disponible.

    Performance:
        Reutiliza metadatos en memoria para evitar múltiples llamadas. Costo O(1)
        tras la primera carga.
    """
    cache = ProjectCache()
    proj_num = project_number or PROJECT_NUMBER
    proj_owner = project_owner or PROJECT_OWNER
    cache_key = (proj_num, proj_owner)

    cached = cache.get_project_info(cache_key)
    if cached and not cached_fields:
        return cached

    if cached_fields:
        raw_fields = cached_fields.get("raw_fields", [])
        project_info = {
            "project_id": cached_fields.get("project_id"),
            "title": cached_fields.get("title", "Unknown"),
            "raw_fields": raw_fields,
            "fields": _map_fields(raw_fields),
        }
        cache.set_project_info(cache_key, project_info)
        return project_info

    # Intentar primero como organización; si no, como usuario (projectV2 personal)
    query_org = """
    query($owner: String!, $number: Int!) {
      organization(login: $owner) {
        projectV2(number: $number) {
          id
          title
          fields(first: 50) {
            nodes {
              __typename
              ... on ProjectV2FieldCommon {
                id
                name
                dataType
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options { id name }
              }
              ... on ProjectV2IterationField {
                id
                name
                configuration { iterations { id title } }
              }
            }
          }
        }
      }
    }
    """
    query_user = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
          title
          fields(first: 50) {
            nodes {
              __typename
              ... on ProjectV2FieldCommon {
                id
                name
                dataType
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options { id name }
              }
              ... on ProjectV2IterationField {
                id
                name
                configuration { iterations { id title } }
              }
            }
          }
        }
      }
    }
    """

    variables = {"owner": proj_owner, "number": proj_num}

    project = None
    try:
        org_resp = gh.execute_query(query_org, variables)
        if org_resp.get("organization") and org_resp["organization"].get("projectV2"):
            project = org_resp["organization"]["projectV2"]
    except RuntimeError:
        logger.info("Proyecto no encontrado en Org; se probará ámbito User...")

    if project is None:
        user_resp = gh.execute_query(query_user, variables)
        if user_resp.get("user") and user_resp["user"].get("projectV2"):
            project = user_resp["user"]["projectV2"]

    if not project:
        raise ValueError(
            f"Proyecto #{proj_num} no encontrado como organización ni usuario: {proj_owner}"
        )

    raw_fields = project.get("fields", {}).get("nodes", [])
    project_info = {
        "project_id": project["id"],
        "title": project.get("title", "Unknown"),
        "raw_fields": raw_fields,
        "fields": _map_fields(raw_fields),
    }
    cache.set_project_info(cache_key, project_info)
    return project_info


def get_issue_node_id(gh: GitHubGraphQL, issue_number: int) -> str:
    """
    Obtiene el node ID de un issue por su número.

    Performance:
        Query directa O(1) al issue.
    """
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          id
        }
      }
    }
    """
    result = gh.execute_query(
        query,
        {"owner": ORG_NAME, "repo": REPO_NAME, "number": issue_number},
    )
    repo_node = result.get("repository") if isinstance(result, dict) else None
    issue = repo_node.get("issue") if repo_node else None
    if not issue:
        raise ValueError(f"Issue #{issue_number} no encontrado en {ORG_NAME}/{REPO_NAME}")
    return issue["id"]


def get_item_id_for_issue_optimized(
    gh: GitHubGraphQL,
    project_id: str,
    issue_number: int,
    owner: str,
    repo: str,
) -> Optional[str]:
    """
    Lookup directo del item usando query filtrada en items(first:1).

    Performance:
        Evita paginar todos los items (O(n)) usando filtro query O(1).
    """
    query = """
    query($projectId: ID!, $queryString: String!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 1, query: $queryString) {
            nodes {
              id
              content {
                ... on Issue {
                  number
                }
              }
            }
          }
        }
      }
    }
    """
    query_string = f"repo:{owner}/{repo} number:{issue_number} is:issue"
    variables = {"projectId": project_id, "queryString": query_string}
    result = gh.execute_query(query, variables)
    node = result.get("node") if isinstance(result, dict) else None
    items = node.get("items", {}) if node else {}
    nodes = items.get("nodes") or []
    if not nodes:
        return None
    return nodes[0].get("id")


def _resolve_option(
    value: Optional[str], options: Dict[str, str]
) -> Optional[str]:
    """Match case-insensitive para opciones single select/iteration."""
    if not value:
        return None
    for name, opt_id in options.items():
        if name.lower() == value.lower():
            return opt_id
    return options.get(value)


def _build_field_updates(
    project_fields: Dict[str, Dict[str, Any]],
    impact: Optional[str],
    fuente: Optional[str],
    sprint: Optional[str],
    status: Optional[str],
    owner: Optional[str],
    dqc_status: Optional[str],
    kpi_objetivo: Optional[str],
) -> List[FieldUpdate]:
    """
    Prepara la lista de updates con payloads ya formateados.
    """
    updates: List[FieldUpdate] = []
    alias_counter = 1

    def next_alias() -> str:
        nonlocal alias_counter
        alias = f"f{alias_counter}"
        alias_counter += 1
        return alias

    def resolve_field(name_key: str) -> Optional[Dict[str, Any]]:
        mapped = FIELD_MAPPING.get(name_key, name_key)
        field = project_fields.get(mapped.lower())
        if not field:
            logger.warning(
                "Field '%s' (from arg '%s') not found in project.",
                mapped,
                name_key,
            )
        return field

    if impact:
        field = resolve_field("impact")
        opt_id = _resolve_option(impact, field.get("options", {})) if field else None
        if field and opt_id:
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f'singleSelectOptionId: "{opt_id}"',
                )
            )

    if fuente:
        field = resolve_field("fuente")
        opt_id = _resolve_option(fuente, field.get("options", {})) if field else None
        if field and opt_id:
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f'singleSelectOptionId: "{opt_id}"',
                )
            )

    if sprint:
        field = resolve_field("sprint")
        iter_id = _resolve_option(sprint, field.get("iterations", {})) if field else None
        if field and iter_id:
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f'iterationId: "{iter_id}"',
                )
            )

    if status:
        field = resolve_field("status")
        opt_id = _resolve_option(status, field.get("options", {})) if field else None
        if field and opt_id:
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f'singleSelectOptionId: "{opt_id}"',
                )
            )

    if owner:
        field = resolve_field("owner")
        opt_id = _resolve_option(owner, field.get("options", {})) if field else None
        if field and opt_id:
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f'singleSelectOptionId: "{opt_id}"',
                )
            )

    if dqc_status:
        field = resolve_field("dqc_status")
        opt_id = _resolve_option(dqc_status, field.get("options", {})) if field else None
        if field and opt_id:
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f'singleSelectOptionId: "{opt_id}"',
                )
            )

    if kpi_objetivo:
        field = resolve_field("kpi_objetivo")
        if field:
            kpi_json = json.dumps(kpi_objetivo)
            updates.append(
                FieldUpdate(
                    alias=next_alias(),
                    field_id=field["id"],
                    value_payload=f"text: {kpi_json}",
                )
            )

    return updates


def update_fields_batch(
    gh: GitHubGraphQL, project_id: str, item_id: str, updates: List[FieldUpdate]
) -> None:
    """
    Ejecuta una mutación única con aliases para múltiples campos.

    Performance:
        Reemplaza múltiples mutaciones individuales por una sola llamada (O(1) por issue).
    """
    if not updates:
        logger.info("No hay campos para actualizar")
        return

    mutation_lines = ["mutation UpdateFields {"]
    for upd in updates:
        mutation_lines.append(
            f"""{upd.alias}: updateProjectV2ItemFieldValue(input: {{
        projectId: "{project_id}"
        itemId: "{item_id}"
        fieldId: "{upd.field_id}"
        value: {{
          {upd.value_payload}
        }}
      }}) {{
        projectV2Item {{ id }}
      }}"""
        )
    mutation_lines.append("}")
    mutation = "\n".join(mutation_lines)

    result = gh.execute_query(mutation)
    if isinstance(result, dict) and result.get("errors"):
        raise ValueError(f"Error en mutación batch: {result['errors']}")


def add_issue_to_project(gh: GitHubGraphQL, project_id: str, issue_id: str) -> str:
    """
    Añade el issue al proyecto y retorna el item_id.

    Performance:
        Se usa solo cuando no existe item y skip_add es False.
    """
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {
        projectId: $projectId
        contentId: $contentId
      }) {
        item { id }
      }
    }
    """
    result = gh.execute_query(
        mutation, {"projectId": project_id, "contentId": issue_id}
    )
    if isinstance(result, dict) and result.get("errors"):
        raise ValueError(result["errors"])
    return result["addProjectV2ItemById"]["item"]["id"]


def sync_issue(
    gh: GitHubGraphQL,
    project_info: Dict[str, Any],
    issue_number: int,
    impact: Optional[str],
    fuente: Optional[str],
    sprint: Optional[str],
    status: Optional[str],
    owner: Optional[str],
    dqc_status: Optional[str],
    kpi_objetivo: Optional[str],
    skip_add: bool,
) -> None:
    """
    Sincroniza un issue: lookup, optional add, y mutación batch.

    Performance:
        - Lookup O(1) de item.
        - Una mutación batch por issue.
        - Cache en memoria para evitar re-fetch de metadatos.
    """
    cache = ProjectCache()
    project_id = project_info["project_id"]
    fields = project_info["fields"]

    logger.info("Procesando issue #%s", issue_number)

    item_id = cache.get_item_id(project_id, issue_number)
    if not item_id:
        item_id = get_item_id_for_issue_optimized(
            gh=gh,
            project_id=project_id,
            issue_number=issue_number,
            owner=ORG_NAME,
            repo=REPO_NAME,
        )
        if item_id:
            cache.set_item_id(project_id, issue_number, item_id)

    if not item_id and skip_add:
        logger.info("Item no existe y skip_add activo; se omite issue #%s", issue_number)
        return

    if not item_id:
        issue_node_id = get_issue_node_id(gh, issue_number)
        item_id = add_issue_to_project(gh, project_id, issue_node_id)
        cache.set_item_id(project_id, issue_number, item_id)
        logger.info("Issue añadido al proyecto (item_id %s)", item_id)

    updates = _build_field_updates(
        project_fields=fields,
        impact=impact,
        fuente=fuente,
        sprint=sprint,
        status=status,
        owner=owner,
        dqc_status=dqc_status,
        kpi_objetivo=kpi_objetivo,
    )
    if updates:
        update_fields_batch(gh, project_id, item_id, updates)
        logger.info("Campos actualizados para issue #%s", issue_number)
    else:
        logger.info("No hay campos para actualizar en issue #%s", issue_number)


def sync_issues_batch(
    gh: GitHubGraphQL,
    issues: List[int],
    project_number: Optional[int],
    project_owner: Optional[str],
    impact: Optional[str],
    fuente: Optional[str],
    sprint: Optional[str],
    status: Optional[str],
    owner: Optional[str],
    dqc_status: Optional[str],
    kpi_objetivo: Optional[str],
    skip_add: bool,
    rate_limit_delay: float,
) -> None:
    """
    Sincroniza en batch una lista de issues con cache compartido.

    Performance:
        - Carga de proyecto una sola vez.
        - Reutiliza cache y lookup O(1) por issue.
        - Una mutación batch por issue reduce roundtrips.
    """
    project_info = get_project_info(
        gh, project_number=project_number, project_owner=project_owner
    )
    start = time.time()
    for idx, issue in enumerate(issues, start=1):
        try:
            sync_issue(
                gh=gh,
                project_info=project_info,
                issue_number=issue,
                impact=impact,
                fuente=fuente,
                sprint=sprint,
                status=status,
                owner=owner,
                dqc_status=dqc_status,
                kpi_objetivo=kpi_objetivo,
                skip_add=skip_add,
            )
        except Exception as exc:
            logger.error("Error en issue #%s: %s", issue, exc, exc_info=True)
        if idx < len(issues):
            time.sleep(rate_limit_delay)
    duration = time.time() - start
    if issues:
        logger.info(
            "Tiempo total: %.2fs (%.2fs por issue)",
            duration,
            duration / len(issues),
        )


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Sincroniza issues con GitHub Projects v2 (versión optimizada)"
    )
    parser.add_argument(
        "--issues",
        nargs="+",
        type=int,
        required=True,
        help="Lista de números de issue a procesar",
    )
    parser.add_argument("--impact", help="Impacto (High, Medium, Low, Critical)")
    parser.add_argument(
        "--fuente",
        help="Fuente de datos (IDESCAT, Incasòl, OpenData BCN, Portal Dades, Internal)",
    )
    parser.add_argument("--sprint", help='Sprint (ej: "Sprint 1 (Idescat)")')
    parser.add_argument(
        "--status",
        help="Status (Backlog, Ready, In Progress, Review/QA, Blocked..., Done)",
    )
    parser.add_argument(
        "--owner",
        help="Owner (Data Engineering, Data Analysis, Product, Infraestructure)",
    )
    parser.add_argument(
        "--kpi-objetivo",
        dest="kpi_objetivo",
        help="Descripción del KPI objetivo",
    )
    parser.add_argument(
        "--dqc-status",
        choices=["Passed", "Failed", "Pending", "N/A"],
        help="Estado DQC",
    )
    parser.add_argument(
        "--project-number",
        type=int,
        default=int(os.environ.get("PROJECT_NUMBER", "7")),
        help="Número del proyecto (default: env PROJECT_NUMBER o 7)",
    )
    parser.add_argument(
        "--project-owner",
        type=str,
        default=None,
        help=f"Owner del proyecto (default: {PROJECT_OWNER})",
    )
    parser.add_argument(
        "--skip-add",
        action="store_true",
        help="No intentar añadir el issue si no existe en el proyecto",
    )
    parser.add_argument(
        "--rate-limit-delay",
        type=float,
        default=0.1,
        help="Delay entre issues (segundos)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Habilita logging DEBUG",
    )
    return parser.parse_args()


def main() -> None:
    """Punto de entrada CLI."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN no encontrado en variables de entorno")

    gh = GitHubGraphQL(token=token)
    sync_issues_batch(
        gh=gh,
        issues=args.issues,
        project_number=args.project_number,
        project_owner=args.project_owner,
        impact=args.impact,
        fuente=args.fuente,
        sprint=args.sprint,
        status=args.status,
        owner=args.owner,
        dqc_status=args.dqc_status,
        kpi_objetivo=args.kpi_objetivo,
        skip_add=args.skip_add,
        rate_limit_delay=args.rate_limit_delay,
    )


if __name__ == "__main__":
    main()
