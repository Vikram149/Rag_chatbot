import re
import unicodedata
from collections import Counter
from math import ceil
from pathlib import Path

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

from app.database import get_database_connection
from app.rag_service import embedding_model


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "documents"
)

DOCUMENTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

SUPPORTED_FILE_TYPES = {
    ".docx",
    ".pdf",
    ".txt",
}

CHUNK_SIZE = 180
CHUNK_OVERLAP = 40


# --------------------------------------------------
# 1. Clean extracted document text
# --------------------------------------------------

def clean_extracted_text(text: str) -> str:
    """
    Clean extraction noise while preserving meaningful
    symbols, formulas, code and paragraph boundaries.
    """

    if not text:
        return ""

    # Normalize Unicode without removing mathematical
    # symbols such as ², √ or π.
    text = unicodedata.normalize(
        "NFC",
        text,
    )

    replacements = {
        "\r\n": "\n",
        "\r": "\n",
        "\u00a0": " ",
        "\u00ad": "",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\ufeff": "",
    }

    for old_value, new_value in replacements.items():
        text = text.replace(
            old_value,
            new_value,
        )

    # Remove invisible control characters while
    # preserving normal line breaks and tabs.
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
        "",
        text,
    )

    # Remove long groups of broken dash or underscore
    # symbols sometimes produced during PDF extraction.
    text = re.sub(
        r"(?<!\w)[—–_-]{4,}(?!\w)",
        " ",
        text,
    )

    # Normalize repeated spaces.
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Remove spaces around line breaks.
    text = re.sub(
        r" *\n *",
        "\n",
        text,
    )

    # Keep at most one blank line between sections.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# --------------------------------------------------
# 2. Remove repeated headers and footers
# --------------------------------------------------

def remove_repeated_page_edges(
    pages: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """
    Remove short headers or footers repeated across
    most pages of a document.
    """

    if len(pages) < 3:
        return pages

    edge_counts = Counter()
    page_line_groups = []

    for page_number, page_text in pages:
        lines = [
            line.strip()
            for line in page_text.splitlines()
            if line.strip()
        ]

        page_line_groups.append(
            (
                page_number,
                lines,
            )
        )

        # Only examine the first two and last two
        # lines of each page.
        edge_lines = (
            lines[:2]
            + lines[-2:]
        )

        normalized_edges = {
            " ".join(
                line.lower().split()
            )
            for line in edge_lines
            if len(line) <= 120
        }

        edge_counts.update(
            normalized_edges
        )

    minimum_repetitions = max(
        3,
        ceil(len(pages) * 0.60),
    )

    repeated_edges = {
        line
        for line, count in edge_counts.items()
        if count >= minimum_repetitions
    }

    cleaned_pages = []

    for page_number, lines in page_line_groups:
        final_lines = []

        for index, line in enumerate(lines):
            normalized_line = " ".join(
                line.lower().split()
            )

            is_page_edge = (
                index < 2
                or index >= len(lines) - 2
            )

            if (
                is_page_edge
                and normalized_line
                in repeated_edges
            ):
                continue

            final_lines.append(line)

        cleaned_text = clean_extracted_text(
            "\n".join(final_lines)
        )

        if cleaned_text:
            cleaned_pages.append(
                (
                    page_number,
                    cleaned_text,
                )
            )

    return cleaned_pages


# --------------------------------------------------
# 3. Read paragraphs and tables in DOCX order
# --------------------------------------------------

def iterate_docx_blocks(document):
    """
    Yield paragraphs and tables in their original
    document order.
    """

    parent_element = (
        document.element.body
    )

    for child in (
        parent_element.iterchildren()
    ):
        if isinstance(child, CT_P):
            yield Paragraph(
                child,
                document,
            )

        elif isinstance(child, CT_Tbl):
            yield Table(
                child,
                document,
            )


# --------------------------------------------------
# 4. Extract DOCX text
# --------------------------------------------------

def extract_docx_pages(
    file_path: Path,
) -> list[tuple[int, str]]:
    document = Document(file_path)

    pages = []
    current_page = 1
    current_text_parts = []

    for block in iterate_docx_blocks(
        document
    ):
        if isinstance(block, Paragraph):
            text = block.text.strip()

            if text:
                current_text_parts.append(
                    text
                )

            # Detect manually inserted page breaks.
            page_breaks = block._p.xpath(
                './/w:br[@w:type="page"]'
            )

            for _ in page_breaks:
                page_text = "\n".join(
                    current_text_parts
                ).strip()

                if page_text:
                    pages.append(
                        (
                            current_page,
                            page_text,
                        )
                    )

                current_page += 1
                current_text_parts = []

        elif isinstance(block, Table):
            table_rows = []

            for row in block.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                    if cell.text.strip()
                ]

                if cells:
                    table_rows.append(
                        " | ".join(cells)
                    )

            if table_rows:
                current_text_parts.append(
                    "\n".join(table_rows)
                )

    remaining_text = "\n".join(
        current_text_parts
    ).strip()

    if remaining_text:
        pages.append(
            (
                current_page,
                remaining_text,
            )
        )

    return pages


# --------------------------------------------------
# 5. Extract PDF text
# --------------------------------------------------

def extract_pdf_pages(
    file_path: Path,
) -> list[tuple[int, str]]:
    reader = PdfReader(file_path)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = (
            page.extract_text()
            or ""
        )

        if text.strip():
            pages.append(
                (
                    page_number,
                    text,
                )
            )

    return pages


# --------------------------------------------------
# 6. Extract TXT text
# --------------------------------------------------

def extract_txt_pages(
    file_path: Path,
) -> list[tuple[int, str]]:
    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    if not text.strip():
        return []

    return [
        (
            1,
            text,
        )
    ]


# --------------------------------------------------
# 7. Choose reader and clean extracted pages
# --------------------------------------------------

def extract_document_pages(
    file_path: Path,
) -> list[tuple[int, str]]:
    file_extension = (
        file_path.suffix.lower()
    )

    if file_extension == ".docx":
        pages = extract_docx_pages(
            file_path
        )

    elif file_extension == ".pdf":
        pages = extract_pdf_pages(
            file_path
        )

    elif file_extension == ".txt":
        pages = extract_txt_pages(
            file_path
        )

    else:
        raise ValueError(
            "Unsupported file type. "
            "Only DOCX, PDF and TXT are allowed."
        )

    cleaned_pages = []

    for page_number, page_text in pages:
        cleaned_text = clean_extracted_text(
            page_text
        )

        if cleaned_text:
            cleaned_pages.append(
                (
                    page_number,
                    cleaned_text,
                )
            )

    return remove_repeated_page_edges(
        cleaned_pages
    )


# --------------------------------------------------
# 8. Divide extracted text into chunks
# --------------------------------------------------

def is_likely_heading(line: str) -> bool:
    """
    Detect short lines that probably represent headings.

    Examples:
    Multi-Threading
    Life-Cycle of a Thread:
    Synchronization:
    DeadLock:
    4. Thread(Runnable, String)
    """

    line = line.strip()

    if not line:
        return False

    if len(line) > 120:
        return False

    words = line.split()

    if len(words) > 14:
        return False

    # Bullet points normally contain explanation text,
    # so they should not be treated as headings.
    if re.match(
        r"^[•●▪◦*]\s*",
        line,
    ):
        return False

    # Avoid treating Java code as headings.
    if any(
        symbol in line
        for symbol in [
            "{",
            "}",
            ";",
            "=",
        ]
    ):
        return False

    # Headings commonly end with a colon.
    if line.endswith(":"):
        return True

    # Numbered headings such as:
    # 1. Thread Class
    # 2) Synchronization
    if re.match(
        r"^\d+(?:\.\d+)*[.)]?\s+\S+",
        line,
    ):
        return True

    letters = [
        character
        for character in line
        if character.isalpha()
    ]

    if not letters:
        return False

    # Uppercase headings.
    if line.isupper():
        return True

    # Title-style headings that do not end like
    # a normal sentence.
    if (
        line.istitle()
        and not line.endswith(
            (".", "?", "!")
        )
    ):
        return True

    return False


def split_page_into_sections(
    page_text: str,
) -> list[dict]:
    """
    Divide a page into heading-and-content sections.
    """

    lines = [
        line.strip()
        for line in page_text.splitlines()
        if line.strip()
    ]

    if not lines:
        return []

    sections = []

    current_heading = None
    current_content_lines = []

    for line in lines:
        if is_likely_heading(line):
            clean_heading = (
                line.rstrip(":").strip()
            )

            # Save the previous section before
            # starting the new heading.
            if current_content_lines:
                sections.append(
                    {
                        "heading":
                            current_heading,
                        "content":
                            " ".join(
                                current_content_lines
                            ),
                    }
                )

                current_content_lines = []
                current_heading = (
                    clean_heading
                )

            elif current_heading:
                # Preserve consecutive headings.
                current_heading = (
                    f"{current_heading} > "
                    f"{clean_heading}"
                )

            else:
                current_heading = (
                    clean_heading
                )

        else:
            current_content_lines.append(
                line
            )

    if current_content_lines:
        sections.append(
            {
                "heading":
                    current_heading,
                "content":
                    " ".join(
                        current_content_lines
                    ),
            }
        )

    elif current_heading:
        sections.append(
            {
                "heading":
                    current_heading,
                "content": "",
            }
        )

    # If no heading was detected, keep the entire
    # page as one normal section.
    if not sections:
        sections.append(
            {
                "heading": None,
                "content": " ".join(lines),
            }
        )

    return sections


def create_chunks(
    pages: list[tuple[int, str]],
) -> list[dict]:
    """
    Create structure-aware chunks.

    Small heading sections are combined until the
    chunk reaches the size limit. Large sections are
    divided while repeating their heading.
    """

    chunks = []
    chunk_index = 0

    def save_chunk(
        page_number: int,
        text: str,
    ):
        nonlocal chunk_index

        cleaned_text = text.strip()

        if not cleaned_text:
            return

        chunks.append(
            {
                "page_number":
                    page_number,
                "chunk_index":
                    chunk_index,
                "content":
                    cleaned_text,
            }
        )

        chunk_index += 1

    for page_number, page_text in pages:
        sections = split_page_into_sections(
            page_text
        )

        current_parts = []
        current_word_count = 0

        for section in sections:
            heading = section["heading"]
            content = section["content"]

            heading_prefix = ""

            if heading:
                heading_prefix = (
                    f"Section: {heading}"
                )

            body_words = content.split()
            heading_words = (
                heading_prefix.split()
            )

            complete_section_words = (
                heading_words
                + body_words
            )

            if not complete_section_words:
                continue

            # Small sections are packed together,
            # while remaining under CHUNK_SIZE.
            if (
                len(complete_section_words)
                <= CHUNK_SIZE
            ):
                if (
                    current_parts
                    and current_word_count
                    + len(complete_section_words)
                    > CHUNK_SIZE
                ):
                    save_chunk(
                        page_number,
                        "\n\n".join(
                            current_parts
                        ),
                    )

                    current_parts = []
                    current_word_count = 0

                if heading_prefix and content:
                    section_text = (
                        f"{heading_prefix}\n"
                        f"{content}"
                    )
                elif heading_prefix:
                    section_text = (
                        heading_prefix
                    )
                else:
                    section_text = content

                current_parts.append(
                    section_text
                )

                current_word_count += len(
                    complete_section_words
                )

                continue

            # Save anything already collected before
            # processing an oversized section.
            if current_parts:
                save_chunk(
                    page_number,
                    "\n\n".join(
                        current_parts
                    ),
                )

                current_parts = []
                current_word_count = 0

            # Split a large section and repeat its
            # heading in every resulting chunk.
            available_body_words = max(
                40,
                CHUNK_SIZE
                - len(heading_words),
            )

            section_overlap = min(
                CHUNK_OVERLAP,
                available_body_words - 1,
            )

            words_to_move = (
                available_body_words
                - section_overlap
            )

            start_position = 0

            while start_position < len(
                body_words
            ):
                end_position = (
                    start_position
                    + available_body_words
                )

                body_part = " ".join(
                    body_words[
                        start_position:end_position
                    ]
                ).strip()

                if heading_prefix:
                    chunk_text = (
                        f"{heading_prefix}\n"
                        f"{body_part}"
                    )
                else:
                    chunk_text = body_part

                save_chunk(
                    page_number,
                    chunk_text,
                )

                if (
                    end_position
                    >= len(body_words)
                ):
                    break

                start_position += (
                    words_to_move
                )

        # Save the final collected sections
        # from this page.
        if current_parts:
            save_chunk(
                page_number,
                "\n\n".join(
                    current_parts
                ),
            )

    return chunks
# --------------------------------------------------
# 9. Register and process an uploaded document
# --------------------------------------------------

def ingest_document(
    file_path: Path,
    original_filename: str,
    user_id: int,

):
    file_path = Path(file_path)

    file_extension = (
        file_path.suffix.lower()
    )

    if (
        file_extension
        not in SUPPORTED_FILE_TYPES
    ):
        raise ValueError(
            "Only DOCX, PDF and TXT "
            "files are supported."
        )

    file_size = (
        file_path.stat().st_size
    )

    # Create the document record first.
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (
                    filename,
                    stored_filename,
                    file_type,
                    file_size_bytes,
                    user_id,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'processing'
                )
                RETURNING id;
                """,
                (
                    original_filename,
                    file_path.name,
                    file_extension.removeprefix("."),
                    file_size,
                    user_id,
                ),
            )

            document_id = (
                cursor.fetchone()[0]
            )

    try:
        pages = extract_document_pages(
            file_path
        )

        chunks = create_chunks(
            pages
        )

        if not chunks:
            raise ValueError(
                "No readable text was found "
                "in the document."
            )

        # Add useful document information before
        # creating the embedding.
        enriched_chunks = []

        for chunk in chunks:
            enriched_text = (
                f"Document: "
                f"{original_filename}\n"
                f"Page: "
                f"{chunk['page_number']}\n"
                f"Content: "
                f"{chunk['content']}"
            )

            enriched_chunks.append(
                enriched_text
            )

        # Create all embeddings together.
        embeddings = (
            embedding_model.encode(
                enriched_chunks,
                normalize_embeddings=True,
            )
        )

        # Store chunks and embeddings.
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                for chunk, embedding in zip(
                    chunks,
                    embeddings,
                ):
                    cursor.execute(
                        """
                        INSERT INTO document_chunks (
                            document_id,
                            source,
                            page_number,
                            chunk_index,
                            content,
                            embedding
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        );
                        """,
                        (
                            document_id,
                            original_filename,
                            chunk[
                                "page_number"
                            ],
                            chunk[
                                "chunk_index"
                            ],
                            chunk["content"],
                            embedding,
                        ),
                    )

                cursor.execute(
                    """
                    UPDATE documents
                    SET
                        status = 'ready',
                        chunk_count = %s,
                        error_message = NULL
                    WHERE id = %s;
                    """,
                    (
                        len(chunks),
                        document_id,
                    ),
                )

        return {
            "id": document_id,
            "filename":
                original_filename,
            "status": "ready",
            "chunk_count":
                len(chunks),
        }

    except Exception as error:
        # Mark the document as failed.
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE documents
                    SET
                        status = 'failed',
                        error_message = %s
                    WHERE id = %s;
                    """,
                    (
                        str(error),
                        document_id,
                    ),
                )

        raise


def replace_document(
    document_id: int,
    file_path: Path,
    original_filename: str,
):
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()

    if file_extension not in SUPPORTED_FILE_TYPES:
        raise ValueError(
            "Only DOCX, PDF and TXT files are supported."
        )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT stored_filename
                FROM documents
                WHERE id = %s;
                """,
                (document_id,),
            )

            existing_document = cursor.fetchone()

    if existing_document is None:
        raise ValueError("Document not found.")

    old_stored_filename = Path(
        existing_document[0]
    ).name

    old_file_path = (
        DOCUMENTS_DIRECTORY
        / old_stored_filename
    )

    # Process the new file before changing the database.
    pages = extract_document_pages(file_path)
    chunks = create_chunks(pages)

    if not chunks:
        raise ValueError(
            "No readable text was found in the new document."
        )

    enriched_chunks = []

    for chunk in chunks:
        enriched_chunks.append(
            f"Document: {original_filename}\n"
            f"Page: {chunk['page_number']}\n"
            f"Content: {chunk['content']}"
        )

    embeddings = embedding_model.encode(
        enriched_chunks,
        normalize_embeddings=True,
    )

    file_size = file_path.stat().st_size

    # Replace metadata and chunks in one transaction.
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM document_chunks
                WHERE document_id = %s;
                """,
                (document_id,),
            )

            for chunk, embedding in zip(
                chunks,
                embeddings,
            ):
                cursor.execute(
                    """
                    INSERT INTO document_chunks (
                        document_id,
                        source,
                        page_number,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s
                    );
                    """,
                    (
                        document_id,
                        original_filename,
                        chunk["page_number"],
                        chunk["chunk_index"],
                        chunk["content"],
                        embedding,
                    ),
                )

            cursor.execute(
                """
                UPDATE documents
                SET
                    filename = %s,
                    stored_filename = %s,
                    file_type = %s,
                    file_size_bytes = %s,
                    status = 'ready',
                    chunk_count = %s,
                    error_message = NULL,
                    uploaded_at = CURRENT_TIMESTAMP
                WHERE id = %s;
                """,
                (
                    original_filename,
                    file_path.name,
                    file_extension.removeprefix("."),
                    file_size,
                    len(chunks),
                    document_id,
                ),
            )

    # Remove the old stored file after success.
    if (
    old_file_path != file_path
    and old_file_path.exists()
):
        try:
            old_file_path.unlink()
        except PermissionError:
            # Windows may temporarily lock a previewed PDF.
            # This should not make the replacement fail.
            pass

    return {
        "id": document_id,
        "filename": original_filename,
        "status": "ready",
        "chunk_count": len(chunks),
    }

# --------------------------------------------------
# 10. List uploaded documents
# --------------------------------------------------

def get_all_documents(
    user_id: int,
):
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    filename,
                    file_type,
                    file_size_bytes,
                    status,
                    chunk_count,
                    error_message,
                    uploaded_at
                FROM documents
                WHERE user_id = %s
                ORDER BY uploaded_at DESC;
                """,
                (user_id,),
            )

            rows = cursor.fetchall()

    documents = []

    for row in rows:
        documents.append(
            {
                "id": row[0],
                "filename": row[1],
                "file_type": row[2],
                "file_size_bytes": row[3],
                "status": row[4],
                "chunk_count": row[5],
                "error_message": row[6],
                "uploaded_at": row[7],
            }
        )

    return documents

def get_document_file_info(
    document_id: int,
) -> dict | None:
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    filename,
                    stored_filename,
                    file_type,
                    status
                FROM documents
                WHERE id = %s;
                """,
                (document_id,),
            )

            row = cursor.fetchone()

    if row is None:
        return None

    safe_stored_filename = Path(row[1]).name
    file_path = DOCUMENTS_DIRECTORY / safe_stored_filename

    return {
        "filename": row[0],
        "stored_filename": safe_stored_filename,
        "file_type": row[2],
        "status": row[3],
        "file_path": file_path,
    }
# --------------------------------------------------
# 11. Delete a document
# --------------------------------------------------

def delete_document(
    document_id: int,
) -> bool:
    stored_filename = None

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM documents
                WHERE id = %s
                RETURNING stored_filename;
                """,
                (document_id,),
            )

            deleted_row = (
                cursor.fetchone()
            )

            if deleted_row:
                stored_filename = (
                    deleted_row[0]
                )

    if not stored_filename:
        return False

    # Path.name protects against unsafe paths.
    safe_filename = Path(
        stored_filename
    ).name

    file_path = (
        DOCUMENTS_DIRECTORY
        / safe_filename
    )

    if file_path.exists():
        file_path.unlink()

    return True