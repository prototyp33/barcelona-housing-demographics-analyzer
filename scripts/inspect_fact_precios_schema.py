import os
import psycopg2

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
        user=os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        port=int(os.getenv("POSTGRES_PORT", "5432"))
    )

def main():
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- SCHEMA FOR fact_precios ---")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'fact_precios'
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"Column: {row[0]}, Type: {row[1]}")
        
    print("\n--- UNIQUE CONSTRAINTS / INDEXES ON fact_precios ---")
    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'fact_precios';
    """)
    for row in cur.fetchall():
        print(f"Index: {row[0]}")
        print(f"Def: {row[1]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
