# GitHub GraphQL API - Guía de Uso

## 📚 Introducción

Este proyecto incluye un módulo helper para usar la **GitHub GraphQL API** en lugar de la REST API tradicional. GraphQL ofrece ventajas significativas para consultas complejas y gestión de Projects v2.

## 🎯 Ventajas de GraphQL vs REST API

| Característica | REST API | GraphQL API |
|----------------|----------|-------------|
| **Peticiones** | Múltiples (una por recurso) | Una sola (todos los datos) |
| **Rate Limiting** | 5,000 requests/hora | 5,000 puntos/hora (más eficiente) |
| **Over-fetching** | Sí (recibes campos innecesarios) | No (solo pides lo que necesitas) |
| **Under-fetching** | Sí (necesitas múltiples requests) | No (una query obtiene todo) |
| **Projects v2** | No soportado | ✅ Soporte nativo |
| **Consultas complejas** | Limitadas | ✅ Muy potentes |
| **Latencia** | Alta (múltiples round-trips) | Baja (un solo round-trip) |

## 📦 Instalación

El módulo `scripts/github_graphql.py` no requiere dependencias adicionales (usa `requests` que ya está en `requirements.txt`).

## 🚀 Uso Básico

### Inicialización

```python
from scripts.github_graphql import GitHubGraphQL

# El token se obtiene automáticamente de GITHUB_TOKEN o gh CLI
gh = GitHubGraphQL()
```

### Obtener Issues con Detalles Completos

```python
# Una sola query obtiene: número, título, labels, milestone, assignees, etc.
issues = gh.get_issues_with_details(
    owner="prototyp33",
    repo="barcelona-housing-demographics-analyzer",
    state="OPEN",
    labels=["bug", "enhancement"],
    limit=100
)

for issue in issues["issues"]:
    print(f"#{issue['number']}: {issue['title']}")
    labels = [l["name"] for l in issue["labels"]["nodes"]]
    print(f"  Labels: {', '.join(labels)}")
```

### Obtener Todas las Issues (con paginación automática)

```python
# Obtiene TODAS las issues automáticamente (maneja paginación)
all_issues = gh.get_all_issues_paginated(
    owner="prototyp33",
    repo="barcelona-housing-demographics-analyzer",
    state="OPEN",
    labels=["priority-high"]
)

print(f"Total: {len(all_issues)} issues")
```

## 📊 Projects v2

GraphQL es la **única forma** de acceder a Projects v2 de GitHub.

### Obtener Información de un Proyecto

```python
project = gh.get_project_v2(
    owner="prototyp33",
    repo="barcelona-housing-demographics-analyzer",
    project_number=1
)

print(f"Proyecto: {project['title']}")
print(f"ID: {project['id']}")
print(f"URL: {project['url']}")

# Ver campos personalizados
for field in project["fields"]["nodes"]:
    print(f"  - {field['name']} ({field['dataType']})")
```

### Obtener Items de un Proyecto

```python
# Primero obtener el ID del proyecto
project = gh.get_project_v2(owner="prototyp33", repo="repo", project_number=1)
project_id = project["id"]

# Luego obtener los items
items = gh.get_project_items(project_id=project_id, limit=100)

for item in items["items"]:
    content = item.get("content", {})
    if content:
        print(f"#{content['number']}: {content['title']} ({content['state']})")
    
    # Ver valores de campos personalizados
    for field_value in item.get("fieldValues", {}).get("nodes", []):
        print(f"  {field_value.get('field', {}).get('name')}: {field_value.get('text') or field_value.get('number')}")
```

## 🔧 Consultas Personalizadas

Para consultas más complejas, puedes usar `execute_query()` directamente:

```python
query = """
query($owner: String!, $repo: String!) {
    repository(owner: $owner, name: $repo) {
        issues(first: 10, states: [OPEN]) {
            nodes {
                number
                title
                labels(first: 5) {
                    nodes {
                        name
                    }
                }
                comments {
                    totalCount
                }
                reactions {
                    totalCount
                }
            }
        }
        pullRequests(first: 10, states: [OPEN]) {
            nodes {
                number
                title
                reviews {
                    totalCount
                }
            }
        }
    }
}
"""

variables = {
    "owner": "prototyp33",
    "repo": "barcelona-housing-demographics-analyzer"
}

data = gh.execute_query(query, variables)

# Acceder a los datos
issues = data["repository"]["issues"]["nodes"]
prs = data["repository"]["pullRequests"]["nodes"]
```

## 📈 Ejemplo: Migración de REST a GraphQL

### Antes (REST API - múltiples requests)

```python
# Request 1: Obtener issues
issues = requests.get(f"{API_BASE}/repos/{owner}/{repo}/issues?state=open")

# Request 2: Para cada issue, obtener labels
for issue in issues.json():
    labels = requests.get(issue["labels_url"])
    issue["labels"] = labels.json()

# Request 3: Para cada issue, obtener milestone
for issue in issues.json():
    if issue.get("milestone_url"):
        milestone = requests.get(issue["milestone_url"])
        issue["milestone"] = milestone.json()

# Total: 1 + N + M requests (donde N = issues, M = issues con milestone)
```

### Después (GraphQL - una sola request)

```python
gh = GitHubGraphQL()
issues = gh.get_issues_with_details(
    owner=owner,
    repo=repo,
    state="OPEN"
)

# Total: 1 request (obtiene issues + labels + milestone + assignees + etc.)
```

## 🎨 Casos de Uso Recomendados

### ✅ Usar GraphQL para:

1. **Consultas complejas con múltiples recursos**
   - Issues con labels, milestone, assignees, comments
   - Commits con autor, mensaje, fecha
   - Pull requests con reviews, checks, comments

2. **Projects v2**
   - Obtener proyectos y sus items
   - Leer/escribir campos personalizados
   - Gestionar iteraciones y sprints

3. **Reportes y métricas**
   - Agregaciones complejas
   - Filtros avanzados
   - Datos de múltiples fuentes en una query

4. **Reducir rate limiting**
   - Menos requests = menos riesgo de rate limit
   - Más eficiente con el límite de puntos

### ⚠️ Considerar REST API para:

1. **Operaciones simples de escritura**
   - Crear/actualizar issues (REST es más directo)
   - Crear/actualizar PRs
   - Operaciones de mutación simples

2. **APIs que no tienen equivalente GraphQL**
   - Algunas APIs de GitHub Actions
   - Webhooks
   - Releases (parcialmente soportado)

## 📝 Scripts Migrados

- ✅ `scripts/weekly_report_graphql.py` - Versión GraphQL del reporte semanal
- ✅ `scripts/github_graphql.py` - Módulo helper principal

## 🔗 Referencias

- [GitHub GraphQL API Docs](https://docs.github.com/en/graphql)
- [GraphQL Explorer](https://docs.github.com/en/graphql/overview/explorer)
- [Projects v2 API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)

## 💡 Tips y Mejores Prácticas

1. **Usa paginación para grandes datasets**
   ```python
   all_issues = gh.get_all_issues_paginated(...)  # Maneja paginación automáticamente
   ```

2. **Filtra en la query, no en Python**
   ```python
   # ✅ Mejor: Filtrar en GraphQL
   issues = gh.get_issues_with_details(labels=["bug"])
   
   # ❌ Peor: Obtener todas y filtrar en Python
   all_issues = gh.get_all_issues_paginated()
   bug_issues = [i for i in all_issues if "bug" in [l["name"] for l in i["labels"]["nodes"]]]
   ```

3. **Reutiliza el cliente GraphQL**
   ```python
   gh = GitHubGraphQL()  # Crear una vez
   issues = gh.get_issues_with_details(...)
   commits = gh.execute_query(commits_query, ...)
   ```

4. **Maneja errores de rate limiting**
   ```python
   try:
       data = gh.execute_query(query, variables)
   except RuntimeError as e:
       if "rate limit" in str(e).lower():
           # Esperar y reintentar
           time.sleep(60)
           data = gh.execute_query(query, variables)
   ```

