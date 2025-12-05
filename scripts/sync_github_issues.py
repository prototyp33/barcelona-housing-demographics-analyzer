#!/usr/bin/env python3
"""
Sincroniza el estado de issues de GitHub con documentación local.

Uso:
    # Actualizar PROJECT_METRICS.md con métricas actuales
    python scripts/sync_github_issues.py --update-docs
    
    # Generar reporte de métricas en consola
    python scripts/sync_github_issues.py --metrics
    
    # Ambos
    python scripts/sync_github_issues.py --update-docs --metrics

Requiere:
    - gh CLI instalado y autenticado
"""

import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def get_github_issues() -> List[Dict[str, Any]]:
    """Obtiene todas las issues del repositorio usando gh CLI."""
    try:
        result = subprocess.run(
            [
                "gh", "issue", "list",
                "--state", "all",
                "--limit", "1000",
                "--json", "number,title,state,labels,milestone,createdAt,closedAt"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error obteniendo issues: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando respuesta JSON: {e}")
        return []


def calculate_metrics(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula métricas de las issues."""
    open_issues = [i for i in issues if i["state"] == "OPEN"]
    closed_issues = [i for i in issues if i["state"] == "CLOSED"]
    
    # Agrupar por labels
    labels_count = defaultdict(int)
    for issue in open_issues:
        for label in issue.get("labels", []):
            label_name = label.get("name", "") if isinstance(label, dict) else str(label)
            if label_name:
                labels_count[label_name] += 1
    
    # Agrupar por milestone
    milestones_count = defaultdict(int)
    for issue in open_issues:
        milestone = issue.get("milestone")
        if milestone:
            milestone_title = milestone.get("title", "") if isinstance(milestone, dict) else str(milestone)
            if milestone_title:
                milestones_count[milestone_title] += 1
    
    # Calcular tiempo promedio de resolución
    resolution_times = []
    for issue in closed_issues:
        if issue.get("closedAt") and issue.get("createdAt"):
            try:
                created = datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00"))
                closed = datetime.fromisoformat(issue["closedAt"].replace("Z", "+00:00"))
                delta = (closed - created).days
                resolution_times.append(delta)
            except (ValueError, TypeError):
                pass
    
    avg_resolution = (
        sum(resolution_times) / len(resolution_times)
        if resolution_times else 0
    )
    
    # Identificar issues por prioridad
    priority_count = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    for issue in open_issues:
        labels = [
            (l.get("name", "") if isinstance(l, dict) else str(l)).lower()
            for l in issue.get("labels", [])
        ]
        if "priority-critical" in labels or any("critical" in l for l in labels):
            priority_count["critical"] += 1
        elif "priority-high" in labels or any("high" in l for l in labels):
            priority_count["high"] += 1
        elif "priority-medium" in labels or any("medium" in l for l in labels):
            priority_count["medium"] += 1
        elif "priority-low" in labels or any("low" in l for l in labels):
            priority_count["low"] += 1
    
    return {
        "total": len(issues),
        "open": len(open_issues),
        "closed": len(closed_issues),
        "labels": dict(labels_count),
        "milestones": dict(milestones_count),
        "priority": priority_count,
        "avg_resolution_days": round(avg_resolution, 1),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def update_project_metrics(metrics: Dict[str, Any]) -> None:
    """Actualiza PROJECT_METRICS.md con métricas actuales."""
    metrics_file = Path("docs/PROJECT_METRICS.md")
    
    if not metrics_file.exists():
        print(f"⚠️  {metrics_file} no existe, creando nuevo archivo...")
    
    # Generar contenido de métricas
    content = f"""# Métricas del Proyecto Barcelona Housing Demographics Analyzer

**Última actualización:** {metrics['generated_at']}  
**Generado automáticamente por:** `scripts/sync_github_issues.py`

---

## 📊 Issue Management KPIs

| Métrica | Valor Actual | Objetivo | Estado |
|---------|--------------|----------|--------|
| **Total de Issues** | {metrics['total']} | - | ℹ️ |
| **Issues Abiertas** | {metrics['open']} | < 20 | {'✅' if metrics['open'] < 20 else '🟡' if metrics['open'] < 30 else '🔴'} |
| **Issues Cerradas** | {metrics['closed']} | - | ℹ️ |
| **Tiempo Promedio Resolución** | {metrics['avg_resolution_days']} días | < 5 días | {'✅' if metrics['avg_resolution_days'] < 5 else '🟡' if metrics['avg_resolution_days'] < 10 else '🔴'} |

---

## 🎯 Issues por Prioridad

| Prioridad | Cantidad | Estado |
|-----------|----------|--------|
| 🔴 Crítica | {metrics['priority']['critical']} | {'✅' if metrics['priority']['critical'] == 0 else '🔴'} |
| 🟡 Alta | {metrics['priority']['high']} | {'✅' if metrics['priority']['high'] < 5 else '🟡'} |
| 🟢 Media | {metrics['priority']['medium']} | ℹ️ |
| ⚪ Baja | {metrics['priority']['low']} | ℹ️ |

---

## 📋 Issues por Milestone

| Milestone | Issues Abiertas |
|-----------|-----------------|
"""
    
    if metrics['milestones']:
        for milestone, count in sorted(metrics['milestones'].items()):
            content += f"| {milestone} | {count} |\n"
    else:
        content += "| (Sin asignar) | - |\n"
    
    content += """
---

## 🏷️ Issues por Categoría (Labels)

| Label | Cantidad |
|-------|----------|
"""
    
    # Ordenar labels por cantidad
    sorted_labels = sorted(
        metrics['labels'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for label, count in sorted_labels[:15]:  # Top 15 labels
        content += f"| `{label}` | {count} |\n"
    
    content += f"""
---

## 📈 Tendencias

### Distribución Visual de Labels

```
"""
    
    # Gráfico de barras ASCII
    max_count = max(metrics['labels'].values()) if metrics['labels'] else 1
    for label, count in sorted_labels[:10]:
        bar_length = int((count / max_count) * 30)
        bar = "█" * bar_length
        content += f"{label:25s} {bar} {count}\n"
    
    content += f"""```

---

## 🔄 Actualización

Para actualizar estas métricas:

```bash
make sync-issues
# o
python3 scripts/sync_github_issues.py --update-docs --metrics
```

---

*Generado automáticamente el {metrics['generated_at']}*
"""
    
    metrics_file.write_text(content, encoding="utf-8")
    print(f"✅ {metrics_file} actualizado con métricas")


def generate_metrics_report(metrics: Dict[str, Any]) -> None:
    """Genera reporte detallado de métricas en consola."""
    print("\n" + "=" * 60)
    print("📊 REPORTE DE MÉTRICAS DE ISSUES")
    print("=" * 60)
    print(f"\nGenerado: {metrics['generated_at']}\n")
    
    print(f"📈 Totales:")
    print(f"   Total de issues: {metrics['total']}")
    print(f"   ├─ Abiertas: {metrics['open']}")
    print(f"   └─ Cerradas: {metrics['closed']}")
    print(f"\n⏱️  Tiempo promedio de resolución: {metrics['avg_resolution_days']} días")
    
    print("\n🎯 Por Prioridad:")
    print(f"   🔴 Crítica: {metrics['priority']['critical']}")
    print(f"   🟡 Alta: {metrics['priority']['high']}")
    print(f"   🟢 Media: {metrics['priority']['medium']}")
    print(f"   ⚪ Baja: {metrics['priority']['low']}")
    
    if metrics['milestones']:
        print("\n📅 Por Milestone:")
        for milestone, count in sorted(metrics['milestones'].items()):
            print(f"   {milestone}: {count}")
    
    print("\n📋 Por Categoría (top 10):")
    sorted_labels = sorted(
        metrics['labels'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    max_count = max(metrics['labels'].values()) if metrics['labels'] else 1
    for label, count in sorted_labels[:10]:
        bar_length = int((count / max_count) * 20)
        bar = "█" * bar_length
        print(f"   {label:25s} {bar} {count}")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza issues de GitHub con documentación local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Actualizar PROJECT_METRICS.md
  python scripts/sync_github_issues.py --update-docs
  
  # Generar reporte en consola
  python scripts/sync_github_issues.py --metrics
  
  # Ambos
  python scripts/sync_github_issues.py --update-docs --metrics
        """
    )
    parser.add_argument(
        "--update-docs",
        action="store_true",
        help="Actualiza PROJECT_METRICS.md con métricas"
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Genera reporte de métricas en consola"
    )
    
    args = parser.parse_args()
    
    if not (args.update_docs or args.metrics):
        parser.print_help()
        print("\n⚠️  Especifica al menos una opción: --update-docs o --metrics")
        return
    
    # Obtener issues
    print("📥 Obteniendo issues de GitHub...")
    issues = get_github_issues()
    
    if not issues:
        print("⚠️  No se pudieron obtener issues o el repositorio está vacío")
        return
    
    print(f"✅ {len(issues)} issues obtenidas")
    
    # Calcular métricas
    metrics = calculate_metrics(issues)
    
    # Ejecutar acciones solicitadas
    if args.metrics:
        generate_metrics_report(metrics)
    
    if args.update_docs:
        update_project_metrics(metrics)


if __name__ == "__main__":
    main()

