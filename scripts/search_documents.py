import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer


PROJECT_FOLDER = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_FOLDER / ".env")


# Load the same model used during document ingestion
print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# Get a question from the user
question = input("\nAsk a question: ")


# Convert the question into a 384-number vector
question_embedding = model.encode(
    question,
    normalize_embeddings=True,
)


# Connect to PostgreSQL
connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

register_vector(connection)


# Search for the three most similar chunks
with connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT
            source,
            page_number,
            content,
            1 - (embedding <=> %s) AS similarity
        FROM document_chunks
        ORDER BY embedding <=> %s
        LIMIT 3;
        """,
        (question_embedding, question_embedding),
    )

    results = cursor.fetchall()


connection.close()


print("\nTop matching chunks:")

for position, result in enumerate(results, start=1):
    source, page_number, content, similarity = result

    print("\n" + "=" * 60)
    print(f"Result {position}")
    print(f"Source: {source}")
    print(f"Page: {page_number}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Content:\n{content}")