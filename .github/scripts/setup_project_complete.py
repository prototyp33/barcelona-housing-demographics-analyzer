#!/usr/bin/env python3
"""
🚀 Setup Maestro de Proyecto GitHub (Versión Producción)
Barcelona Housing Demographics Analyzer

Características:
- Auto-detección inteligente (SSH/HTTPS)
- Idempotencia (No duplica recursos)
- Automatización Project V2 vía GraphQL
- Soporte Híbrido (User/Org)

Uso:
    export GITHUB_TOKEN="ghp_xxx"
    python .github/scripts/setup_project_complete.py
    python .github/scripts/setup_project_complete.py --project-number 2 --no-auto-fields
"""

import os
import sys
import subprocess
import argparse
import requests
import time
from typing import List, Dict, Optional, Tuple

try:
    from github import Github, GithubException
except ImportError:
    print("❌ Error: PyGithub no está instalado")
    print("   Ejecuta: pip install PyGithub requests")
    sys.exit(1)

# =============================================================================
# 1. CONFIGURACIÓN Y AUTO-DETECCIÓN
# =============================================================================

def detect_git_context() -> Tuple[str, str]:
    """
    Detecta owner y repo analizando el remote 'origin' de git.
    Soporta SSH y HTTPS.
    """
    try:
        # Obtiene URL: git@github.com:User/Repo.git o https://github.com/User/Repo.git
        url = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        clean_url = url.replace(".git", "").replace("git@github.com:", "").replace("https://github.com/", "")
        
        if "/" in clean_url:
            parts = clean_url.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    
    return "prototyp33", "barcelona-housing-demographics-analyzer"

DETECTED_OWNER, DETECTED_REPO = detect_git_context()

# Configuración de Argumentos CLI
parser = argparse.ArgumentParser(
    description='Setup Automatizado de Repositorio GitHub',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Ejemplos:
  # Uso básico (auto-detecta desde git)
  python .github/scripts/setup_project_complete.py

  # Configuración manual
  python .github/scripts/setup_project_complete.py --owner prototyp33 --repo mi-repo --project-number 2

  # Sin crear campos automáticamente
  python .github/scripts/setup_project_complete.py --no-auto-fields
    """
)

parser.add_argument(
    '--owner',
    default=os.environ.get("REPO_OWNER", DETECTED_OWNER),
    help='Dueño del repositorio (default: auto-detectado)'
)
parser.add_argument(
    '--repo',
    default=os.environ.get("REPO_NAME", DETECTED_REPO),
    help='Nombre del repositorio (default: auto-detectado)'
)
parser.add_argument(
    '--project-number',
    type=int,
    default=int(os.environ.get("PROJECT_NUMBER", "1")),
    help='Número del Project V2 (default: 1)'
)
parser.add_argument(
    '--token',
    default=os.environ.get("GITHUB_TOKEN"),
    help='Personal Access Token (PAT) (default: GITHUB_TOKEN env var)'
)
parser.add_argument(
    '--no-auto-fields',
    action='store_true',
    help='Saltar configuración automática de campos'
)

args = parser.parse_args()

if not args.token:
    print("❌ Error CRÍTICO: No se encontró GITHUB_TOKEN.")
    print("   -> Exportalo en tu terminal: export GITHUB_TOKEN='ghp_...'")
    print("   -> O usa el argumento: --token 'ghp_...'")
    sys.exit(1)

GRAPHQL_URL = "https://api.github.com/graphql"

# =============================================================================
# 2. DEFINICIÓN DE METADATOS
# =============================================================================

LABELS_CONFIG = [
    # Tipos básicos
    {"name": "bug", "color": "d73a4a", "description": "Algo no funciona correctamente"},
    {"name": "feature", "color": "0e8a16", "description": "Nueva funcionalidad"},
    {"name": "enhancement", "color": "a2eeef", "description": "Mejora de funcionalidad existente"},
    {"name": "documentation", "color": "0075ca", "description": "Mejoras en documentación"},
    {"name": "task", "color": "d4c5f9", "description": "Tarea general"},
    
    # Dominios técnicos
    {"name": "data-extraction", "color": "fbca04", "description": "Pipelines y ETL"},
    {"name": "data-processing", "color": "fbca04", "description": "Procesamiento y limpieza"},
    {"name": "data-quality", "color": "fbca04", "description": "Validación y DQC"},
    {"name": "etl", "color": "fbca04", "description": "Pipeline ETL"},
    {"name": "database", "color": "006b75", "description": "Esquema y queries"},
    {"name": "analysis", "color": "c2e0c6", "description": "Análisis exploratorio"},
    {"name": "dashboard", "color": "1d76db", "description": "Streamlit / Viz"},
    {"name": "testing", "color": "0e8a16", "description": "Tests y QA"},
    {"name": "automation", "color": "5319e7", "description": "Automatización"},
    
    # Fuentes de datos
    {"name": "idescat", "color": "fef2c0", "description": "Fuente: IDESCAT"},
    {"name": "incasl", "color": "fef2c0", "description": "Fuente: Incasòl"},
    {"name": "opendatabcn", "color": "fef2c0", "description": "Fuente: Open Data BCN"},
    {"name": "portal-dades", "color": "fef2c0", "description": "Fuente: Portal de Dades"},
    
    # Prioridad
    {"name": "priority-high", "color": "b60205", "description": "Alta prioridad (Bloqueante)"},
    {"name": "priority-medium", "color": "fbca04", "description": "Prioridad media"},
    {"name": "priority-low", "color": "0e8a16", "description": "Prioridad baja"},
    
    # Estado
    {"name": "in-progress", "color": "c5def5", "description": "En progreso"},
    {"name": "needs-review", "color": "fbca04", "description": "Requiere revisión"},
    {"name": "blocked", "color": "d93f0b", "description": "Bloqueado"},
    
    # Sprints
    {"name": "sprint-0", "color": "e99695", "description": "Sprint 0: Setup"},
    {"name": "sprint-1", "color": "f9d0c4", "description": "Sprint 1: IDESCAT"},
    {"name": "sprint-2", "color": "c2e0c6", "description": "Sprint 2: Renta"},
    {"name": "sprint-3", "color": "bfdadc", "description": "Sprint 3: Incasòl"},
    {"name": "sprint-4", "color": "d4c5f9", "description": "Sprint 4: Precios"},
    
    # Roadmap
    {"name": "roadmap", "color": "5319e7", "description": "Hito clave del Roadmap"},
    
    # Especiales
    {"name": "good-first-issue", "color": "7057ff", "description": "Bueno para nuevos contribuidores"},
    {"name": "help-wanted", "color": "008672", "description": "Se busca ayuda"},
]

MILESTONES_CONFIG = [
    {
        "title": "Sprint 0: Foundation & Setup",
        "description": "Infraestructura base del proyecto",
        "due_on": "2026-01-15"
    },
    {
        "title": "Sprint 1: IDESCAT Integration",
        "description": "Integración datos renta IDESCAT",
        "due_on": "2026-01-31"
    },
    {
        "title": "Sprint 2: Income Pipeline",
        "description": "Pipeline histórico renta",
        "due_on": "2026-02-15"
    },
    {
        "title": "Sprint 3: Incasòl Integration",
        "description": "Oferta vivienda protegida",
        "due_on": "2026-02-28"
    },
    {
        "title": "Sprint 4: Market Prices",
        "description": "Precios de mercado",
        "due_on": "2026-03-15"
    },
    {
        "title": "Dashboard & Visualization",
        "description": "Dashboard interactivo completo",
        "due_on": "2026-04-15"
    },
    {
        "title": "Testing & Documentation",
        "description": "Asegurar calidad y preparar release",
        "due_on": "2026-04-30"
    }
]

# =============================================================================
# 3. UTILIDADES CORE
# =============================================================================

def graphql_request(query: str, variables: Dict = None) -> Dict:
    """
    Ejecuta queries de GraphQL manejando errores básicos.
    
    Args:
        query: Query GraphQL como string
        variables: Variables para la query
    
    Returns:
        Respuesta JSON de la API o dict vacío en caso de error
    """
    headers = {
        "Authorization": f"Bearer {args.token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables or {}},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # Verificar errores de GraphQL
        if "errors" in data:
            error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
            # Solo mostrar si no es "already exists" (esperado en algunos casos)
            if not any("already exists" in msg.lower() for msg in error_messages):
                print(f"   ⚠️  GraphQL errors: {', '.join(error_messages)}")
        
        return data
    except requests.Timeout:
        print(f"   ⚠️  Timeout en GraphQL request")
        return {}
    except requests.RequestException as e:
        print(f"   ⚠️  Error de red en GraphQL: {e}")
        return {}
    except Exception as e:
        print(f"   ⚠️  Error inesperado en GraphQL: {e}")
        return {}

def setup_repo_metadata(repo):
    """
    Configura Labels y Milestones de forma idempotente.
    
    Args:
        repo: Repositorio de GitHub
    """
    print(f"\n🏷️  SINCRONIZANDO METADATOS ({repo.full_name})...")
    
    # Labels
    existing_labels = {l.name: l for l in repo.get_labels()}
    count_created = 0
    count_updated = 0
    
    for cfg in LABELS_CONFIG:
        try:
            if cfg["name"] in existing_labels:
                # Opcional: Descomentar para forzar actualización de colores
                # existing_labels[cfg["name"]].edit(color=cfg["color"], description=cfg.get("description", ""))
                count_updated += 1
            else:
                repo.create_label(
                    name=cfg["name"],
                    color=cfg["color"],
                    description=cfg.get("description", "")
                )
                count_created += 1
                time.sleep(0.3)  # Rate limiting
        except GithubException as e:
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            print(f"   ⚠️  Error con label '{cfg['name']}': {error_msg}")
        except Exception as e:
            print(f"   ⚠️  Error inesperado con label '{cfg['name']}': {e}")
    
    print(f"   ✓ Labels: {count_created} creados, {count_updated} verificados.")
    
    # Milestones
    existing_ms = {m.title: m for m in repo.get_milestones(state="all")}
    ms_created = 0
    
    for cfg in MILESTONES_CONFIG:
        try:
            if cfg["title"] not in existing_ms:
                repo.create_milestone(
                    title=cfg["title"],
                    description=cfg["description"],
                    due_on=cfg.get("due_on")
                )
                ms_created += 1
                time.sleep(0.3)  # Rate limiting
        except GithubException as e:
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            print(f"   ⚠️  Error con milestone '{cfg['title']}': {error_msg}")
        except Exception as e:
            print(f"   ⚠️  Error inesperado con milestone '{cfg['title']}': {e}")
    
    print(f"   ✓ Milestones: {ms_created} nuevos creados.")

# =============================================================================
# 4. GESTIÓN DE PROJECT V2 (GRAPHQL)
# =============================================================================

def get_project_node_id(owner: str, number: int) -> Optional[str]:
    """
    Obtiene el Node ID del proyecto (User u Org).
    
    Args:
        owner: Owner del proyecto
        number: Número del proyecto
    
    Returns:
        Node ID del proyecto o None si no se encuentra
    """
    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) {
          id
          title
        }
      }
      organization(login: $owner) {
        projectV2(number: $number) {
          id
          title
        }
      }
    }
    """
    
    data = graphql_request(query, {"owner": owner, "number": number})
    
    if not data or "data" not in data:
        return None
    
    data_node = data.get("data", {})
    
    # Intentar User
    user_node = data_node.get("user")
    if user_node and user_node.get("projectV2"):
        project = user_node["projectV2"]
        if project and project.get("id"):
            print(f"   ✓ Proyecto encontrado (User): {project.get('title', 'Unknown')}")
            return project["id"]
    
    # Intentar Org
    org_node = data_node.get("organization")
    if org_node and org_node.get("projectV2"):
        project = org_node["projectV2"]
        if project and project.get("id"):
            print(f"   ✓ Proyecto encontrado (Organization): {project.get('title', 'Unknown')}")
            return project["id"]
    
    return None

def create_project_field(project_id: str, name: str, data_type: str, options: List[Dict] = None):
    """
    Crea un campo personalizado en el Proyecto V2.
    
    Args:
        project_id: ID del proyecto
        name: Nombre del campo
        data_type: Tipo de campo (SINGLE_SELECT, TEXT, NUMBER)
        options: Lista de opciones para SINGLE_SELECT (formato: [{"name": "...", "color": "..."}])
    """
    mutation = """
    mutation($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
      createProjectV2Field(input: {
        projectId: $projectId
        name: $name
        dataType: $dataType
        singleSelectOptions: $options
      }) {
        projectV2Field {
          ... on ProjectV2Field {
            id
            name
          }
        }
      }
    }
    """
    
    variables = {
        "projectId": project_id,
        "name": name,
        "dataType": data_type,
        "options": options if options else None
    }
    
    res = graphql_request(mutation, variables)
    
    if not res:
        print(f"   ❌ Error: No se pudo conectar con GraphQL para crear '{name}'")
        return
    
    # Verificar errores
    if "errors" in res:
        err_msg = res["errors"][0].get("message", "Unknown error")
        if "already exists" in err_msg.lower() or "duplicate" in err_msg.lower():
            print(f"   ℹ️  Campo '{name}' ya existe.")
        else:
            print(f"   ❌ Error creando '{name}': {err_msg}")
        return
    
    # Verificar respuesta exitosa
    data = res.get("data", {})
    if not data:
        print(f"   ⚠️  Respuesta vacía al crear '{name}'")
        return
    
    field_data = data.get("createProjectV2Field", {}).get("projectV2Field", {})
    if field_data and field_data.get("id"):
        print(f"   ✅ Campo creado: {name}")
    else:
        print(f"   ⚠️  Campo '{name}' no se creó correctamente (verificar permisos)")

def setup_project_v2_structure(project_id: str):
    """
    Orquesta la creación de campos del proyecto.
    
    Args:
        project_id: ID del proyecto
    """
    print(f"\n🏗️  CONFIGURANDO ESTRUCTURA PROJECT V2 (ID: {project_id[:20]}...)...")
    
    # Campos Single Select con colores
    create_project_field(project_id, "Impacto", "SINGLE_SELECT", [
        {"name": "High", "color": "RED"},
        {"name": "Medium", "color": "YELLOW"},
        {"name": "Low", "color": "GRAY"}
    ])
    time.sleep(0.5)  # Rate limiting
    
    create_project_field(project_id, "Fuente de Datos", "SINGLE_SELECT", [
        {"name": "IDESCAT", "color": "BLUE"},
        {"name": "Incasòl", "color": "ORANGE"},
        {"name": "OpenData BCN", "color": "PURPLE"},
        {"name": "Portal Dades", "color": "ORANGE"},
        {"name": "Internal", "color": "GRAY"}
    ])
    time.sleep(0.5)
    
    create_project_field(project_id, "Estado DQC", "SINGLE_SELECT", [
        {"name": "Passed", "color": "GREEN"},
        {"name": "Failed", "color": "RED"},
        {"name": "Pending", "color": "GRAY"}
    ])
    time.sleep(0.5)
    
    # Campos de Texto/Número
    create_project_field(project_id, "KPI Objetivo", "TEXT")
    time.sleep(0.5)
    
    create_project_field(project_id, "Confidence", "NUMBER")
    time.sleep(0.5)
    
    create_project_field(project_id, "Owner", "TEXT")

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Función principal del setup."""
    print("="*60)
    print(f"🚀 INICIANDO SETUP: {args.owner}/{args.repo}")
    print("="*60)
    
    # 1. Conexión a GitHub
    try:
        gh = Github(args.token)
        # Verificar que el token es válido
        user = gh.get_user()
        print(f"✅ Conexión establecida con GitHub")
        print(f"   👤 Usuario: {user.login}")
    except GithubException as e:
        error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
        print(f"❌ Error: Token inválido o sin permisos.")
        print(f"   Detalle: {error_msg}")
        print("   Verifica que el token tenga permisos: repo, project")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado conectando a GitHub: {e}")
        sys.exit(1)
    
    # 2. Verificar acceso al repositorio
    try:
        repo = gh.get_repo(f"{args.owner}/{args.repo}")
        print(f"   📦 Repositorio: {repo.full_name}")
    except GithubException as e:
        error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
        print(f"❌ Error: No se puede acceder a {args.owner}/{args.repo}.")
        print(f"   Detalle: {error_msg}")
        print("   Verifica que el repositorio exista y tengas permisos.")
        sys.exit(1)
    
    # 3. Configurar Repo (REST API)
    setup_repo_metadata(repo)
    
    # 4. Configurar Proyecto (GraphQL)
    if not args.no_auto_fields:
        project_id = get_project_node_id(args.owner, args.project_number)
        if project_id:
            setup_project_v2_structure(project_id)
        else:
            print(f"\n⚠️  Aviso: No se encontró el Project #{args.project_number}.")
            print(f"   -> Crea un proyecto vacío en: https://github.com/users/{args.owner}/projects/new")
            print("   -> Y vuelve a ejecutar este script.")
    else:
        print("\n⏭️  Modo --no-auto-fields: saltando configuración de campos.")
        print(f"   Configura manualmente en: https://github.com/users/{args.owner}/projects/{args.project_number}/settings")
    
    # Resumen final
    print("\n" + "="*60)
    print("✨ SETUP COMPLETADO EXITOSAMENTE")
    print("="*60)
    print("\n📝 Siguientes pasos manuales:")
    print("   1. Configura el campo 'Iteration' (Sprints) en la configuración del Proyecto.")
    print("   2. Crea las Vistas (Views) para visualizar el Tablero y el Roadmap.")
    print("   3. Activa las automatizaciones built-in del proyecto.")
    print("\n💡 Próximo paso automatizado:")
    print("   python .github/scripts/create_sprint_issues.py")

if __name__ == "__main__":
    main()
