import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv

# Find and load the .env file from the project folder
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT current_database(), extversion
        FROM pg_extension
        WHERE extname = 'vector';
    """)

    result = cursor.fetchone()

print("Connected successfully!")
print("Database:", result[0])
print("pgvector version:", result[1])

connection.close()