#!/usr/bin/env python3
"""
Setup de campos para GitHub Projects v2.
Crea los campos necesarios si no existen.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Asegurar imports locales
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.github_graphql import GitHubGraphQL
from project_automation_v2 import get_project_info, PROJECT_NUMBER, PROJECT_OWNER

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Definición de campos
REQUIRED_FIELDS = {
    "Impacto": {
        "dataType": "SINGLE_SELECT",
        "options": [
            {"name": "High", "color": "RED", "description": "High impact"},
            {"name": "Medium", "color": "ORANGE", "description": "Medium impact"},
            {"name": "Low", "color": "GREEN", "description": "Low impact"},
            {"name": "Critical", "color": "PURPLE", "description": "Critical impact"},
        ],
    },
    "Fuente": {
        "dataType": "SINGLE_SELECT",
        "options": [
            {"name": "IDESCAT", "color": "BLUE", "description": "Institut d'Estadística de Catalunya"},
            {"name": "Incasòl", "color": "YELLOW", "description": "Institut Català del Sol"},
            {"name": "OpenData BCN", "color": "RED", "description": "Open Data Barcelona"},
            {"name": "Portal Dades", "color": "PURPLE", "description": "Portal de Dades Obertes"},
            {"name": "Internal", "color": "GRAY", "description": "Internal data"},
            {"name": "Idealista", "color": "GREEN", "description": "Idealista data"},
        ],
    },
    "Sprint": {
        "dataType": "ITERATION",
        "configuration": {
            "duration": 14,
            "startDay": 1,
        }
    },
    "KPI": {
        "dataType": "TEXT",
    },
    "Owner": {
        "dataType": "SINGLE_SELECT",
        "options": [
            {"name": "Data Engineering", "color": "BLUE", "description": "Data Engineering Team"},
            {"name": "Data Analysis", "color": "GREEN", "description": "Data Analysis Team"},
            {"name": "Product", "color": "PURPLE", "description": "Product Team"},
            {"name": "Infraestructure", "color": "GRAY", "description": "Infraestructure Team"},
        ],
    },
    "Estado DQC": {
        "dataType": "SINGLE_SELECT",
        "options": [
            {"name": "Passed", "color": "GREEN", "description": "Data Quality Check Passed"},
            {"name": "Failed", "color": "RED", "description": "Data Quality Check Failed"},
            {"name": "Pending", "color": "YELLOW", "description": "Data Quality Check Pending"},
            {"name": "N/A", "color": "GRAY", "description": "Not Applicable"},
        ],
    },
}

def create_field(gh: GitHubGraphQL, project_id: str, name: str, config: Dict[str, Any]) -> None:
    """Crea un campo en el proyecto."""
    logger.info(f"Creando campo '{name}'...")
    
    data_type = config["dataType"]
    
    # Construir input
    input_args = f'projectId: "{project_id}", name: "{name}", dataType: {data_type}'
    
    if data_type == "SINGLE_SELECT" and "options" in config:
        # Formatear opciones
        options_str = ", ".join(
            [f'{{name: "{opt["name"]}", color: {opt["color"]}, description: "{opt["description"]}"}}' for opt in config["options"]]
        )
        input_args += f', singleSelectOptions: [{options_str}]'
        
    query = f"""
    mutation {{
      createProjectV2Field(input: {{
        {input_args}
      }}) {{
        projectV2Field {{
          ... on ProjectV2FieldCommon {{
            id
            name
          }}
          ... on ProjectV2SingleSelectField {{
            id
            name
          }}
          ... on ProjectV2IterationField {{
            id
            name
          }}
        }}
      }}
    }}
    """
    
    try:
        gh.execute_query(query)
        logger.info(f"✅ Campo '{name}' creado exitosamente.")
    except Exception as e:
        logger.error(f"❌ Error creando campo '{name}': {e}")

def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN no encontrado.")
        sys.exit(1)

    gh = GitHubGraphQL(token=token)
    
    logger.info(f"Obteniendo info del proyecto #{PROJECT_NUMBER} de {PROJECT_OWNER}...")
    try:
        project_info = get_project_info(gh)
    except Exception as e:
        logger.error(f"Error obteniendo proyecto: {e}")
        sys.exit(1)
        
    project_id = project_info["project_id"]
    existing_fields = project_info["fields"] # Dict[lowercase_name, field_info]
    
    logger.info(f"Campos existentes: {list(existing_fields.keys())}")
    
    for name, config in REQUIRED_FIELDS.items():
        if name.lower() in existing_fields:
            logger.info(f"Campo '{name}' ya existe. Saltando.")
            # TODO: Podríamos verificar si faltan opciones y añadirlas, pero por ahora asumimos que está bien.
        else:
            create_field(gh, project_id, name, config)

if __name__ == "__main__":
    main()
