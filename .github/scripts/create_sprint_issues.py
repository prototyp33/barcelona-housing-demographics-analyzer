#!/usr/bin/env python3
"""
Crea issues del Sprint 1 con configuración completa

Uso:
    export GITHUB_TOKEN="tu_token"
    python .github/scripts/create_sprint_issues.py
"""

import os
import sys
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

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN no encontrado")
    print("   Ejecuta: export GITHUB_TOKEN='tu_token'")
    sys.exit(1)

REPO_OWNER = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"

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

## Definición de Hecho

- [ ] ID identificado y documentado
- [ ] Endpoint funcional probado
- [ ] Documentación actualizada
- [ ] Tests actualizados

## Impacto KPI

- **KPI:** Años de renta disponibles (objetivo: 8 años)
- **Fuente:** IDESCAT API
- **Bloquea:** Issue Pipeline renta histórica
""",
        "labels": ["sprint-1", "data-extraction", "idescat", "priority-high", "roadmap"],
        "milestone": "Sprint 1: IDESCAT Integration"
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

## Definición de Hecho

- [ ] Documentación completa en docs/sources/idescat.md
- [ ] Ejemplos de uso incluidos
- [ ] Referencias en README actualizadas

## Impacto

Facilita onboarding y mantenimiento futuro.
""",
        "labels": ["sprint-1", "documentation", "idescat", "priority-medium"],
        "milestone": "Sprint 1: IDESCAT Integration"
    },
    {
        "title": "[S1] Implementar estrategias alternativas IDESCATExtractor",
        "body": """## Objetivo

Completar estrategias 2 y 3 (web scraping y archivos públicos) como fallback.

## Contexto

Solo activar si la API no proporciona datos por barrio.

## Pasos

1. Investigar estructura web IDESCAT
2. Implementar scraping específico
3. Identificar URLs archivos públicos
4. Validar mapeo de barrios

## Definición de Hecho

- [ ] Al menos una estrategia alternativa funcional
- [ ] Cobertura ≥80% para 2015-2023
- [ ] Tests actualizados

## Notas

**PLAN B:** Solo si Issue 1 falla.
""",
        "labels": ["sprint-1", "data-extraction", "web-scraping", "priority-low"],
        "milestone": "Sprint 1: IDESCAT Integration"
    }
]


def create_sprint_issues():
    """Crea issues del Sprint 1"""
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
    
    # Obtener milestones
    milestones = {ms.title: ms for ms in repo.get_milestones(state="all")}
    
    print("\n📝 Creando issues del Sprint 1...")
    print("="*60)
    
    created = 0
    errors = 0
    
    for issue_data in SPRINT_1_ISSUES:
        try:
            # Obtener milestone
            milestone = milestones.get(issue_data["milestone"])
            if not milestone:
                print(f"  ⚠️  Milestone '{issue_data['milestone']}' no encontrado")
                print(f"     Creando issue sin milestone...")
            
            # Crear issue
            issue = repo.create_issue(
                title=issue_data["title"],
                body=issue_data["body"],
                labels=issue_data["labels"],
                milestone=milestone
            )
            
            print(f"  ✓ Creada: #{issue.number} - {issue.title}")
            created += 1
            time.sleep(1)  # Rate limiting
            
        except GithubException as e:
            print(f"  ❌ Error creando '{issue_data['title']}': {e.data.get('message', str(e))}")
            errors += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            errors += 1
    
    print("\n" + "="*60)
    if created > 0:
        print(f"✅ {created} issues creadas exitosamente")
    if errors > 0:
        print(f"⚠️  {errors} errores al crear issues")
    
    print("\n💡 Próximo paso: Sincronizar issues con el proyecto:")
    print("   python .github/scripts/project_automation.py --issue <NUM> --auto-detect")


if __name__ == "__main__":
    create_sprint_issues()

