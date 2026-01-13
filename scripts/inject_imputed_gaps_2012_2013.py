import os
import logging
import psycopg2
from datetime import datetime

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE RATIOS (Calculados históricamente 2014-2024) ---
# Adjustment_Factor = Avg_Barrio / Avg_Distrito
RATIOS = {
    '12': {'name': 'la Marina del Prat Vermell', 'ratio': 0.6062, 'barrio_id': 12},
    '42': {'name': 'la Clota', 'ratio': 0.9079, 'barrio_id': 42},
    '47': {'name': 'Can Peguera', 'ratio': 0.9762, 'barrio_id': 47},
    '56': {'name': 'Vallbona', 'ratio': 0.7858, 'barrio_id': 56},
    '58': {'name': 'Baró de Viver', 'ratio': 0.5263, 'barrio_id': 58}
}

# Gaps por año
GAPS = {
    2012: ['12', '42', '47', '56', '58'],
    2013: ['12', '42', '47']
}

def get_connection():
    """Establece conexión con PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
        user=os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        port=int(os.getenv("POSTGRES_PORT", "5432"))
    )

def main():
    try:
        conn = get_connection()
        cur = conn.cursor()
        logger.info("Conectado a PostgreSQL exitosamente.")

        # 1. Obtener precios medios por distrito para 2012 y 2013
        # Usamos dim_barrios para agrupar fact_precios por distrito
        query_distritos = """
            SELECT b.distrito_nombre, p.anio, AVG(p.precio_m2_venta)
            FROM fact_precios p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.anio IN (2012, 2013) AND p.precio_m2_venta > 0
            GROUP BY b.distrito_nombre, p.anio
        """
        cur.execute(query_distritos)
        dist_prices = {}
        for dist, anio, price in cur.fetchall():
            if anio not in dist_prices: dist_prices[anio] = {}
            dist_prices[anio][dist] = float(price)

        # 2. Preparar inserciones
        imputations = []
        etl_time = datetime.now().isoformat()
        
        for anio, codigos in GAPS.items():
            for codi in codigos:
                rule = RATIOS[codi]
                barrio_id = rule['barrio_id']
                
                # Obtener el nombre del distrito para este barrio
                cur.execute("SELECT distrito_nombre FROM dim_barrios WHERE barrio_id = %s", (barrio_id,))
                dist_res = cur.fetchone()
                if not dist_res: continue
                distrito_nombre = dist_res[0]
                
                if distrito_nombre in dist_prices.get(anio, {}):
                    price_dist = dist_prices[anio][distrito_nombre]
                    imputed_price = price_dist * rule['ratio']
                    
                    # Usamos una fecha real para el periodo para evitar errores de tipo en Postgres
                    # Formato YYYY-MM-DD
                    periodo_date = f"{anio}-01-01"
                    
                    imputations.append((
                        barrio_id, anio, periodo_date, imputed_price, 
                        'IMPUTACION_DISTRITO_RATIO', 'ETL_BACKFILLING', datetime.now()
                    ))
                    logger.info(f"Calculado: {rule['name']} ({anio}) -> {imputed_price:.2f} €/m2 (Distrito {distrito_nombre}: {price_dist:.2f} * {rule['ratio']})")

        # 3. Insertar en la base de datos
        if imputations:
            # Primero borramos registros previos de imputación para evitar duplicados
            # Esto es más seguro que ON CONFLICT dado el mismatch de tipos en 'trimestre' (timestamp vs int)
            delete_query = """
                DELETE FROM fact_precios 
                WHERE dataset_id = 'IMPUTACION_DISTRITO_RATIO' 
                AND anio IN (2012, 2013)
            """
            cur.execute(delete_query)
            
            insert_query = """
                INSERT INTO fact_precios (barrio_id, anio, periodo, precio_m2_venta, dataset_id, source, etl_loaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.executemany(insert_query, imputations)
            conn.commit()
            logger.info(f"Se han insertado {len(imputations)} registros de imputación en fact_precios.")
        else:
            logger.warning("No se generaron imputaciones.")

        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error durante la inyección: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
