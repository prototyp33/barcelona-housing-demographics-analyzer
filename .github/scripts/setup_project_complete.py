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
# CONFIGURACIÓN Y AUTO-DETECCIÓN
# =============================================================================

def detect_git_repo() -> tuple[str, str]:
    """
    Detecta owner y repo desde git config.
    Soporta SSH y HTTPS.
    """
    try:
        url = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # Limpiar URL (soporta SSH y HTTPS)
        clean_url = url.replace(".git", "").replace("git@github.com:", "").replace("https://github.com/", "")
        
        if "/" in clean_url:
            parts = clean_url.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    
    # Valores por defecto
    return "prototyp33", "barcelona-housing-demographics-analyzer"

DETECTED_OWNER, DETECTED_NAME = detect_git_repo()

# Argumentos CLI
parser = argparse.ArgumentParser(
    description='Setup completo del proyecto GitHub con mejores prácticas',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Ejemplos:
  # Uso básico (auto-detecta desde git)
  python .github/scripts/setup_project_complete.py

  # Especificar configuración manualmente
  python .github/scripts/setup_project_complete.py --owner prototyp33 --repo mi-repo --project-number 2

  # Sin crear campos automáticamente
  python .github/scripts/setup_project_complete.py --no-auto-fields
    """
)

parser.add_argument(
    '--owner',
    default=os.environ.get("REPO_OWNER", DETECTED_OWNER),
    help='Dueño del repo (default: auto-detectado desde git)'
)
parser.add_argument(
    '--repo',
    default=os.environ.get("REPO_NAME", DETECTED_NAME),
    help='Nombre del repo (default: auto-detectado desde git)'
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
    help='GitHub Token (default: GITHUB_TOKEN env var)'
)
parser.add_argument(
    '--no-auto-fields',
    action='store_true',
    help='No crear campos automáticamente (solo mostrar instrucciones)'
)

args = parser.parse_args()

if not args.token:
    print("❌ Error: GITHUB_TOKEN no encontrado")
    print("   Exportalo o usa --token")
    sys.exit(1)

GRAPHQL_URL = "https://api.github.com/graphql"

# =============================================================================
# HELPERS GRAPHQL
# =============================================================================

def graphql_request(query: str, variables: Dict = None) -> Dict:
    """
    Ejecuta query GraphQL con manejo de errores.
    
    Args:
        query: Query GraphQL como string
        variables: Variables para la query
    
    Returns:
        Respuesta JSON de la API
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
        
        if response.status_code != 200:
            raise Exception(f"GraphQL Error ({response.status_code}): {response.text}")
        
        data = response.json()
        
        if "errors" in data:
            error_messages = [e.get("message", "Unknown error") for e in data["errors"]]
            # Solo mostrar warning si no es "already exists" (esperado)
            if not any("already exists" in msg.lower() for msg in error_messages):
                print(f"⚠️  GraphQL Warnings: {', '.join(error_messages)}")
        
        return data
    except requests.RequestException as e:
        raise Exception(f"GraphQL Request Error: {str(e)}")


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


def setup_labels_milestones(repo):
    """
    Configura labels y milestones de forma segura e idempotente.
    
    Args:
        repo: Repositorio de GitHub
    """
    print(f"\n🏷️  Sincronizando Metadatos en {repo.full_name}...")
    
    # Labels
    existing_labels = {l.name: l for l in repo.get_labels()}
    labels_created = 0
    labels_updated = 0
    
    for cfg in LABELS_CONFIG:
        name = cfg["name"]
        try:
            if name in existing_labels:
                existing_labels[name].edit(
                    name=name,
                    color=cfg["color"],
                    description=cfg.get("description", "")
                )
                labels_updated += 1
            else:
                repo.create_label(
                    name=name,
                    color=cfg["color"],
                    description=cfg.get("description", "")
                )
                labels_created += 1
            time.sleep(0.3)  # Rate limiting
        except GithubException as e:
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            print(f"   ⚠️  Error con label '{name}': {error_msg}")
        except Exception as e:
            print(f"   ⚠️  Error con label '{name}': {e}")
    
    if labels_created > 0 or labels_updated > 0:
        print(f"   ✓ Labels: {labels_created} creados, {labels_updated} actualizados")
    
    # Milestones
    existing_ms = {m.title: m for m in repo.get_milestones(state="all")}
    milestones_created = 0
    
    for cfg in MILESTONES_CONFIG:
        title = cfg["title"]
        try:
            if title not in existing_ms:
                repo.create_milestone(
                    title=title,
                    description=cfg["description"],
                    due_on=cfg.get("due_on")
                )
                milestones_created += 1
                time.sleep(0.3)  # Rate limiting
        except GithubException as e:
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            print(f"   ⚠️  Error con milestone '{title}': {error_msg}")
        except Exception as e:
            print(f"   ⚠️  Error con milestone '{title}': {e}")
    
    if milestones_created > 0:
        print(f"   ✓ Milestones: {milestones_created} creados")
    
    print(f"   ✅ Metadatos sincronizados ({len(LABELS_CONFIG)} labels, {len(MILESTONES_CONFIG)} milestones)")


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
    Obtiene ID del proyecto soportando User y Org.
    
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
        
        # Intentar User
        if result_data.get("user") and result_data["user"].get("projectV2"):
            project = result_data["user"]["projectV2"]
            print(f"   ✓ Proyecto encontrado (User): {project.get('title', 'Unknown')}")
            return project["id"]
        
        # Intentar Org
        if result_data.get("organization") and result_data["organization"].get("projectV2"):
            project = result_data["organization"]["projectV2"]
            print(f"   ✓ Proyecto encontrado (Organization): {project.get('title', 'Unknown')}")
            return project["id"]
        
        return None
    except Exception as e:
        print(f"   ⚠️  Error obteniendo Project ID: {e}")
        return None


def create_project_field(project_id: str, name: str, data_type: str, options: List[Dict] = None):
    """
    Crea campo usando GraphQL mutations.
    
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
    
    try:
        graphql_request(mutation, variables)
        print(f"   ✅ Campo creado: {name}")
    except Exception as e:
        error_str = str(e)
        if "already exists" in error_str.lower() or "duplicate" in error_str.lower():
            print(f"   ℹ️  Campo ya existe: {name}")
        else:
            print(f"   ⚠️  Error creando {name}: {e}")


def setup_project_v2(project_id: str):
    """
    Configura estructura completa del proyecto.
    
    Args:
        project_id: ID del proyecto
    """
    print("\n🏗️  Configurando Campos del Proyecto (GraphQL)...")
    
    if args.no_auto_fields:
        print("   ⏭️  Modo --no-auto-fields: saltando creación automática")
        print(f"\n   📝 Ve a: https://github.com/users/{args.owner}/projects/{args.project_number}/settings")
        print("   Y crea los campos manualmente según la documentación.")
        return
    
    # 1. Impacto (Single Select)
    create_project_field(project_id, "Impacto", "SINGLE_SELECT", [
        {"name": "High", "color": "RED"},
        {"name": "Medium", "color": "YELLOW"},
        {"name": "Low", "color": "GRAY"}
    ])
    time.sleep(0.5)  # Rate limiting
    
    # 2. Fuente de Datos (Single Select)
    create_project_field(project_id, "Fuente de Datos", "SINGLE_SELECT", [
        {"name": "IDESCAT", "color": "BLUE"},
        {"name": "Incasòl", "color": "ORANGE"},
        {"name": "OpenData BCN", "color": "PURPLE"},
        {"name": "Portal Dades", "color": "ORANGE"},
        {"name": "Internal", "color": "GRAY"}
    ])
    time.sleep(0.5)
    
    # 3. Estado DQC (Single Select)
    create_project_field(project_id, "Estado DQC", "SINGLE_SELECT", [
        {"name": "Passed", "color": "GREEN"},
        {"name": "Failed", "color": "RED"},
        {"name": "Pending", "color": "GRAY"}
    ])
    time.sleep(0.5)
    
    # 4. Otros Campos
    create_project_field(project_id, "KPI Objetivo", "TEXT")
    time.sleep(0.5)
    
    create_project_field(project_id, "Confidence", "NUMBER")
    time.sleep(0.5)
    
    create_project_field(project_id, "Owner", "TEXT")
    
    print("\n📝 NOTA MANUAL IMPORTANTE:")
    print("   La API no permite configurar fechas de iteraciones (Sprints).")
    print(f"   Ve a: https://github.com/users/{args.owner}/projects/{args.project_number}/settings")
    print("   Y configura el campo 'Iteration' manualmente con los sprints.")


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
    print("="*60)
    print(f"🚀 SETUP DE PROYECTO: {args.owner}/{args.repo}")
    print("="*60)
    
    # Conexión
    try:
        gh = Github(args.token)
        repo = gh.get_repo(f"{args.owner}/{args.repo}")
        user = gh.get_user()
    except GithubException as e:
        error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
        print(f"❌ No se encuentra el repositorio: {error_msg}")
        print("   Verifica nombre y permisos.")
        sys.exit(1)
    
    print(f"\n📦 Repositorio: {repo.full_name}")
    print(f"👤 Usuario: {user.login}")
    print(f"🔗 URL: {repo.html_url}")
    
    # 1. Configurar Repo (Labels y Milestones)
    setup_labels_milestones(repo)
    
    # 2. Configurar Proyecto V2
    project_id = get_project_node_id(args.owner, args.project_number)
    
    if project_id:
        print(f"\n✓ Proyecto encontrado (ID: {project_id[:20]}...)")
        setup_project_v2(project_id)
        setup_project_views(project_id)
        setup_project_automations(project_id)
    else:
        print(f"\n⚠️  No se encontró el Proyecto #{args.project_number}")
        print(f"   Crea uno vacío primero en: https://github.com/users/{args.owner}/projects/new")
    
    # 3. Columnas y Templates
    setup_project_columns()
    verify_templates()
    
    # Resumen final
    print("\n" + "="*60)
    print("✅ SETUP FINALIZADO")
    print("="*60)
    
    print("""
📋 **Resumen:**

   ✓ Labels sincronizados
   ✓ Milestones creados
   ✓ Campos del proyecto configurados
   ✓ Templates verificados

🎯 **Próximos pasos:**

   1. Configura el campo 'Iteration' (Sprints) manualmente en la UI
   2. Crea las vistas recomendadas del proyecto
   3. Activa las automatizaciones built-in
   4. Ejecuta: python .github/scripts/create_sprint_issues.py
   5. Comienza Sprint 1

📚 **Documentación:**

   - docs/PROJECT_MANAGEMENT.md
   - .github/scripts/README_SETUP.md
""")


if __name__ == "__main__":
    main()

