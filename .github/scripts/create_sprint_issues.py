#!/usr/bin/env python3
"""
Crea issues del Sprint 1 (Idempotente)

El script es idempotente: no crea duplicados si se ejecuta múltiples veces.
Detecta issues existentes por título y las omite.

Uso:
    export GITHUB_TOKEN="tu_token"
    python .github/scripts/create_sprint_issues.py
    python .github/scripts/create_sprint_issues.py --sprint 2
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Añadir el directorio raíz al path para imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from github import Github, GithubException
except ImportError:
    print("❌ Error: PyGithub no está instalado")
    print("   Ejecuta: pip install PyGithub")
    sys.exit(1)

# Configuración básica
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN no encontrado")
    print("   Ejecuta: export GITHUB_TOKEN='tu_token'")
    sys.exit(1)

# Detección automática de owner/repo desde git
def detect_git_config() -> tuple[str, str]:
    """Detecta owner y repo desde git config."""
    try:
        import subprocess
        git_remote = subprocess.check_output(
            ['git', 'config', '--get', 'remote.origin.url'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        if "github.com" in git_remote:
            parts = git_remote.replace(".git", "").split("/")[-2:]
            if ":" in parts[0]:
                parts[0] = parts[0].split(":")[-1]
            return parts[0], parts[1]
    except Exception:
        pass
    
    return "prototyp33", "barcelona-housing-demographics-analyzer"

DETECTED_OWNER, DETECTED_REPO = detect_git_config()
REPO_OWNER = os.environ.get("REPO_OWNER", DETECTED_OWNER)
REPO_NAME = os.environ.get("REPO_NAME", DETECTED_REPO)

SPRINT_1_ISSUES = [
    {
        "title": "[S1] Investigar ID indicador renta IDESCAT",
        "body": """## Objetivo

Identificar el ID específico del indicador de renta disponible en la API de IDESCAT.

## Contexto

- Extractor base implementado con 3 estrategias
- Tests unitarios completos (13/13 pasando)
- Falta ID del indicador específico de renta

## Pasos

1. Explorar API de indicadores
2. Buscar indicadores relacionados con "renta"
3. Probar endpoint con datos reales
4. Verificar cobertura temporal 2015-2023
5. Documentar hallazgos

## Criterios de Aceptación

- [ ] ID identificado y documentado
- [ ] Endpoint funcional probado con curl/requests
- [ ] Documentación actualizada
- [ ] Tests actualizados

## Impacto KPI

- **KPI:** Años de renta disponibles (objetivo: 8 años)
- **Fuente:** IDESCAT API
- **Bloquea:** Issue Pipeline renta histórica
""",
        "labels": ["sprint-1", "data-extraction", "idescat", "priority-high", "roadmap"],
        "milestone_keyword": "Sprint 1"
    },
    {
        "title": "[S1] Documentar IDESCATExtractor",
        "body": """## Objetivo

Crear documentación completa del extractor de IDESCAT.

## Pasos

1. Crear docs/sources/idescat.md
2. Documentar endpoints y estructura API
3. Documentar estrategias de extracción
4. Incluir ejemplos de uso
5. Documentar limitaciones y rate limits

## Entregable

- Archivo `docs/sources/idescat.md` con documentación técnica completa

## Definición de Hecho

- [ ] Documentación completa en docs/sources/idescat.md
- [ ] Ejemplos de uso incluidos
- [ ] Referencias en README actualizadas

## Impacto

Facilita onboarding y mantenimiento futuro.
""",
        "labels": ["sprint-1", "documentation", "idescat", "priority-medium"],
        "milestone_keyword": "Sprint 1"
    },
    {
        "title": "[S1] Implementar tests unitarios base",
        "body": """## Objetivo

Asegurar cobertura mínima del 80% para IDESCATExtractor.

## Tareas

- [ ] Testear conexión API
- [ ] Testear parseo de JSON
- [ ] Testear manejo de errores
- [ ] Testear rate limiting
- [ ] Verificar cobertura con pytest-cov

## Criterios de Aceptación

- [ ] Cobertura ≥80% en tests
- [ ] Todos los tests pasando
- [ ] Tests documentados

## Impacto

Garantiza calidad y mantenibilidad del código.
""",
        "labels": ["sprint-1", "testing", "priority-medium"],
        "milestone_keyword": "Sprint 1"
    }
]


def get_milestone(repo, keyword: str):
    """
    Busca milestone por palabra clave (case-insensitive).
    
    Args:
        repo: Repositorio de GitHub
        keyword: Palabra clave para buscar (ej: "Sprint 1")
    
    Returns:
        Milestone encontrado o None
    """
    keyword_lower = keyword.lower()
    
    # Buscar en milestones abiertos primero
    for ms in repo.get_milestones(state="open"):
        if keyword_lower in ms.title.lower():
            return ms
    
    # Si no se encuentra, buscar en todos (incluyendo cerrados)
    for ms in repo.get_milestones(state="all"):
        if keyword_lower in ms.title.lower():
            return ms
    
    return None


def get_existing_issues(repo, state: str = "all"):
    """
    Obtiene todas las issues existentes para evitar duplicados.
    
    Args:
        repo: Repositorio de GitHub
        state: Estado de issues ("open", "closed", "all")
    
    Returns:
        Dict con títulos como keys
    """
    existing = {}
    try:
        for issue in repo.get_issues(state=state):
            existing[issue.title] = issue
    except Exception as e:
        print(f"⚠️  Error obteniendo issues existentes: {e}")
    
    return existing


def main():
    """Función principal idempotente"""
    parser = argparse.ArgumentParser(
        description="Crea issues del Sprint 1 (idempotente)"
    )
    parser.add_argument(
        "--sprint",
        type=int,
        default=1,
        help="Número de sprint (default: 1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sin crear issues"
    )
    
    args = parser.parse_args()
    
    if not GITHUB_TOKEN:
        print("❌ Error: Faltan credenciales (GITHUB_TOKEN)")
        sys.exit(1)
    
    gh = Github(GITHUB_TOKEN)
    
    try:
        repo = gh.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    except GithubException as e:
        error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
        print(f"❌ Error accediendo al repositorio: {error_msg}")
        sys.exit(1)
    
    print(f"\n🚀 Gestionando Issues Sprint {args.sprint} en {repo.full_name}...")
    print("="*60)
    
    # Caché de issues existentes para evitar duplicados
    existing_issues = get_existing_issues(repo, state="all")
    existing_titles = set(existing_issues.keys())
    
    if args.dry_run:
        print("🔍 MODO DRY-RUN: No se crearán issues reales\n")
    
    created = 0
    skipped = 0
    errors = 0
    
    # Filtrar issues según sprint (por ahora solo Sprint 1)
    issues_to_create = [
        issue for issue in SPRINT_1_ISSUES
        if args.sprint == 1  # Por ahora solo soportamos Sprint 1
    ]
    
    if not issues_to_create:
        print(f"⚠️  No hay issues configuradas para Sprint {args.sprint}")
        return
    
    for issue_data in issues_to_create:
        title = issue_data["title"]
        
        # Verificar si ya existe
        if title in existing_titles:
            existing_issue = existing_issues[title]
            print(f"  ⏭️  Saltando (ya existe): #{existing_issue.number} - {title}")
            skipped += 1
            continue
        
        # Buscar milestone
        milestone = get_milestone(repo, issue_data["milestone_keyword"])
        if not milestone:
            print(f"  ⚠️  Milestone '{issue_data['milestone_keyword']}' no encontrado")
            print(f"     Se creará issue sin milestone")
        
        if args.dry_run:
            print(f"  🔍 [DRY-RUN] Crearía: {title}")
            print(f"     Labels: {', '.join(issue_data['labels'])}")
            if milestone:
                print(f"     Milestone: {milestone.title}")
            created += 1
            continue
        
        # Crear issue
        try:
            new_issue = repo.create_issue(
                title=title,
                body=issue_data["body"],
                labels=issue_data["labels"],
                milestone=milestone
            )
            print(f"  ✅ Creada #{new_issue.number}: {title}")
            created += 1
            time.sleep(1)  # Rate limiting
            
        except GithubException as e:
            error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)
            print(f"  ❌ Error creando '{title}': {error_msg}")
            errors += 1
        except Exception as e:
            print(f"  ❌ Error inesperado: {e}")
            errors += 1
    
    # Resumen
    print("\n" + "="*60)
    if args.dry_run:
        print(f"🔍 DRY-RUN completado:")
    else:
        print(f"📊 Resumen:")
    print(f"   ✅ Creadas: {created}")
    print(f"   ⏭️  Omitidas (existentes): {skipped}")
    if errors > 0:
        print(f"   ❌ Errores: {errors}")
    
    if created > 0 and not args.dry_run:
        print("\n💡 Próximo paso: Sincronizar issues con el proyecto:")
        print("   python .github/scripts/project_automation.py --issue <NUM> --auto-detect")


if __name__ == "__main__":
    main()

