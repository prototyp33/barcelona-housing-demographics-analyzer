#!/usr/bin/env python3
"""
Genera métricas del proyecto desde Projects v2

Uso:
    python .github/scripts/project_metrics.py
    python .github/scripts/project_metrics.py --export-json metrics.json
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

# Añadir el directorio raíz al path para imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.github_graphql import GitHubGraphQL

# Configuración
ORG_NAME = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
PROJECT_NUMBER = 1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_project_metrics(gh: GitHubGraphQL) -> dict:
    """
    Obtiene métricas del proyecto.
    
    Returns:
        Dict con métricas agregadas
    """
    # Obtener proyecto
    project = gh.get_project_v2(
        owner=ORG_NAME,
        repo=REPO_NAME,
        project_number=PROJECT_NUMBER
    )
    
    if not project:
        raise ValueError(f"Proyecto #{PROJECT_NUMBER} no encontrado")
    
    project_id = project["id"]
    logger.info(f"Analizando proyecto: {project.get('title', 'Unknown')}")
    
    # Obtener todos los items (con paginación)
    all_items = []
    cursor = None
    
    while True:
        items_data = gh.get_project_items(
            project_id=project_id,
            limit=100,
            cursor=cursor
        )
        
        items = items_data.get("items", [])
        all_items.extend(items)
        
        page_info = items_data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        
        cursor = page_info.get("endCursor")
        logger.debug(f"Obtenidos {len(all_items)} items, continuando paginación...")
    
    logger.info(f"Total de items encontrados: {len(all_items)}")
    
    # Analizar métricas
    metrics = {
        "total_items": len(all_items),
        "by_status": defaultdict(int),
        "by_sprint": defaultdict(int),
        "by_fuente": defaultdict(int),
        "by_impacto": defaultdict(int),
        "by_dqc": defaultdict(int),
        "open_issues": 0,
        "closed_issues": 0,
        "by_owner": defaultdict(int),
    }
    
    for item in all_items:
        content = item.get("content", {})
        
        # Estado del issue
        if content:
            state = content.get("state", "UNKNOWN")
            if state == "OPEN":
                metrics["open_issues"] += 1
            elif state == "CLOSED":
                metrics["closed_issues"] += 1
        
        # Analizar campos personalizados
        field_values_raw = item.get("fieldValues", {})
        if isinstance(field_values_raw, dict):
            field_values = field_values_raw.get("nodes", [])
        else:
            field_values = field_values_raw if isinstance(field_values_raw, list) else []
        
        for field_value in field_values:
            field = field_value.get("field", {})
            field_name = field.get("name")
            
            if not field_name:
                continue
            
            # Single select fields
            if "name" in field_value:  # ProjectV2ItemFieldSingleSelectValue
                value_name = field_value.get("name")
                
                if field_name == "Sprint":
                    metrics["by_sprint"][value_name or "Sin Sprint"] += 1
                elif field_name == "Fuente de Datos":
                    metrics["by_fuente"][value_name or "Sin Fuente"] += 1
                elif field_name == "Impacto":
                    metrics["by_impacto"][value_name or "Sin Impacto"] += 1
                elif field_name == "Estado DQC":
                    metrics["by_dqc"][value_name or "Sin Estado"] += 1
            
            # Text fields
            elif "text" in field_value:  # ProjectV2ItemFieldTextValue
                if field_name == "Owner":
                    owner = field_value.get("text", "").strip()
                    if owner:
                        metrics["by_owner"][owner] += 1
    
    return metrics


def print_report(metrics: dict):
    """Imprime reporte de métricas."""
    print("=" * 60)
    print(f"📊 MÉTRICAS DEL PROYECTO - {ORG_NAME}/{REPO_NAME}")
    print("=" * 60)
    
    print(f"\n📈 Resumen General:")
    print(f"  Total de items: {metrics['total_items']}")
    print(f"  Issues abiertos: {metrics['open_issues']}")
    print(f"  Issues cerrados: {metrics['closed_issues']}")
    
    if metrics['total_items'] > 0:
        completion_rate = (metrics['closed_issues'] / metrics['total_items']) * 100
        print(f"  Tasa de completitud: {completion_rate:.1f}%")
    
    if metrics["by_sprint"]:
        print(f"\n🎯 Por Sprint:")
        for sprint in sorted(metrics["by_sprint"].keys()):
            count = metrics["by_sprint"][sprint]
            print(f"  {sprint}: {count}")
    
    if metrics["by_fuente"]:
        print(f"\n📁 Por Fuente de Datos:")
        for fuente in sorted(metrics["by_fuente"].keys()):
            count = metrics["by_fuente"][fuente]
            print(f"  {fuente}: {count}")
    
    if metrics["by_impacto"]:
        print(f"\n⚡ Por Impacto:")
        impact_order = ["High", "Medium", "Low"]
        for impacto in impact_order:
            if impacto in metrics["by_impacto"]:
                count = metrics["by_impacto"][impacto]
                print(f"  {impacto}: {count}")
        # Otros impactos
        for impacto, count in metrics["by_impacto"].items():
            if impacto not in impact_order:
                print(f"  {impacto}: {count}")
    
    if metrics["by_dqc"]:
        print(f"\n✅ Por Estado DQC:")
        for estado in sorted(metrics["by_dqc"].keys()):
            count = metrics["by_dqc"][estado]
            print(f"  {estado}: {count}")
    
    if metrics["by_owner"]:
        print(f"\n👤 Por Owner:")
        for owner in sorted(metrics["by_owner"].keys()):
            count = metrics["by_owner"][owner]
            print(f"  {owner}: {count}")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Genera métricas del proyecto desde Projects v2"
    )
    parser.add_argument(
        "--export-json",
        type=Path,
        help="Exportar métricas a archivo JSON"
    )
    
    args = parser.parse_args()
    
    # Obtener token
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN no encontrado en variables de entorno")
        sys.exit(1)
    
    # Inicializar cliente GraphQL
    gh = GitHubGraphQL(token=token)
    
    try:
        # Obtener métricas
        metrics = get_project_metrics(gh)
        
        # Imprimir reporte
        print_report(metrics)
        
        # Exportar si se solicita
        if args.export_json:
            args.export_json.parent.mkdir(parents=True, exist_ok=True)
            with open(args.export_json, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Métricas exportadas a: {args.export_json}")
    
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

