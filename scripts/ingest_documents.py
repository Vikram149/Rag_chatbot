import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Project paths and environment variables
# --------------------------------------------------

PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DOCUMENTS_FOLDER = PROJECT_FOLDER / "data" / "documents"

load_dotenv(PROJECT_FOLDER / ".env")


# --------------------------------------------------
# 2. Read paragraphs and tables in their correct order
# --------------------------------------------------

def read_docx_by_page(file_path):
    document = Document(file_path)

    pages = []
    current_page = []
    page_number = 1

    for element in document.element.body.iterchildren():

        # Read a normal paragraph
        if element.tag == qn("w:p"):
            paragraph = Paragraph(element, document)
            text = paragraph.text.strip()

            if text:
                current_page.append(text)

            # Detect a manually inserted page break
            page_breaks = element.xpath('.//w:br[@w:type="page"]')

            if page_breaks:
                if current_page:
                    pages.append(
                        {
                            "page_number": page_number,
                            "text": "\n".join(current_page),
                        }
                    )

                page_number += 1
                current_page = []

        # Read a table
        elif element.tag == qn("w:tbl"):
            table = Table(element, document)
            table_lines = []

            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                table_lines.append(" | ".join(cells))

            current_page.append("\n".join(table_lines))

    # Save the final page
    if current_page:
        pages.append(
            {
                "page_number": page_number,
                "text": "\n".join(current_page),
            }
        )

    return pages


# --------------------------------------------------
# 3. Split text into chunks with overlap
# --------------------------------------------------

def create_chunks(text, chunk_size=180, overlap=40):
    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


# --------------------------------------------------
# 4. Connect to PostgreSQL
# --------------------------------------------------

connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

register_vector(connection)


# --------------------------------------------------
# 5. Load our local embedding model
# --------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded!")


# --------------------------------------------------
# 6. Process every Word document
# --------------------------------------------------

document_files = list(DOCUMENTS_FOLDER.glob("*.docx"))

if not document_files:
    print("No DOCX documents were found.")
    connection.close()
    raise SystemExit


with connection.cursor() as cursor:

    for document_path in document_files:
        print(f"\nProcessing: {document_path.name}")

        pages = read_docx_by_page(document_path)

        # Prevent duplicate chunks when rerunning the script
        cursor.execute(
            "DELETE FROM document_chunks WHERE source = %s",
            (document_path.name,),
        )

        chunk_index = 0

        for page in pages:
            chunks = create_chunks(page["text"])

            for chunk in chunks:

                # Chunk enrichment:
                # Add document and page context before embedding
                enriched_text = (
                    f"Document: {document_path.name}\n"
                    f"Page: {page['page_number']}\n"
                    f"Content: {chunk}"
                )

                embedding = model.encode(
                    enriched_text,
                    normalize_embeddings=True,
                ).tolist()

                cursor.execute(
                    """
                    INSERT INTO document_chunks
                        (source, page_number, chunk_index, content, embedding)
                    VALUES
                        (%s, %s, %s, %s, %s)
                    """,
                    (
                        document_path.name,
                        page["page_number"],
                        chunk_index,
                        chunk,
                        embedding,
                    ),
                )

                chunk_index += 1

        print(f"Stored {chunk_index} chunks.")

connection.commit()
connection.close()

print("\nDocument ingestion completed successfully!")