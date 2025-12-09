#!/usr/bin/env python3
"""
Módulo helper para GitHub GraphQL API.

Ventajas sobre REST API:
- Consultas más eficientes (una sola petición para múltiples datos)
- Soporte nativo para Projects v2
- Menos rate limiting (5000 puntos/hora vs 5000 requests/hora)
- Consultas complejas con filtros avanzados
- Menor latencia (menos round-trips)

Uso:
    from scripts.github_graphql import GitHubGraphQL
    
    gh = GitHubGraphQL(token="ghp_xxx")
    
    # Obtener issues con labels y milestone en una sola query
    issues = gh.get_issues_with_details(state="OPEN", labels=["bug", "enhancement"])
    
    # Obtener datos de Projects v2
    project = gh.get_project_v2(project_number=1)
    items = gh.get_project_items(project_id=project["id"])
"""

import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

# Configuración
GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitHubGraphQL:
    """
    Cliente para GitHub GraphQL API.
    
    Proporciona métodos de alto nivel para consultas comunes y acceso
    directo a GraphQL para consultas personalizadas.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Inicializa el cliente GraphQL.
        
        Args:
            token: Token de GitHub. Si no se proporciona, intenta obtenerlo
                   de GITHUB_TOKEN o gh CLI.
        """
        self.token = token or self._get_token()
        if not self.token:
            raise ValueError(
                "No se pudo obtener token de GitHub. "
                "Configura GITHUB_TOKEN o autentica con 'gh auth login'"
            )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
    
    def _get_token(self) -> Optional[str]:
        """Obtiene token de GITHUB_TOKEN o gh CLI."""
        token = os.getenv("GITHUB_TOKEN")
        if token:
            return token
        
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta una query GraphQL.
        
        Args:
            query: Query GraphQL como string.
            variables: Variables para la query.
        
        Returns:
            Respuesta JSON de la API.
        
        Raises:
            RuntimeError: Si la query falla.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                GITHUB_GRAPHQL_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar errores de GraphQL
            if "errors" in data:
                error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
                raise RuntimeError(f"GraphQL errors: {', '.join(error_messages)}")
            
            # Verificar rate limiting
            if "rateLimit" in data.get("data", {}):
                rate_limit = data["data"]["rateLimit"]
                remaining = rate_limit.get("remaining", 0)
                logger.debug(
                    "Rate limit: %d/%d remaining (resets at %s)",
                    remaining,
                    rate_limit.get("limit", 5000),
                    rate_limit.get("resetAt", "unknown")
                )
            
            return data.get("data", {})
        
        except requests.RequestException as e:
            logger.error(f"Error en petición GraphQL: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Respuesta: {e.response.text}")
            raise RuntimeError(f"GitHub GraphQL API error: {e}")
    
    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Obtiene información básica del repositorio.
        
        Args:
            owner: Propietario del repositorio.
            repo: Nombre del repositorio.
        
        Returns:
            Dict con información del repositorio.
        """
        query = """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                id
                name
                description
                url
                createdAt
                updatedAt
                isPrivate
                stargazerCount
                forkCount
                defaultBranchRef {
                    name
                }
                languages(first: 10) {
                    edges {
                        node {
                            name
                        }
                        size
                    }
                }
            }
        }
        """
        
        variables = {"owner": owner, "repo": repo}
        data = self.execute_query(query, variables)
        return data.get("repository", {})
    
    def get_issues_with_details(
        self,
        owner: str,
        repo: str,
        state: str = "OPEN",
        labels: Optional[List[str]] = None,
        milestone: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene issues con detalles completos (labels, milestone, assignees, etc.)
        en una sola consulta.
        
        Args:
            owner: Propietario del repositorio.
            repo: Nombre del repositorio.
            state: Estado de las issues (OPEN, CLOSED).
            labels: Lista de labels a filtrar (opcional).
            milestone: Título del milestone a filtrar (opcional).
            limit: Número máximo de issues (máx 100 por página).
            cursor: Cursor para paginación (opcional).
        
        Returns:
            Dict con 'issues' (lista) y 'pageInfo' (paginación).
        """
        if labels:
            label_list = ", ".join([f'"{l}"' for l in labels])
            label_filter = f'labels: [{label_list}]'
        else:
            label_filter = ""
        milestone_filter = f'milestone: "{milestone}"' if milestone else ""
        
        query = f"""
        query($owner: String!, $repo: String!, $limit: Int!, $cursor: String) {{
            repository(owner: $owner, name: $repo) {{
                issues(
                    states: {state}
                    first: $limit
                    after: $cursor
                    {label_filter}
                    {milestone_filter}
                    orderBy: {{field: UPDATED_AT, direction: DESC}}
                ) {{
                    totalCount
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                    nodes {{
                        number
                        title
                        body
                        state
                        createdAt
                        updatedAt
                        closedAt
                        url
                        author {{
                            login
                        }}
                        labels(first: 20) {{
                            nodes {{
                                name
                                color
                                description
                            }}
                        }}
                        milestone {{
                            title
                            number
                            dueOn
                        }}
                        assignees(first: 10) {{
                            nodes {{
                                login
                                name
                            }}
                        }}
                        comments {{
                            totalCount
                        }}
                        reactions {{
                            totalCount
                        }}
                    }}
                }}
            }}
        }}
        """
        
        variables = {
            "owner": owner,
            "repo": repo,
            "limit": min(limit, 100),
            "cursor": cursor
        }
        
        data = self.execute_query(query, variables)
        repository = data.get("repository", {})
        issues_data = repository.get("issues", {})
        
        return {
            "issues": issues_data.get("nodes", []),
            "totalCount": issues_data.get("totalCount", 0),
            "pageInfo": issues_data.get("pageInfo", {})
        }
    
    def get_project_v2(self, owner: str, repo: str, project_number: int) -> Dict[str, Any]:
        """
        Obtiene información de un Project v2 asociado a un repositorio.
        """
        query = """
        query($owner: String!, $repo: String!, $projectNumber: Int!) {
            repository(owner: $owner, name: $repo) {
                projectV2(number: $projectNumber) {
                    id
                    title
                    number
                    url
                    shortDescription
                    public
                    closed
                    createdAt
                    updatedAt
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                                dataType
                            }
                            ... on ProjectV2IterationField {
                                id
                                name
                                configuration {
                                    iterations {
                                        id
                                        title
                                        startDate
                                        duration
                                    }
                                }
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "owner": owner,
            "repo": repo,
            "projectNumber": project_number
        }
        
        data = self.execute_query(query, variables)
        repository = data.get("repository", {})
        return repository.get("projectV2", {})

    def get_project_v2_any(
        self,
        owner: str,
        repo: str,
        project_owner: str,
        project_number: int
    ) -> Dict[str, Any]:
        """
        Obtiene información de un Project v2 intentando en este orden:
        1) Proyecto de repositorio
        2) Proyecto de usuario (user login)
        3) Proyecto de organización
        """
        # 1. Proyecto de repositorio
        try:
            project = self.get_project_v2(owner=owner, repo=repo, project_number=project_number)
            if project:
                return project
        except Exception:
            # Continuar con siguientes intentos
            pass

        # 2. Proyecto de usuario
        query_user = """
        query($owner: String!, $projectNumber: Int!) {
            user(login: $owner) {
                projectV2(number: $projectNumber) {
                    id
                    title
                    number
                    url
                    shortDescription
                    public
                    closed
                    createdAt
                    updatedAt
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                                dataType
                            }
                            ... on ProjectV2IterationField {
                                id
                                name
                                configuration {
                                    iterations {
                                        id
                                        title
                                        startDate
                                        duration
                                    }
                                }
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        try:
            data = self.execute_query(query_user, {"owner": project_owner, "projectNumber": project_number})
            user_node = data.get("user", {})
            if user_node and user_node.get("projectV2"):
                return user_node.get("projectV2", {})
        except Exception:
            pass

        # 3. Proyecto de organización
        query_org = """
        query($owner: String!, $projectNumber: Int!) {
            organization(login: $owner) {
                projectV2(number: $projectNumber) {
                    id
                    title
                    number
                    url
                    shortDescription
                    public
                    closed
                    createdAt
                    updatedAt
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                                dataType
                            }
                            ... on ProjectV2IterationField {
                                id
                                name
                                configuration {
                                    iterations {
                                        id
                                        title
                                        startDate
                                        duration
                                    }
                                }
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        try:
            data = self.execute_query(query_org, {"owner": project_owner, "projectNumber": project_number})
            org_node = data.get("organization", {})
            if org_node and org_node.get("projectV2"):
                return org_node.get("projectV2", {})
        except Exception:
            pass

        return {}
    
    def get_project_items(
        self,
        project_id: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene items de un Project v2.
        
        Args:
            project_id: ID del proyecto (obtenido de get_project_v2).
            limit: Número máximo de items (máx 100 por página).
            cursor: Cursor para paginación (opcional).
        
        Returns:
            Dict con 'items' (lista) y 'pageInfo' (paginación).
        """
        query = """
        query($projectId: ID!, $limit: Int!, $cursor: String) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    items(first: $limit, after: $cursor) {
                        totalCount
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
                            id
                            type
                            fieldValues(first: 20) {
                                nodes {
                                    ... on ProjectV2ItemFieldTextValue {
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                        text
                                    }
                                    ... on ProjectV2ItemFieldNumberValue {
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                        number
                                    }
                                    ... on ProjectV2ItemFieldDateValue {
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                        date
                                    }
                                    ... on ProjectV2ItemFieldSingleSelectValue {
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                        name
                                    }
                                    ... on ProjectV2ItemFieldIterationValue {
                                        field {
                                            ... on ProjectV2FieldCommon {
                                                name
                                            }
                                        }
                                        title
                                    }
                                }
                            }
                            content {
                                ... on Issue {
                                    number
                                    title
                                    state
                                    url
                                }
                                ... on PullRequest {
                                    number
                                    title
                                    state
                                    url
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "projectId": project_id,
            "limit": min(limit, 100),
            "cursor": cursor
        }
        
        data = self.execute_query(query, variables)
        node = data.get("node", {})
        items_data = node.get("items", {})
        
        return {
            "items": items_data.get("nodes", []),
            "totalCount": items_data.get("totalCount", 0),
            "pageInfo": items_data.get("pageInfo", {})
        }
    
    def get_all_issues_paginated(
        self,
        owner: str,
        repo: str,
        state: str = "OPEN",
        labels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las issues (con paginación automática).
        
        Args:
            owner: Propietario del repositorio.
            repo: Nombre del repositorio.
            state: Estado de las issues.
            labels: Lista de labels a filtrar (opcional).
        
        Returns:
            Lista completa de issues.
        """
        all_issues = []
        cursor = None
        
        while True:
            result = self.get_issues_with_details(
                owner=owner,
                repo=repo,
                state=state,
                labels=labels,
                limit=100,
                cursor=cursor
            )
            
            all_issues.extend(result["issues"])
            
            page_info = result.get("pageInfo", {})
            if not page_info.get("hasNextPage", False):
                break
            
            cursor = page_info.get("endCursor")
            logger.info(f"Obtenidas {len(all_issues)}/{result['totalCount']} issues...")
        
        logger.info(f"Total de issues obtenidas: {len(all_issues)}")
        return all_issues


# ==============================================================================
# FUNCIONES DE CONVENIENCIA
# ==============================================================================

def get_repo_owner_and_name() -> Tuple[str, str]:
    """
    Obtiene owner y repo del repositorio actual usando git.
    
    Returns:
        Tuple (owner, repo).
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        url = result.stdout.strip()
        
        # Parsear URL (git@github.com:owner/repo.git o https://github.com/owner/repo.git)
        if "github.com" in url:
            parts = url.split("github.com")[-1].strip("/").replace(".git", "").split("/")
            if len(parts) >= 2:
                return parts[-2], parts[-1]
        
        raise ValueError("No se pudo parsear la URL del repositorio")
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.warning(f"No se pudo obtener owner/repo del git: {e}")
        return "prototyp33", "barcelona-housing-demographics-analyzer"


if __name__ == "__main__":
    # Ejemplo de uso
    import argparse
    
    parser = argparse.ArgumentParser(description="Ejemplo de uso de GitHub GraphQL API")
    parser.add_argument("--owner", default="prototyp33", help="Owner del repositorio")
    parser.add_argument("--repo", default="barcelona-housing-demographics-analyzer", help="Nombre del repo")
    parser.add_argument("--state", choices=["OPEN", "CLOSED"], default="OPEN", help="Estado de issues")
    parser.add_argument("--labels", nargs="+", help="Labels a filtrar")
    
    args = parser.parse_args()
    
    gh = GitHubGraphQL()
    
    print(f"📊 Obteniendo issues de {args.owner}/{args.repo}...")
    issues = gh.get_all_issues_paginated(
        owner=args.owner,
        repo=args.repo,
        state=args.state,
        labels=args.labels
    )
    
    print(f"\n✅ {len(issues)} issues encontradas\n")
    
    for issue in issues[:10]:  # Mostrar primeras 10
        labels = [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
        print(f"#{issue['number']}: {issue['title']}")
        if labels:
            print(f"  Labels: {', '.join(labels)}")
        print()

