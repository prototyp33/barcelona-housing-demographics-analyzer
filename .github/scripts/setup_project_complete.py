#!/usr/bin/env python3
"""
Setup completo del proyecto GitHub con mejores prácticas (Versión Mejorada)
Barcelona Housing Demographics Analyzer

Mejoras:
- Automatización de creación de campos en ProjectV2 (GraphQL Mutations)
- Detección automática de Org vs User
- Manejo robusto de errores
- Detección automática de owner/repo desde git

Configura:
- Labels
- Milestones
- Project v2 (campos personalizados)
- Automatizaciones
- Vistas del proyecto

Uso:
    export GITHUB_TOKEN="tu_token"
    python .github/scripts/setup_project_complete.py
    python .github/scripts/setup_project_complete.py --project-number 2
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# Añadir el directorio raíz al path para imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from github import Github, GithubException
    import requests
except ImportError:
    print("❌ Error: Dependencias no instaladas")
    print("   Ejecuta: pip install PyGithub requests")
    sys.exit(1)

# =============================================================================
# DETECCIÓN AUTOMÁTICA DE CONFIGURACIÓN
# =============================================================================

def detect_git_config() -> tuple[str, str]:
    """Detecta owner y repo desde git config."""
    try:
        git_remote = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        if "github.com" in git_remote:
            # Formato ssh: git@github.com:owner/repo.git
            # Formato https: https://github.com/owner/repo.git
            parts = git_remote.replace(".git", "").split("/")[-2:]
            if ":" in parts[0]:
                parts[0] = parts[0].split(":")[-1]
            return parts[0], parts[1]
    except Exception:
        pass
    
    # Valores por defecto
    return "prototyp33", "barcelona-housing-demographics-analyzer"

DETECTED_OWNER, DETECTED_REPO = detect_git_config()

# Configuración (con detección automática)
REPO_OWNER = os.environ.get("REPO_OWNER", DETECTED_OWNER)
REPO_NAME = os.environ.get("REPO_NAME", DETECTED_REPO)
ORG_NAME = REPO_OWNER
PROJECT_NUMBER = int(os.environ.get("PROJECT_NUMBER", "1"))

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN no encontrado en variables de entorno")
    print("   Ejecuta: export GITHUB_TOKEN='tu_token'")
    sys.exit(1)

GRAPHQL_URL = "https://api.github.com/graphql"

# =============================================================================
# UTILIDADES GRAPHQL
# =============================================================================

def graphql_request(query: str, variables: Dict = None) -> Dict:
    """Ejecuta query GraphQL con manejo de errores."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
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
        
        if "errors" in data:
            error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
            print(f"⚠️  GraphQL Warnings/Errors: {', '.join(error_messages)}")
        
        return data
    except requests.RequestException as e:
        raise Exception(f"GraphQL Error ({getattr(e.response, 'status_code', 'unknown')}): {str(e)}")


# =============================================================================
# 1. CONFIGURACIÓN DE LABELS
# =============================================================================

LABELS_CONFIG = [
    # Tipos
    {"name": "bug", "color": "d73a4a", "description": "Algo no funciona correctamente"},
    {"name": "feature", "color": "0e8a16", "description": "Nueva funcionalidad"},
    {"name": "enhancement", "color": "a2eeef", "description": "Mejora de funcionalidad existente"},
    {"name": "documentation", "color": "0075ca", "description": "Mejoras en documentación"},
    {"name": "task", "color": "d4c5f9", "description": "Tarea general"},
    
    # Dominios técnicos
    {"name": "data-extraction", "color": "fbca04", "description": "Extracción de datos"},
    {"name": "data-processing", "color": "fbca04", "description": "Procesamiento y limpieza"},
    {"name": "data-quality", "color": "fbca04", "description": "Validación y DQC"},
    {"name": "etl", "color": "fbca04", "description": "Pipeline ETL"},
    {"name": "database", "color": "006b75", "description": "Esquema y queries"},
    {"name": "analysis", "color": "c2e0c6", "description": "Análisis de datos"},
    {"name": "dashboard", "color": "1d76db", "description": "Dashboard Streamlit"},
    {"name": "testing", "color": "0e8a16", "description": "Tests y QA"},
    {"name": "automation", "color": "5319e7", "description": "Automatización"},
    
    # Fuentes de datos
    {"name": "idescat", "color": "fef2c0", "description": "Fuente: IDESCAT"},
    {"name": "incasl", "color": "fef2c0", "description": "Fuente: Incasòl"},
    {"name": "opendatabcn", "color": "fef2c0", "description": "Fuente: Open Data BCN"},
    {"name": "portal-dades", "color": "fef2c0", "description": "Fuente: Portal de Dades"},
    
    # Prioridad
    {"name": "priority-high", "color": "b60205", "description": "Prioridad alta"},
    {"name": "priority-medium", "color": "fbca04", "description": "Prioridad media"},
    {"name": "priority-low", "color": "0e8a16", "description": "Prioridad baja"},
    
    # Estado
    {"name": "in-progress", "color": "c5def5", "description": "En progreso"},
    {"name": "needs-review", "color": "fbca04", "description": "Requiere revisión"},
    {"name": "blocked", "color": "d93f0b", "description": "Bloqueado"},
    
    # Sprint
    {"name": "sprint-0", "color": "e99695", "description": "Sprint 0: Setup"},
    {"name": "sprint-1", "color": "f9d0c4", "description": "Sprint 1: IDESCAT"},
    {"name": "sprint-2", "color": "c2e0c6", "description": "Sprint 2: Renta"},
    {"name": "sprint-3", "color": "bfdadc", "description": "Sprint 3: Incasòl"},
    {"name": "sprint-4", "color": "d4c5f9", "description": "Sprint 4: Precios"},
    
    # Roadmap
    {"name": "roadmap", "color": "5319e7", "description": "Parte del roadmap"},
    
    # Especiales
    {"name": "good-first-issue", "color": "7057ff", "description": "Bueno para nuevos contribuidores"},
    {"name": "help-wanted", "color": "008672", "description": "Se busca ayuda"},
    {"name": "wontfix", "color": "ffffff", "description": "No se implementará"},
    {"name": "duplicate", "color": "cfd3d7", "description": "Duplicado de otra issue"},
]


def setup_labels(repo):
    """Configura labels del repositorio"""
    print("\n" + "="*60)
    print("📋 CONFIGURANDO LABELS")
    print("="*60)
    
    existing_labels = {label.name: label for label in repo.get_labels()}
    created = 0
    updated = 0
    
    for label_config in LABELS_CONFIG:
        name = label_config["name"]
        
        try:
            if name in existing_labels:
                # Actualizar label existente
                label = existing_labels[name]
                label.edit(
                    name=name,
                    color=label_config["color"],
                    description=label_config.get("description", "")
                )
                print(f"  ✓ Actualizado: {name}")
                updated += 1
            else:
                # Crear nuevo label
                repo.create_label(
                    name=name,
                    color=label_config["color"],
                    description=label_config.get("description", "")
                )
                print(f"  ✓ Creado: {name}")
                created += 1
            time.sleep(0.5)  # Rate limiting
        except GithubException as e:
            print(f"  ⚠️  Error con {name}: {e.data.get('message', str(e))}")
        except Exception as e:
            print(f"  ⚠️  Error con {name}: {e}")
    
    print(f"\n✅ Labels: {created} creados, {updated} actualizados (total: {len(LABELS_CONFIG)})")


# =============================================================================
# 2. CONFIGURACIÓN DE MILESTONES
# =============================================================================

MILESTONES_CONFIG = [
    {
        "title": "Sprint 0: Foundation & Setup",
        "description": """**Objetivo:** Configurar infraestructura base del proyecto

**Entregables clave:**
- Esquema de base de datos SQLite
- Framework ETL básico
- Estructura de proyecto completa
- Sistema de logging

**Duración:** 2 semanas""",
        "due_on": "2026-01-15"
    },
    {
        "title": "Sprint 1: IDESCAT Integration",
        "description": """**Objetivo:** Integrar datos de renta desde IDESCAT/Open Data BCN

**Entregables clave:**
- IDESCATExtractor funcional
- Datos de renta 2015-2023 (≥80% cobertura)
- Tests completos
- Documentación

**Duración:** 2 semanas""",
        "due_on": "2026-01-31"
    },
    {
        "title": "Sprint 2: Income Pipeline",
        "description": """**Objetivo:** Pipeline completo de renta histórica

**Entregables clave:**
- Tabla fact_renta_hist poblada
- ETL automatizado
- Validación DQC (≥95% completitud)

**Duración:** 2 semanas""",
        "due_on": "2026-02-15"
    },
    {
        "title": "Sprint 3: Incasòl Integration",
        "description": """**Objetivo:** Integrar oferta de vivienda protegida

**Entregables clave:**
- IncasolExtractor funcional
- Datos de oferta inmobiliaria
- Integración con dim_barrios

**Duración:** 2 semanas""",
        "due_on": "2026-02-28"
    },
    {
        "title": "Sprint 4: Market Prices",
        "description": """**Objetivo:** Completar datos de precios de mercado

**Entregables clave:**
- fact_precios actualizada
- Indicadores de asequibilidad
- Dashboard Market Cockpit v1

**Duración:** 2 semanas""",
        "due_on": "2026-03-15"
    },
    {
        "title": "Dashboard & Visualization",
        "description": """**Objetivo:** Dashboard interactivo completo

**Entregables clave:**
- Streamlit app funcional
- Mapas interactivos
- Filtros por barrio/distrito
- Visualizaciones de correlaciones

**Duración:** 3-4 semanas""",
        "due_on": "2026-04-15"
    },
    {
        "title": "Testing & Documentation",
        "description": """**Objetivo:** Asegurar calidad y preparar release

**Entregables clave:**
- Cobertura de tests ≥80%
- Documentación completa
- Guías de usuario
- CI/CD completo

**Duración:** 2 semanas""",
        "due_on": "2026-04-30"
    }
]


def setup_milestones(repo):
    """Configura milestones del repositorio"""
    print("\n" + "="*60)
    print("🎯 CONFIGURANDO MILESTONES")
    print("="*60)
    
    existing_milestones = {ms.title: ms for ms in repo.get_milestones(state="all")}
    created = 0
    updated = 0
    
    for ms_config in MILESTONES_CONFIG:
        title = ms_config["title"]
        
        try:
            if title in existing_milestones:
                # Actualizar milestone existente
                ms = existing_milestones[title]
                ms.edit(
                    title=title,
                    description=ms_config["description"],
                    due_on=ms_config.get("due_on")
                )
                print(f"  ✓ Actualizado: {title}")
                updated += 1
            else:
                # Crear nuevo milestone
                repo.create_milestone(
                    title=title,
                    description=ms_config["description"],
                    due_on=ms_config.get("due_on")
                )
                print(f"  ✓ Creado: {title}")
                created += 1
            time.sleep(0.5)  # Rate limiting
        except GithubException as e:
            print(f"  ⚠️  Error con {title}: {e.data.get('message', str(e))}")
        except Exception as e:
            print(f"  ⚠️  Error con {title}: {e}")
    
    print(f"\n✅ Milestones: {created} creados, {updated} actualizados (total: {len(MILESTONES_CONFIG)})")


# =============================================================================
# 3. CONFIGURACIÓN DE PROJECT V2
# =============================================================================

def get_project_node_id(owner: str, number: int) -> Optional[str]:
    """
    Busca el Project ID soportando Users y Organizations.
    
    Args:
        owner: Owner del proyecto (usuario u organización)
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
    
    try:
        data = graphql_request(query, {"owner": owner, "number": number})
        result_data = data.get("data", {})
        
        # Intentar obtener de User
        if result_data.get("user") and result_data["user"].get("projectV2"):
            project = result_data["user"]["projectV2"]
            print(f"  ✓ Proyecto encontrado (User): {project.get('title', 'Unknown')}")
            return project["id"]
        
        # Intentar obtener de Org
        if result_data.get("organization") and result_data["organization"].get("projectV2"):
            project = result_data["organization"]["projectV2"]
            print(f"  ✓ Proyecto encontrado (Organization): {project.get('title', 'Unknown')}")
            return project["id"]
        
        return None
    except Exception as e:
        print(f"⚠️  Error obteniendo Project ID: {e}")
        return None


def create_project_field(project_id: str, name: str, data_type: str, options: List[str] = None) -> bool:
    """
    Crea un campo personalizado en el proyecto automáticamente usando GraphQL.
    
    Args:
        project_id: ID del proyecto
        name: Nombre del campo
        data_type: Tipo de campo (SINGLE_SELECT, TEXT, NUMBER, DATE)
        options: Lista de opciones para SINGLE_SELECT
    
    Returns:
        True si se creó exitosamente, False en caso contrario
    """
    mutation = """
    mutation($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!, $singleSelectOptions: [ProjectV2SingleSelectFieldOptionInput!]) {
      createProjectV2Field(input: {
        projectId: $projectId
        name: $name
        dataType: $dataType
        singleSelectOptions: $singleSelectOptions
      }) {
        projectV2Field {
          ... on ProjectV2Field {
            id
            name
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
    """
    
    variables = {
        "projectId": project_id,
        "name": name,
        "dataType": data_type,
        "singleSelectOptions": None
    }
    
    if options and data_type == "SINGLE_SELECT":
        # Colores para opciones (puedes personalizar)
        color_map = {
            "High": "RED",
            "Medium": "ORANGE",
            "Low": "GREEN",
            "Pending": "GRAY",
            "Passed": "GREEN",
            "Failed": "RED"
        }
        variables["singleSelectOptions"] = [
            {"name": opt, "color": color_map.get(opt, "GRAY")}
            for opt in options
        ]
    
    try:
        result = graphql_request(mutation, variables)
        if "errors" in result:
            error_msg = result["errors"][0].get("message", "")
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                print(f"     ℹ️  Campo '{name}' ya existe, saltando.")
                return True
            else:
                print(f"     ❌ Error creando campo '{name}': {error_msg}")
                return False
        
        field_data = result.get("data", {}).get("createProjectV2Field", {}).get("projectV2Field", {})
        if field_data:
            print(f"     ✓ Campo '{name}' creado exitosamente.")
            return True
        return False
    except Exception as e:
        error_str = str(e)
        if "already exists" in error_str.lower() or "duplicate" in error_str.lower():
            print(f"     ℹ️  Campo '{name}' ya existe, saltando.")
            return True
        else:
            print(f"     ❌ Error creando campo '{name}': {e}")
            return False


def setup_project_fields(project_id: str, auto_create: bool = True):
    """
    Configura campos personalizados del proyecto.
    
    Args:
        project_id: ID del proyecto
        auto_create: Si True, intenta crear campos automáticamente
    """
    print("\n" + "="*60)
    print("🔧 CONFIGURANDO CAMPOS PERSONALIZADOS")
    print("="*60)
    
    fields_to_create = [
        {"name": "Impacto", "type": "SINGLE_SELECT", "options": ["High", "Medium", "Low"]},
        {"name": "Fuente de Datos", "type": "SINGLE_SELECT", 
         "options": ["IDESCAT", "Incasòl", "OpenData BCN", "Portal Dades", "Internal"]},
        {"name": "Estado DQC", "type": "SINGLE_SELECT", "options": ["Pending", "Passed", "Failed"]},
        {"name": "KPI Objetivo", "type": "TEXT", "options": None},
        {"name": "Confidence", "type": "NUMBER", "options": None},
        {"name": "Owner", "type": "TEXT", "options": None}
    ]
    
    if auto_create:
        print("\n⚙️  Creando campos automáticamente...")
        created_count = 0
        for field in fields_to_create:
            if create_project_field(project_id, field["name"], field["type"], field.get("options")):
                created_count += 1
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n✅ {created_count}/{len(fields_to_create)} campos procesados")
    
    print(f"""
⚠️  NOTA IMPORTANTE:

1. El campo 'Sprint' (Iteration) debe configurarse manualmente en la UI
   debido a limitaciones de la API para configuración de fechas.

2. Ve a tu proyecto: https://github.com/users/{ORG_NAME}/projects/{PROJECT_NUMBER}
   → Settings → Fields → Add field → Iteration

3. Configura las iteraciones (Sprints) con fechas:
   - Sprint 0 (Setup)
   - Sprint 1 (IDESCAT)
   - Sprint 2 (Renta)
   - Sprint 3 (Incasòl)
   - Sprint 4 (Precios)
""")


def setup_project_views(project_id: str):
    """Configura vistas del proyecto"""
    print("\n" + "="*60)
    print("👁️  CONFIGURANDO VISTAS DEL PROYECTO")
    print("="*60)
    
    print(f"""
⚠️  NOTA: Las vistas deben configurarse manualmente:

1. Ve a tu proyecto: https://github.com/users/{ORG_NAME}/projects/{PROJECT_NUMBER}

2. **Vista 1: Board - Ejecución Diaria**
   - Click en "+" para nueva vista
   - Tipo: Board
   - Nombre: "📋 Sprint Board"
   - Grupo por: Status (columnas por defecto)
   - Filtro: Sprint = "Sprint actual"
   - Mostrar: Título, Impacto, Fuente, Owner

3. **Vista 2: Table - Planificación**
   - Tipo: Table
   - Nombre: "📊 Planning View"
   - Grupo por: Sprint
   - Ordenar por: Impacto (High → Low)
   - Columnas visibles: Título, Impacto, Fuente, Sprint, Estado DQC, Owner, KPI

4. **Vista 3: Roadmap - Timeline**
   - Tipo: Roadmap
   - Nombre: "🗺️  Project Roadmap"
   - Grupo por: Sprint (Iterations)
   - Vista de timeline: 6 meses

5. **Vista 4: Table - DQC Tracking**
   - Tipo: Table
   - Nombre: "✅ Quality Tracking"
   - Filtro: Estado DQC = "Pending" OR "Failed"
   - Ordenar por: Sprint
   - Columnas: Título, Estado DQC, Confidence, Owner

6. **Vista 5: Board - Por Fuente**
   - Tipo: Board
   - Nombre: "📁 By Data Source"
   - Grupo por: Fuente de Datos
   - Para ver cobertura por fuente
""")
    
    response = input("\n¿Has configurado las vistas? (s/n): ").lower().strip()
    if response == 's':
        print("✅ Vistas configuradas")
    else:
        print("⚠️  Recuerda configurar las vistas cuando sea conveniente")


def setup_project_automations(project_id: str):
    """Configura automatizaciones del proyecto"""
    print("\n" + "="*60)
    print("⚙️  CONFIGURANDO AUTOMATIZACIONES")
    print("="*60)
    
    print(f"""
⚠️  NOTA: Configurar estas automatizaciones en Project Settings:

**Automatizaciones Built-in:**

1. **Auto-close → Done**
   - When: Issue is closed
   - Then: Set Status to "Done"
   
2. **Auto-archive**
   - When: Item in "Done" for 30 days
   - Then: Archive item
   
3. **Auto-add to project**
   - When: Issue has label "roadmap"
   - Then: Add to project in "Backlog"

**Automatizaciones con GitHub Actions:**

(Ya configuradas en workflows/)

✅ .github/workflows/project-sync.yml
   - Sincroniza PRs con issues
   - Mueve a "In Review" automáticamente

✅ .github/workflows/project-automation.yml
   - Sincroniza issues al abrir
   - Auto-detección de campos

✅ .github/workflows/data-quality.yml
   - Actualiza "Estado DQC" tras tests
   - Notifica fallos

✅ .github/workflows/ai_audit.yml
   - AI PM audita issues automáticamente
   - Actualiza "Confidence"

✅ .github/workflows/kpi-update.yml
   - Actualiza métricas al cerrar issues
   - Genera reportes

Para activar:
1. Ve a Project → Settings → Workflows
2. Habilita cada automatización listada
3. Guarda cambios
""")
    
    response = input("\n¿Has revisado las automatizaciones? (s/n): ").lower().strip()
    if response == 's':
        print("✅ Automatizaciones revisadas")
    else:
        print("⚠️  Revisa las automatizaciones cuando sea conveniente")


# =============================================================================
# 4. ESTRUCTURA DE COLUMNAS
# =============================================================================

def setup_project_columns():
    """Documenta estructura de columnas"""
    print("\n" + "="*60)
    print("📂 ESTRUCTURA DE COLUMNAS RECOMENDADA")
    print("="*60)
    
    print("""
Las columnas por defecto en Projects v2 son configurables.
Estructura recomendada:

1. 📥 **Backlog**
   - Issues planificadas pero no comprometidas
   - Ordenar por: Impacto (High primero)
   - WIP limit: Ninguno

2. 🎯 **Ready (Sprint Actual)**
   - Issues comprometidas para el sprint
   - Campos obligatorios: Impacto, Fuente, Sprint, KPI
   - WIP limit: 5-8 issues

3. 🔨 **In Progress**
   - Trabajo activo
   - WIP limit: 2 (respeta capacidad individual)
   - Owner debe estar asignado

4. ⏸️  **QA / Blocked**
   - Esperando validación o bloqueadas
   - Requiere comentario explicando bloqueador
   - Revisión diaria

5. ✅ **Done**
   - Completadas
   - Estado DQC debe ser "Passed"
   - Auto-archive en 30 días

Las columnas se configuran automáticamente en Projects v2.
No requiere acción manual adicional.
""")
    
    print("✅ Estructura de columnas documentada")


# =============================================================================
# 5. TEMPLATES Y DOCUMENTACIÓN
# =============================================================================

def verify_templates():
    """Verifica que existan los templates necesarios"""
    print("\n" + "="*60)
    print("📝 VERIFICANDO TEMPLATES")
    print("="*60)
    
    templates_to_check = [
        ".github/ISSUE_TEMPLATE.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/CONTRIBUTING.md"
    ]
    
    all_exist = True
    for template in templates_to_check:
        template_path = REPO_ROOT / template
        if template_path.exists():
            print(f"  ✓ Existe: {template}")
        else:
            print(f"  ⚠️  Falta: {template}")
            all_exist = False
    
    if all_exist:
        print("\n✅ Todos los templates existen")
    else:
        print("\n⚠️  Algunos templates faltan (revisar)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Ejecuta configuración completa del proyecto"""
    global PROJECT_NUMBER
    
    parser = argparse.ArgumentParser(
        description="Configuración completa del proyecto GitHub"
    )
    parser.add_argument(
        "--project-number",
        type=int,
        default=PROJECT_NUMBER,
        help=f"Número del proyecto (default: {PROJECT_NUMBER})"
    )
    parser.add_argument(
        "--no-auto-fields",
        action="store_true",
        help="No crear campos automáticamente (solo mostrar instrucciones)"
    )
    
    args = parser.parse_args()
    PROJECT_NUMBER = args.project_number
    
    print("\n" + "="*70)
    print("🚀 CONFIGURACIÓN COMPLETA DEL PROYECTO")
    print("   Barcelona Housing Demographics Analyzer")
    print("="*70)
    
    print(f"\n📋 Configuración detectada:")
    print(f"   Owner: {REPO_OWNER}")
    print(f"   Repo: {REPO_NAME}")
    print(f"   Project: #{PROJECT_NUMBER}")
    
    # Inicializar cliente GitHub
    try:
        gh = Github(GITHUB_TOKEN)
        repo = gh.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        user = gh.get_user()
    except GithubException as e:
        error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
        print(f"❌ Error accediendo a GitHub: {error_msg}")
        sys.exit(1)
    
    print(f"\n📦 Repositorio: {repo.full_name}")
    print(f"👤 Usuario: {user.login}")
    print(f"🔗 URL: {repo.html_url}")
    
    # 1. Labels
    setup_labels(repo)
    time.sleep(1)
    
    # 2. Milestones
    setup_milestones(repo)
    time.sleep(1)
    
    # 3. Project v2
    project_id = get_project_node_id(REPO_OWNER, PROJECT_NUMBER)
    if project_id:
        print(f"\n✓ Project ID encontrado: {project_id[:20]}...")
        setup_project_fields(project_id, auto_create=not args.no_auto_fields)
        setup_project_views(project_id)
        setup_project_automations(project_id)
    else:
        print(f"\n⚠️  No se pudo obtener ID del proyecto #{PROJECT_NUMBER}")
        print(f"   Verifica que el proyecto existe en: https://github.com/users/{REPO_OWNER}/projects/{PROJECT_NUMBER}")
        print(f"   O ajusta PROJECT_NUMBER ({PROJECT_NUMBER}) si es diferente")
    
    # 4. Columnas
    setup_project_columns()
    
    # 5. Templates
    verify_templates()
    
    # Resumen final
    print("\n" + "="*70)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("="*70)
    
    print("""
📋 **Resumen:**

   ✓ Labels configurados (30+)
   ✓ Milestones creados (7)
   ✓ Campos personalizados (instrucciones proporcionadas)
   ✓ Vistas del proyecto (instrucciones proporcionadas)
   ✓ Automatizaciones (instrucciones proporcionadas)
   ✓ Templates verificados

🎯 **Próximos pasos:**

   1. Revisa campos personalizados en la UI del proyecto
   2. Configura las vistas recomendadas
   3. Activa las automatizaciones built-in
   4. Ejecuta: python .github/scripts/create_sprint_issues.py
   5. Comienza Sprint 1

📚 **Documentación:**

   - docs/PROJECT_MANAGEMENT.md
   - docs/COMPLIANCE_CHECKLIST.md
   - .github/CONTRIBUTING.md

🤖 **Workflows activos:**

   - AI PM audita issues diariamente
   - Data Quality Checks en PRs
   - Métricas actualizadas automáticamente
   - Project automation en issues abiertos
""")


if __name__ == "__main__":
    main()

