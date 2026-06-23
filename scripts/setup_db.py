import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_SERVER", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "medication_agent")

    print(f"Connecting to 'postgres' database on {host}:{port} as user '{user}'...")
    
    try:
        conn = psycopg2.connect(
            dbname='postgres', 
            user=user, 
            password=password, 
            host=host, 
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}';")
        exists = cursor.fetchone()

        if not exists:
            print(f"Creating database '{dbname}'...")
            cursor.execute(f"CREATE DATABASE {dbname};")
            print(f"Database '{dbname}' created successfully.")
        else:
            print(f"Database '{dbname}' already exists.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure PostgreSQL is running and your credentials in .env are correct.")

if __name__ == "__main__":
    create_database()
