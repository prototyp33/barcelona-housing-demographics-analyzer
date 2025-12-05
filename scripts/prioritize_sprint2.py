#!/usr/bin/env python3
"""
Prioriza issues del Sprint 2 para trabajar esta semana.

Uso:
    python scripts/prioritize_sprint2.py
"""

import json
import subprocess
from typing import List, Dict, Any


def get_sprint2_issues() -> List[Dict[str, Any]]:
    """Obtiene issues del Sprint 2."""
    try:
        result = subprocess.run(
            [
                "gh", "issue", "list",
                "--milestone", "Sprint 2 - Calidad de Código",
                "--state", "open",
                "--limit", "100",
                "--json", "number,title,labels,body"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error obteniendo issues: {e.stderr}")
        return []


def extract_time_estimate(body: str) -> int:
    """Extrae estimación de tiempo en horas."""
    import re
    
    # Buscar patrones como "2 horas", "3 días", etc.
    hour_match = re.search(r'(\d+)\s*horas?', body, re.IGNORECASE)
    if hour_match:
        return int(hour_match.group(1))
    
    day_match = re.search(r'(\d+)\s*días?', body, re.IGNORECASE)
    if day_match:
        return int(day_match.group(1)) * 8  # Asumir 8 horas por día
    
    return 0


def prioritize_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prioriza issues según criterios."""
    prioritized = []
    
    for issue in issues:
        labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
        body = issue.get("body", "")
        
        # Calcular score de prioridad
        score = 0
        
        # Prioridad por labels
        if "priority-critical" in labels:
            score += 100
        elif "priority-high" in labels:
            score += 50
        elif "priority-medium" in labels:
            score += 25
        
        # Penalizar issues grandes (>8 horas)
        time_estimate = extract_time_estimate(body)
        if time_estimate > 8:
            score -= 20
        elif time_estimate > 0:
            score += 10  # Bonus para issues con estimación
        
        # Bonus para issues con label "bug"
        if "bug" in labels:
            score += 15
        
        # Bonus para issues con label "code-quality"
        if "code-quality" in labels:
            score += 10
        
        prioritized.append({
            **issue,
            "priority_score": score,
            "time_estimate": time_estimate
        })
    
    # Ordenar por score descendente
    prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return prioritized


def main():
    print("📥 Obteniendo issues del Sprint 2...")
    issues = get_sprint2_issues()
    
    if not issues:
        print("⚠️  No se encontraron issues del Sprint 2")
        return
    
    print(f"✅ {len(issues)} issues encontradas\n")
    
    # Priorizar
    prioritized = prioritize_issues(issues)
    
    # Mostrar top 7 recomendadas
    print("=" * 70)
    print("🎯 TOP 7 ISSUES RECOMENDADAS PARA ESTA SEMANA")
    print("=" * 70)
    
    for i, issue in enumerate(prioritized[:7], 1):
        labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
        priority_labels = [l for l in labels if "priority" in l.lower()]
        
        print(f"\n{i}. #{issue['number']}: {issue['title']}")
        print(f"   Score: {issue['priority_score']}")
        print(f"   Estimación: {issue['time_estimate']} horas" if issue['time_estimate'] > 0 else "   Estimación: No especificada")
        if priority_labels:
            print(f"   Prioridad: {', '.join(priority_labels)}")
        print(f"   URL: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/{issue['number']}")
    
    print("\n" + "=" * 70)
    print("\n💡 Recomendación: Trabajar en estas 5-7 issues esta semana")
    print("   Esto representa aproximadamente 20-30 horas de trabajo")
    
    # Generar lista para Project Board
    print("\n📋 Lista de números para copiar:")
    issue_numbers = [str(issue["number"]) for issue in prioritized[:7]]
    print(f"   {', '.join(issue_numbers)}")


if __name__ == "__main__":
    main()

