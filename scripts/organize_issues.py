#!/usr/bin/env python3
"""
Script para organizar y limpiar issues abiertas.

Uso:
    # Analizar issues sin milestone
    python scripts/organize_issues.py --analyze
    
    # Etiquetar issues obsoletas (>90 días sin actividad)
    python scripts/organize_issues.py --mark-stale
    
    # Asignar milestones a issues sin asignar
    python scripts/organize_issues.py --assign-milestones
"""

import argparse
import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_all_issues() -> List[Dict[str, Any]]:
    """Obtiene todas las issues abiertas."""
    try:
        result = subprocess.run(
            [
                "gh", "issue", "list",
                "--state", "all",
                "--limit", "1000",
                "--json", "number,title,labels,milestone,updatedAt,createdAt,state,body"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error obteniendo issues: {e.stderr}")
        return []


def analyze_issues(issues: List[Dict[str, Any]]) -> None:
    """Analiza issues y muestra estadísticas."""
    open_issues = [i for i in issues if i["state"] == "OPEN"]
    closed_issues = [i for i in issues if i["state"] == "CLOSED"]
    
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS DE ISSUES")
    print("=" * 60)
    
    print(f"\n📈 Totales:")
    print(f"   Abiertas: {len(open_issues)}")
    print(f"   Cerradas: {len(closed_issues)}")
    
    # Issues sin milestone
    without_milestone = [i for i in open_issues if not i.get("milestone")]
    print(f"\n⚠️  Issues sin milestone: {len(without_milestone)}")
    if without_milestone:
        print("\n   Top 10:")
        for issue in without_milestone[:10]:
            print(f"   - #{issue['number']}: {issue['title'][:60]}")
    
    # Issues obsoletas (>90 días sin actividad)
    now = datetime.now()
    stale_threshold = timedelta(days=90)
    stale_issues = []
    
    for issue in open_issues:
        updated = datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00"))
        if now - updated.replace(tzinfo=None) > stale_threshold:
            stale_issues.append(issue)
    
    print(f"\n🕐 Issues obsoletas (>90 días sin actividad): {len(stale_issues)}")
    if stale_issues:
        print("\n   Top 10:")
        for issue in stale_issues[:10]:
            updated = datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00"))
            days_ago = (now - updated.replace(tzinfo=None)).days
            print(f"   - #{issue['number']}: {issue['title'][:50]} ({days_ago} días)")
    
    # Issues por milestone
    milestone_count = {}
    for issue in open_issues:
        milestone = issue.get("milestone")
        if milestone:
            title = milestone.get("title", "Unknown")
            milestone_count[title] = milestone_count.get(title, 0) + 1
        else:
            milestone_count["Sin milestone"] = milestone_count.get("Sin milestone", 0) + 1
    
    print(f"\n📅 Issues por milestone:")
    for milestone, count in sorted(milestone_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   {milestone}: {count}")
    
    # Issues por prioridad
    priority_count = {"critical": 0, "high": 0, "medium": 0, "low": 0, "none": 0}
    for issue in open_issues:
        labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
        if any("critical" in l.lower() for l in labels):
            priority_count["critical"] += 1
        elif any("high" in l.lower() for l in labels):
            priority_count["high"] += 1
        elif any("medium" in l.lower() for l in labels):
            priority_count["medium"] += 1
        elif any("low" in l.lower() for l in labels):
            priority_count["low"] += 1
        else:
            priority_count["none"] += 1
    
    print(f"\n🎯 Issues por prioridad:")
    print(f"   🔴 Crítica: {priority_count['critical']}")
    print(f"   🟡 Alta: {priority_count['high']}")
    print(f"   🟢 Media: {priority_count['medium']}")
    print(f"   ⚪ Baja: {priority_count['low']}")
    print(f"   ⚪ Sin prioridad: {priority_count['none']}")
    
    print("\n" + "=" * 60)


def mark_stale_issues(issues: List[Dict[str, Any]], dry_run: bool = True) -> None:
    """Etiqueta issues obsoletas con label 'stale'."""
    now = datetime.now()
    stale_threshold = timedelta(days=90)
    
    open_issues = [i for i in issues if i["state"] == "OPEN"]
    stale_issues = []
    
    for issue in open_issues:
        updated = datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00"))
        if now - updated.replace(tzinfo=None) > stale_threshold:
            stale_issues.append(issue)
    
    if not stale_issues:
        print("✅ No hay issues obsoletas para etiquetar")
        return
    
    print(f"\n🕐 Encontradas {len(stale_issues)} issues obsoletas")
    
    if dry_run:
        print("\n🔍 [DRY RUN] Issues que se etiquetarían como 'stale':")
        for issue in stale_issues[:20]:
            updated = datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00"))
            days_ago = (now - updated.replace(tzinfo=None)).days
            print(f"   - #{issue['number']}: {issue['title'][:50]} ({days_ago} días)")
        print("\n💡 Ejecuta sin --dry-run para aplicar cambios")
        return
    
    # Verificar que existe el label 'stale'
    try:
        subprocess.run(
            ["gh", "label", "list"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        print("⚠️  No se pudo verificar labels. Creando label 'stale'...")
        subprocess.run(
            ["gh", "label", "create", "stale", "--description", "Issue obsoleta (>90 días sin actividad)", "--color", "ededed"],
            check=False
        )
    
    # Etiquetar issues
    for issue in stale_issues:
        try:
            subprocess.run(
                ["gh", "issue", "edit", str(issue["number"]), "--add-label", "stale"],
                capture_output=True,
                check=True
            )
            print(f"✅ #{issue['number']} etiquetada como stale")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error etiquetando #{issue['number']}: {e.stderr}")


def assign_milestones_to_issues(issues: List[Dict[str, Any]], dry_run: bool = True) -> None:
    """Asigna milestones a issues sin asignar basándose en labels."""
    open_issues = [i for i in issues if i["state"] == "OPEN" and not i.get("milestone")]
    
    if not open_issues:
        print("✅ Todas las issues tienen milestone asignado")
        return
    
    print(f"\n⚠️  Encontradas {len(open_issues)} issues sin milestone")
    
    # Obtener milestones disponibles usando API
    try:
        result = subprocess.run(
            ["gh", "api", "repos/:owner/:repo/milestones", "--jq", ".[] | {number: .number, title: .title}"],
            capture_output=True,
            text=True,
            check=True
        )
        milestones_data = result.stdout.strip().split('\n')
        milestones = []
        milestone_map = {}
        
        for line in milestones_data:
            if line.strip():
                milestone = json.loads(line)
                milestones.append(milestone)
                milestone_map[milestone["title"]] = milestone["number"]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"⚠️  Error obteniendo milestones: {e}")
        print("   Continuando sin asignación automática de milestones")
        return
    
    # Mapear labels a milestones
    label_to_milestone = {
        "sprint-1": "Quick Wins Foundation",
        "sprint-2": "Core ML Engine",
        "sprint-3": "Data Expansion",
        "sprint-4": "Differentiation Showcase",
    }
    
    if dry_run:
        print("\n🔍 [DRY RUN] Issues que recibirían milestone:")
        for issue in open_issues[:20]:
            labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
            assigned_milestone = None
            
            for label, milestone in label_to_milestone.items():
                if label in labels and milestone in milestone_map:
                    assigned_milestone = milestone
                    break
            
            if assigned_milestone:
                milestone_title = [m["title"] for m in milestones if m["number"] == assigned_milestone][0]
                print(f"   - #{issue['number']}: {issue['title'][:50]}")
                print(f"     → {milestone_title}")
            else:
                print(f"   - #{issue['number']}: {issue['title'][:50]} (sin milestone sugerido)")
        print("\n💡 Ejecuta sin --dry-run para aplicar cambios")
        return
    
    # Asignar milestones
    assigned = 0
    for issue in open_issues:
        labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
        
        for label, milestone_title in label_to_milestone.items():
            if label in labels and milestone_title in milestone_map:
                milestone_num = milestone_map[milestone_title]
                try:
                    subprocess.run(
                        ["gh", "issue", "edit", str(issue["number"]), "--milestone", str(milestone_num)],
                        capture_output=True,
                        check=True
                    )
                    print(f"✅ #{issue['number']} → {milestone_title}")
                    assigned += 1
                    break
                except subprocess.CalledProcessError as e:
                    print(f"❌ Error asignando milestone a #{issue['number']}: {e.stderr}")
    
    print(f"\n✅ {assigned} issues con milestone asignado")


def main():
    parser = argparse.ArgumentParser(
        description="Organiza y limpia issues del proyecto"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analiza issues y muestra estadísticas"
    )
    parser.add_argument(
        "--mark-stale",
        action="store_true",
        help="Etiqueta issues obsoletas (>90 días)"
    )
    parser.add_argument(
        "--assign-milestones",
        action="store_true",
        help="Asigna milestones a issues sin asignar"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview sin aplicar cambios (default: True)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Aplicar cambios (sobrescribe --dry-run)"
    )
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.mark_stale, args.assign_milestones]):
        parser.print_help()
        return
    
    # Obtener issues
    print("📥 Obteniendo issues de GitHub...")
    issues = get_all_issues()
    
    if not issues:
        print("⚠️  No se pudieron obtener issues")
        return
    
    print(f"✅ {len(issues)} issues obtenidas")
    
    dry_run = args.dry_run and not args.force
    
    # Ejecutar acciones
    if args.analyze:
        analyze_issues(issues)
    
    if args.mark_stale:
        mark_stale_issues(issues, dry_run=dry_run)
    
    if args.assign_milestones:
        assign_milestones_to_issues(issues, dry_run=dry_run)


if __name__ == "__main__":
    main()

