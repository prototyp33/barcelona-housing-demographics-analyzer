import sqlite3
import pandas as pd
from pathlib import Path

def get_topographical_penalty(barrio_nombre, distrito_nombre):
    bn = str(barrio_nombre).lower()
    dn = str(distrito_nombre).lower()
    
    penalty = 0.0
    if 'nou barris' in dn: penalty += 0.4
    elif 'horta-guinardó' in dn: penalty += 0.35
    elif 'sarrià-sant gervasi' in dn: penalty += 0.25
    elif 'gràcia' in dn: penalty += 0.15
    
    if 'coll' in bn: penalty += 0.35
    elif 'vallbona' in bn or 'torre baró' in bn: penalty += 0.4
    elif 'carmel' in bn or 'teixonera' in bn: penalty += 0.3
    elif 'roquetes' in bn or 'trinitat nova' in bn: penalty += 0.25
    
    return min(penalty, 1.0)

db_path = Path('data/master.db')
if not db_path.exists():
    db_path = Path('data/processed/database.db')

conn = sqlite3.connect(db_path)

# Try to add column if not exists
try:
    conn.execute("ALTER TABLE fact_catastro_avanzado ADD COLUMN indice_penalizacion_topografica REAL")
    print("Column added to fact_catastro_avanzado")
except sqlite3.OperationalError:
    print("Column already exists or table not found")

# Get barrios info
barrios = pd.read_sql("SELECT barrio_id, barrio_nombre, distrito_nombre FROM dim_barrios", conn)

# Update each row
for _, row in barrios.iterrows():
    penalty = get_topographical_penalty(row['barrio_nombre'], row['distrito_nombre'])
    conn.execute(
        "UPDATE fact_catastro_avanzado SET indice_penalizacion_topografica = ? WHERE barrio_id = ?",
        (penalty, row['barrio_id'])
    )

conn.commit()
conn.close()
print("✅ Topographical Penalty Index updated for all neighborhoods.")
