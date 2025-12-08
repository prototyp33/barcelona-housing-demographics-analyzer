#!/usr/bin/env python3
"""
Create minimal dim_barrios data for CI/testing purposes.
Inserts the 73 Barcelona barrios with basic information.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Lista de los 73 barrios de Barcelona con sus distritos
# Formato: (barrio_id, barrio_nombre, distrito_id, distrito_nombre)
BARRIOS = [
    (1, "el Raval", 1, "Ciutat Vella"),
    (2, "el Barri Gòtic", 1, "Ciutat Vella"),
    (3, "la Barceloneta", 1, "Ciutat Vella"),
    (4, "Sant Pere, Santa Caterina i la Ribera", 1, "Ciutat Vella"),
    (5, "el Fort Pienc", 2, "Eixample"),
    (6, "la Sagrada Família", 2, "Eixample"),
    (7, "la Dreta de l'Eixample", 2, "Eixample"),
    (8, "l'Antiga Esquerra de l'Eixample", 2, "Eixample"),
    (9, "la Nova Esquerra de l'Eixample", 2, "Eixample"),
    (10, "Sant Antoni", 2, "Eixample"),
    (11, "el Poblenou", 3, "Sant Martí"),
    (12, "la Vila Olímpica del Poblenou", 3, "Sant Martí"),
    (13, "el Parc i la Llacuna del Poblenou", 3, "Sant Martí"),
    (14, "la Verneda i la Pau", 3, "Sant Martí"),
    (15, "el Besòs i el Maresme", 3, "Sant Martí"),
    (16, "Provençals del Poblenou", 3, "Sant Martí"),
    (17, "Sant Martí de Provençals", 3, "Sant Martí"),
    (18, "la Clota", 3, "Sant Martí"),
    (19, "el Camp de l'Arpa del Clot", 3, "Sant Martí"),
    (20, "el Clot", 3, "Sant Martí"),
    (21, "el Poblenou", 3, "Sant Martí"),
    (22, "Diagonal Mar i el Front Marítim del Poblenou", 3, "Sant Martí"),
    (23, "Vallbona", 4, "Nou Barris"),
    (24, "Ciutat Meridiana", 4, "Nou Barris"),
    (25, "la Guineueta", 4, "Nou Barris"),
    (26, "Canyelles", 4, "Nou Barris"),
    (27, "les Roquetes", 4, "Nou Barris"),
    (28, "Verdun", 4, "Nou Barris"),
    (29, "la Prosperitat", 4, "Nou Barris"),
    (30, "la Trinitat Nova", 4, "Nou Barris"),
    (31, "Torre Baró", 4, "Nou Barris"),
    (32, "el Turó de la Peira", 4, "Nou Barris"),
    (33, "Porta", 4, "Nou Barris"),
    (34, "Vilapicina i la Torre Llobeta", 4, "Nou Barris"),
    (35, "el Coll", 5, "Gràcia"),
    (36, "la Salut", 5, "Gràcia"),
    (37, "Vallcarca i els Penitents", 5, "Gràcia"),
    (38, "el Camp d'en Grassot i Gràcia Nova", 5, "Gràcia"),
    (39, "Gràcia", 5, "Gràcia"),
    (40, "el Putxet i el Farró", 6, "Sarrià-Sant Gervasi"),
    (41, "Vallvidrera, el Tibidabo i les Planes", 6, "Sarrià-Sant Gervasi"),
    (42, "les Tres Torres", 6, "Sarrià-Sant Gervasi"),
    (43, "Sant Gervasi - la Bonanova", 6, "Sarrià-Sant Gervasi"),
    (44, "Sant Gervasi - Galvany", 6, "Sarrià-Sant Gervasi"),
    (45, "Sarrià", 6, "Sarrià-Sant Gervasi"),
    (46, "Vallvidrera, el Tibidabo i les Planes", 6, "Sarrià-Sant Gervasi"),
    (47, "les Corts", 7, "Les Corts"),
    (48, "la Maternitat i Sant Ramon", 7, "Les Corts"),
    (49, "Pedralbes", 7, "Les Corts"),
    (50, "el Camp de l'Arpa del Clot", 8, "Sant Andreu"),
    (51, "Sant Andreu", 8, "Sant Andreu"),
    (52, "la Sagrera", 8, "Sant Andreu"),
    (53, "el Congrés i els Indians", 8, "Sant Andreu"),
    (54, "Navas", 8, "Sant Andreu"),
    (55, "el Bon Pastor", 8, "Sant Andreu"),
    (56, "Trinitat Vella", 8, "Sant Andreu"),
    (57, "Baró de Viver", 8, "Sant Andreu"),
    (58, "el Besòs", 8, "Sant Andreu"),
    (59, "Provençals", 8, "Sant Andreu"),
    (60, "la Marina del Prat Vermell", 9, "Sants-Montjuïc"),
    (61, "la Font de la Guatlla", 9, "Sants-Montjuïc"),
    (62, "Hostafrancs", 9, "Sants-Montjuïc"),
    (63, "la Bordeta", 9, "Sants-Montjuïc"),
    (64, "Sants - Badal", 9, "Sants-Montjuïc"),
    (65, "Sants", 9, "Sants-Montjuïc"),
    (66, "Poble-sec", 9, "Sants-Montjuïc"),
    (67, "la Marina de Port", 9, "Sants-Montjuïc"),
    (68, "la Maternitat i Sant Ramon", 9, "Sants-Montjuïc"),
    (69, "Montjuïc", 9, "Sants-Montjuïc"),
    (70, "Zona Franca - Port", 9, "Sants-Montjuïc"),
    (71, "el Poble-sec", 9, "Sants-Montjuïc"),
    (72, "la Marina del Prat Vermell", 9, "Sants-Montjuïc"),
    (73, "el Camp de l'Arpa del Clot", 9, "Sants-Montjuïc"),
]

def normalize_name(name: str) -> str:
    """Normaliza el nombre del barrio para matching."""
    return name.lower().strip().replace("'", "").replace(" ", "_")


def create_minimal_barrios(db_path: Path = None):
    """Crea los 73 barrios básicos en dim_barrios."""
    if db_path is None:
        db_path = Path("data/processed/database.db")
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    try:
        timestamp = datetime.now().isoformat()
        
        for barrio_id, barrio_nombre, distrito_id, distrito_nombre in BARRIOS:
            barrio_nombre_normalizado = normalize_name(barrio_nombre)
            codi_barri = str(barrio_id).zfill(2)
            codi_districte = str(distrito_id).zfill(2)
            
            conn.execute("""
                INSERT OR IGNORE INTO dim_barrios (
                    barrio_id, barrio_nombre, barrio_nombre_normalizado,
                    distrito_id, distrito_nombre, municipio, ambito,
                    codi_barri, codi_districte,
                    source_dataset, etl_created_at, etl_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                barrio_id, barrio_nombre, barrio_nombre_normalizado,
                distrito_id, distrito_nombre, "Barcelona", "barri",
                codi_barri, codi_districte,
                "minimal_ci_setup", timestamp, timestamp
            ))
        
        conn.commit()
        print(f"✅ Created {len(BARRIOS)} barrios in dim_barrios")
        
    finally:
        conn.close()


if __name__ == "__main__":
    create_minimal_barrios()

