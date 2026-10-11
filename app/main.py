import os
from psycopg.errors import UniqueViolation

from app.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from app.database import get_database_connection
from app.document_service import (
    DOCUMENTS_DIRECTORY,
    SUPPORTED_FILE_TYPES,
    delete_document,
    get_all_documents,
    ingest_document,
    extract_document_pages,
    get_document_file_info,
    replace_document,
)
from app.rag_service import (
    answer_question,
    summarize_conversation,
)
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates

from html import escape
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIRECTORY = PROJECT_ROOT / "static"
TEMPLATES_DIRECTORY = PROJECT_ROOT / "templates"

templates = Jinja2Templates(
    directory=TEMPLATES_DIRECTORY
)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


app = FastAPI(
    title="RAG Document Chatbot",
    description="Local RAG chatbot using FastAPI, PostgreSQL and pgvector",
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY),
    name="static",
)


def get_authenticated_user_id(request: Request) -> int | None:
    """Return the signed-in user's ID, or None when the JWT is missing/invalid."""
    token = request.cookies.get("access_token")

    if not token:
        return None

    return decode_access_token(token)


@app.middleware("http")
async def protect_dashboard_and_api(request: Request, call_next):
    """Require a valid JWT for the dashboard, documents, and chats."""
    path = request.url.path
    user_id = get_authenticated_user_id(request)

    if user_id is not None:
        request.state.user_id = user_id

    protected_api = (
        path.startswith("/api/documents")
        or path.startswith("/api/chats")
        or path.startswith(
            "/api/retrieval-analytics"
        )
    )

    if path == "/" or protected_api:
        if user_id is None:
            if path == "/":
                return RedirectResponse(
                    url="/login",
                    status_code=303,
                )

            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required."},
            )

    return await call_next(request)


# --------------------------------------------------
# Request models
# --------------------------------------------------

class CreateChatRequest(BaseModel):
    title: str = "New Chat"
    document_ids: list[int] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    question: str
    document_ids: list[int] | None = None

class RegenerateMessageRequest(BaseModel):
    document_ids: list[int] | None = None

class RenameChatRequest(BaseModel):
    title: str

class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
    )


class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False
    
@app.post(
    "/api/auth/register",
    status_code=201,
)
def register_user(
    registration: RegisterRequest,
):
    username = (
        registration.username
        .strip()
        .lower()
    )

    if registration.password != (
        registration.confirm_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match.",
        )

    password_hash = hash_password(
        registration.password
    )

    try:
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO app_users (
                        username,
                        password_hash
                    )
                    VALUES (%s, %s)
                    RETURNING id;
                    """,
                    (
                        username,
                        password_hash,
                    ),
                )

                new_user = cursor.fetchone()

    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )

    user_id = int(new_user[0])

    

    return {
        "message": "Account created successfully.",
        "user": {
            "id": user_id,
            "username": username,
        },
    }


@app.post("/api/auth/login")
def login_user(
    login: LoginRequest,
    response: Response,
):
    username = (
        login.username
        .strip()
        .lower()
    )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    password_hash
                FROM app_users
                WHERE username = %s
                LIMIT 1;
                """,
                (username,),
            )

            user = cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    user_id = int(user[0])
    stored_username = user[1]
    stored_password_hash = user[2]

    password_is_valid = verify_password(
        plain_password=login.password,
        stored_password_hash=(
            stored_password_hash
        ),
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        user_id=user_id,
        remember_me=login.remember_me,
    )

    set_authentication_cookie(
        response=response,
        token=token,
        remember_me=login.remember_me,
    )

    return {
        "message": "Login successful.",
        "user": {
            "id": user_id,
            "username": stored_username,
        },
    }


@app.post("/api/auth/logout")
def logout_user(
    response: Response,
):
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    return {
        "message": "Logout successful.",
    }


@app.get("/api/auth/me")
def get_current_user(
    request: Request,
):
    token = request.cookies.get(
        "access_token"
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    user_id = decode_access_token(
        token
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login.",
        )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    username,
                    created_at
                FROM app_users
                WHERE id = %s;
                """,
                (user_id,),
            )

            user = cursor.fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists.",
        )

    return {
        "id": int(user[0]),
        "username": user[1],
        "created_at": user[2],
    }
    
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_authenticated_user_id(request) is not None:
        return RedirectResponse(
            url="/",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "RAG Document Chatbot",
    }


# --------------------------------------------------
# Document endpoints
# --------------------------------------------------

@app.get("/api/documents")
def list_documents(request: Request):
    return {
        "documents": get_all_documents(
            request.state.user_id
        )
    }


@app.post("/api/documents/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
):
    user_id = request.state.user_id

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must have a filename.",
        )

    # Remove any directory information from the filename
    original_filename = Path(file.filename).name
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only DOCX, PDF and TXT files are supported.",
        )

    # Prevent duplicate visible filenames
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM documents
                WHERE user_id = %s
                  AND LOWER(filename) = LOWER(%s);
                """,
                (
                    user_id,
                    original_filename,
                ),
            )

            existing_document = cursor.fetchone()

    if existing_document:
        raise HTTPException(
            status_code=409,
            detail=(
                "A document with this filename already exists. "
                "Delete the existing document or rename the new file."
            ),
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="The maximum allowed file size is 20 MB.",
        )

    # Store using a unique internal filename
    stored_filename = (
        f"{uuid4().hex}{file_extension}"
    )

    saved_file_path = (
        DOCUMENTS_DIRECTORY / stored_filename
    )

    saved_file_path.write_bytes(file_content)

    try:
        document_result = ingest_document(
            file_path=saved_file_path,
            original_filename=original_filename,
            user_id=user_id,
        )

        return {
            "message": "Document uploaded and processed successfully.",
            "document": document_result,
        }

    except Exception as error:
        if saved_file_path.exists():
            saved_file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {error}",
        )

@app.get("/api/documents/{document_id}/preview")
def preview_document(
    document_id: int,
    request: Request,
):
    ensure_user_owns_document(
        document_id=document_id,
        user_id=request.state.user_id,
    )

    document = get_document_file_info(
        document_id
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if document["status"] != "ready":
        raise HTTPException(
            status_code=409,
            detail="Document is not ready for preview.",
        )

    file_path = document["file_path"]

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="The stored document file was not found.",
        )

    if document["file_type"] == "pdf":
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=document["filename"],
            content_disposition_type="inline",
        )

    extracted_pages = extract_document_pages(
        file_path
    )

    preview_sections = []

    for page_number, page_text in extracted_pages:
        preview_sections.append(
            f"PAGE {page_number}\n"
            f"{'-' * 50}\n"
            f"{page_text}"
        )

    preview_text = "\n\n".join(
        preview_sections
    )

    return PlainTextResponse(
        content=preview_text,
        media_type="text/plain; charset=utf-8",
    )
    
@app.put("/api/documents/{document_id}/replace")
async def replace_uploaded_document(
    document_id: int,
    request: Request,
    file: UploadFile = File(...),
):
    ensure_user_owns_document(
        document_id=document_id,
        user_id=request.state.user_id,
    )

    existing_document = get_document_file_info(
        document_id
    )

    if existing_document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="The replacement file needs a filename.",
        )

    original_filename = Path(file.filename).name
    file_extension = Path(
        original_filename
    ).suffix.lower()

    if file_extension not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only DOCX, PDF and TXT files are supported.",
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The replacement file is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="The maximum allowed file size is 20 MB.",
        )

    stored_filename = (
        f"{uuid4().hex}{file_extension}"
    )

    saved_file_path = (
        DOCUMENTS_DIRECTORY
        / stored_filename
    )

    saved_file_path.write_bytes(file_content)

    try:
        document_result = replace_document(
            document_id=document_id,
            file_path=saved_file_path,
            original_filename=original_filename,
        )

        return {
            "message": "Document replaced successfully.",
            "document": document_result,
        }

    except Exception as error:
        if saved_file_path.exists():
            saved_file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document replacement failed: {error}",
        )
        
        
@app.delete("/api/documents/{document_id}")
def remove_document(
    document_id: int,
    request: Request,
):
    ensure_user_owns_document(
        document_id=document_id,
        user_id=request.state.user_id,
    )

    was_deleted = delete_document(document_id)

    if not was_deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "message": "Document and its chunks were deleted successfully."
    }


# --------------------------------------------------
# Chat helpers
# --------------------------------------------------
def ensure_user_owns_document(
    document_id: int,
    user_id: int,
) -> None:
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM documents
                WHERE id = %s
                  AND user_id = %s;
                """,
                (
                    document_id,
                    user_id,
                ),
            )

            document = cursor.fetchone()

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )


def set_authentication_cookie(
    response: Response,
    token: str,
    remember_me: bool,
) -> None:
    cookie_max_age = (
        7 * 24 * 60 * 60
        if remember_me
        else 30 * 60
    )

    cookie_secure = (
        os.getenv(
            "COOKIE_SECURE",
            "false",
        ).lower()
        == "true"
    )

    response.set_cookie(
        key="access_token",
        value=token,
        max_age=cookie_max_age,
        httponly=True,
        secure=cookie_secure,
        samesite="lax",
        path="/",
    )


def save_retrieval_run(
    cursor,
    chat_id: int,
    user_message_id: int,
    assistant_message_id: int,
    request_type: str,
    result: dict,
) -> int:
    """
    Save one RAG retrieval operation and every final
    context chunk supplied to Claude.
    """

    retrieval = result.get("retrieval") or {}
    retrieved_chunks = (
        result.get("retrieved_chunks") or []
    )

    cursor.execute(
        """
        INSERT INTO retrieval_runs (
            chat_id,
            user_message_id,
            assistant_message_id,
            request_type,
            retrieval_query,
            vector_candidate_count,
            keyword_candidate_count,
            combined_candidate_count,
            seed_count,
            context_count,
            highest_similarity,
            minimum_similarity,
            claude_called
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        RETURNING id;
        """,
        (
            chat_id,
            user_message_id,
            assistant_message_id,
            request_type,
            retrieval.get("retrieval_query", ""),
            retrieval.get(
                "vector_candidate_count",
                0,
            ),
            retrieval.get(
                "keyword_candidate_count",
                0,
            ),
            retrieval.get("candidate_count", 0),
            retrieval.get("seed_count", 0),
            retrieval.get("context_count", 0),
            retrieval.get("highest_similarity"),
            retrieval.get("threshold"),
            bool(
                retrieval.get(
                    "claude_called",
                    False,
                )
            ),
        ),
    )

    retrieval_run_id = cursor.fetchone()[0]

    for chunk in retrieved_chunks:
        cursor.execute(
            """
            INSERT INTO retrieval_run_chunks (
                retrieval_run_id,
                chunk_id,
                context_position,
                retrieval_type,
                similarity_score,
                keyword_score,
                hybrid_score,
                reranker_score
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            );
            """,
            (
                retrieval_run_id,
                chunk["chunk_id"],
                chunk["context_position"],
                chunk["retrieval_type"],
                chunk.get("similarity_score"),
                chunk.get("keyword_score"),
                chunk.get("hybrid_score"),
                chunk.get("reranker_score"),
            ),
        )

    return retrieval_run_id


def get_user_ready_document_ids(
    user_id: int,
):
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM documents
                WHERE user_id = %s
                  AND status = 'ready'
                ORDER BY id;
                """,
                (user_id,),
            )

            return [
                row[0]
                for row in cursor.fetchall()
            ]


def validate_user_document_ids(
    document_ids: list[int],
    user_id: int,
):
    if not document_ids:
        return []

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM documents
                WHERE user_id = %s
                  AND status = 'ready'
                  AND id = ANY(%s::BIGINT[]);
                """,
                (
                    user_id,
                    document_ids,
                ),
            )

            valid_ids = {
                row[0]
                for row in cursor.fetchall()
            }

    requested_ids = set(document_ids)

    if valid_ids != requested_ids:
        raise HTTPException(
            status_code=400,
            detail="One or more selected documents are unavailable.",
        )

    return list(valid_ids)


def get_chat_document_ids(
    chat_id: int,
    user_id: int,
):
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cd.document_id
                FROM chat_documents AS cd
                INNER JOIN documents AS d
                    ON d.id = cd.document_id
                INNER JOIN chats AS c
                    ON c.id = cd.chat_id
                WHERE cd.chat_id = %s
                  AND c.user_id = %s
                  AND d.user_id = %s
                ORDER BY cd.document_id;
                """,
                (
                    chat_id,
                    user_id,
                    user_id,
                ),
            )

            return [
                row[0]
                for row in cursor.fetchall()
            ]


def replace_user_chat_documents(
    chat_id: int,
    user_id: int,
    document_ids: list[int],
):
    ensure_user_owns_chat(
        chat_id=chat_id,
        user_id=user_id,
    )

    valid_ids = validate_user_document_ids(
        document_ids=document_ids,
        user_id=user_id,
    )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM chat_documents
                WHERE chat_id = %s;
                """,
                (chat_id,),
            )

            for document_id in valid_ids:
                cursor.execute(
                    """
                    INSERT INTO chat_documents (
                        chat_id,
                        document_id
                    )
                    VALUES (%s, %s);
                    """,
                    (
                        chat_id,
                        document_id,
                    ),
                )


def ensure_user_owns_chat(
    chat_id: int,
    user_id: int,
):
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM chats
                WHERE id = %s
                  AND user_id = %s;
                """,
                (
                    chat_id,
                    user_id,
                ),
            )

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail="Chat not found.",
                )

def get_conversation_memory(
    chat_id: int,
    recent_message_limit: int = 8,
):
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT role, content
                FROM messages
                WHERE chat_id = %s
                ORDER BY created_at, id;
                """,
                (chat_id,),
            )

            rows = cursor.fetchall()

    messages = [
        {
            "role": row[0],
            "content": row[1],
        }
        for row in rows
    ]

    if len(messages) <= recent_message_limit:
        return messages, ""

    older_messages = messages[
        :-recent_message_limit
    ]

    recent_messages = messages[
        -recent_message_limit:
    ]

    conversation_summary = (
        summarize_conversation(
            older_messages
        )
    )

    return (
        recent_messages,
        conversation_summary,
    )
    
def get_chat_export_data(
    chat_id: int,
    user_id: int,
):
    ensure_user_owns_chat(
        chat_id=chat_id,
        user_id=user_id,
    )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT title
                FROM chats
                WHERE id = %s
                  AND user_id = %s;
                """,
                (
                    chat_id,
                    user_id,
                ),
            )

            title = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT
                    role,
                    content,
                    sources,
                    created_at
                FROM messages
                WHERE chat_id = %s
                ORDER BY created_at, id;
                """,
                (chat_id,),
            )

            rows = cursor.fetchall()

    messages = []

    for row in rows:
        messages.append(
            {
                "role": row[0],
                "content": row[1],
                "sources": row[2] or [],
                "created_at": row[3],
            }
        )

    return {
        "title": title,
        "messages": messages,
    }
# --------------------------------------------------
# Chat endpoints
# --------------------------------------------------

@app.post("/api/chats")
def create_chat(
    payload: CreateChatRequest,
    request: Request,
):
    user_id = request.state.user_id
    title = payload.title.strip() or "New Chat"

    if payload.document_ids:
        document_ids = validate_user_document_ids(
            document_ids=payload.document_ids,
            user_id=user_id,
        )
    else:
        document_ids = get_user_ready_document_ids(
            user_id
        )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chats (
                    title,
                    user_id
                )
                VALUES (%s, %s)
                RETURNING id, title, created_at, updated_at;
                """,
                (
                    title,
                    user_id,
                ),
            )

            chat_row = cursor.fetchone()

            chat_id = chat_row[0]

            for document_id in document_ids:
                cursor.execute(
                    """
                    INSERT INTO chat_documents (
                        chat_id,
                        document_id
                    )
                    VALUES (%s, %s);
                    """,
                    (
                        chat_id,
                        document_id,
                    ),
                )

    return {
        "id": chat_row[0],
        "title": chat_row[1],
        "created_at": chat_row[2],
        "updated_at": chat_row[3],
        "document_ids": document_ids,
    }


@app.get("/api/chats")
def list_chats(request: Request):
    user_id = request.state.user_id

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    created_at,
                    updated_at
                FROM chats
                WHERE user_id = %s
                ORDER BY updated_at DESC;
                """,
                (user_id,),
            )

            rows = cursor.fetchall()

    chats = []

    for row in rows:
        chats.append(
            {
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
        )

    return {
        "chats": chats
    }


@app.get("/api/chats/{chat_id}/messages")
def get_chat_messages(
    chat_id: int,
    request: Request,
):
    user_id = request.state.user_id

    ensure_user_owns_chat(
        chat_id=chat_id,
        user_id=user_id,
    )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    role,
                    content,
                    sources,
                    created_at
                FROM messages
                WHERE chat_id = %s
                ORDER BY created_at, id;
                """,
                (chat_id,),
            )

            rows = cursor.fetchall()

    messages = []

    for row in rows:
        messages.append(
            {
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "sources": row[3] or [],
                "created_at": row[4],
            }
        )

    return {
        "chat_id": chat_id,
        "document_ids": get_chat_document_ids(
            chat_id=chat_id,
            user_id=user_id,
        ),
        "messages": messages,
    }


@app.post("/api/chats/{chat_id}/messages")
def send_chat_message(
    chat_id: int,
    payload: SendMessageRequest,
    request: Request,
):
    user_id = request.state.user_id

    ensure_user_owns_chat(
        chat_id=chat_id,
        user_id=user_id,
    )

    (
        conversation_history,
        conversation_summary,
    ) = get_conversation_memory(chat_id)

    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # Update the document selection when the UI sends IDs
    if payload.document_ids is not None:
        replace_user_chat_documents(
            chat_id=chat_id,
            user_id=user_id,
            document_ids=payload.document_ids,
        )

    document_ids = get_chat_document_ids(
        chat_id=chat_id,
        user_id=user_id,
    )

    # If the chat has no selections, search all ready documents
    if not document_ids:
        document_ids = get_user_ready_document_ids(
            user_id
        )

    if not document_ids:
        raise HTTPException(
            status_code=400,
            detail="Upload at least one ready document before asking questions.",
        )
        

    # Save the user question
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages (
                    chat_id,
                    role,
                    content
                )
                VALUES (%s, 'user', %s)
                RETURNING id, created_at;
                """,
                (
                    chat_id,
                    question,
                ),
            )

            user_message = cursor.fetchone()

    # Run the complete RAG pipeline
    try:
        result = answer_question(
            question=question,
            document_ids=document_ids,
            conversation_history=conversation_history,
            conversation_summary=conversation_summary,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate an answer: {error}",
        )

    # Save the assistant response and sources
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages (
                    chat_id,
                    role,
                    content,
                    sources
                )
                VALUES (%s, 'assistant', %s, %s)
                RETURNING id, created_at;
                """,
                (
                    chat_id,
                    result["answer"],
                    Jsonb(result["sources"]),
                ),
            )

            assistant_message = cursor.fetchone()

            save_retrieval_run(
                cursor=cursor,
                chat_id=chat_id,
                user_message_id=user_message[0],
                assistant_message_id=(
                    assistant_message[0]
                ),
                request_type="answer",
                result=result,
            )

            # Use the first question as the chat title
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM messages
                WHERE chat_id = %s
                  AND role = 'user';
                """,
                (chat_id,),
            )

            user_message_count = cursor.fetchone()[0]

            if user_message_count == 1:
                generated_title = question[:60]

                cursor.execute(
                    """
                    UPDATE chats
                    SET
                        title = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND user_id = %s;
                    """,
                    (
                        generated_title,
                        chat_id,
                        user_id,
                    ),
                )

            else:
                cursor.execute(
                    """
                    UPDATE chats
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND user_id = %s;
                    """,
                    (
                        chat_id,
                        user_id,
                    ),
                )

    return {
        "chat_id": chat_id,
        "user_message": {
            "id": user_message[0],
            "role": "user",
            "content": question,
            "created_at": user_message[1],
        },
        "assistant_message": {
            "id": assistant_message[0],
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "created_at": assistant_message[1],
        },
    }

@app.post(
    "/api/chats/{chat_id}/regenerate"
)
def regenerate_chat_answer(
    chat_id: int,
    payload: RegenerateMessageRequest,
    request: Request,
):
    user_id = request.state.user_id

    ensure_user_owns_chat(
        chat_id=chat_id,
        user_id=user_id,
    )

    if payload.document_ids is not None:
        replace_user_chat_documents(
            chat_id=chat_id,
            user_id=user_id,
            document_ids=payload.document_ids,
        )

    document_ids = get_chat_document_ids(
        chat_id=chat_id,
        user_id=user_id,
    )

    if not document_ids:
        document_ids = get_user_ready_document_ids(
            user_id
        )

    if not document_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "Upload at least one ready "
                "document before regenerating."
            ),
        )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    content
                FROM messages
                WHERE chat_id = %s
                  AND role = 'user'
                ORDER BY id DESC
                LIMIT 1;
                """,
                (chat_id,),
            )

            user_message = cursor.fetchone()

    if user_message is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "There is no question to regenerate."
            ),
        )

    user_message_id = user_message[0]
    question = user_message[1]

    try:
        result = answer_question(
            question=question,
            document_ids=document_ids,
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to regenerate the answer: "
                f"{error}"
            ),
        )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM messages
                WHERE chat_id = %s
                  AND role = 'assistant'
                  AND id > %s
                ORDER BY id ASC
                LIMIT 1;
                """,
                (
                    chat_id,
                    user_message_id,
                ),
            )

            assistant_row = cursor.fetchone()

            if assistant_row is None:
                cursor.execute(
                    """
                    INSERT INTO messages (
                        chat_id,
                        role,
                        content,
                        sources
                    )
                    VALUES (
                        %s,
                        'assistant',
                        %s,
                        %s
                    )
                    RETURNING id, created_at;
                    """,
                    (
                        chat_id,
                        result["answer"],
                        Jsonb(result["sources"]),
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE messages
                    SET
                        content = %s,
                        sources = %s,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, created_at;
                    """,
                    (
                        result["answer"],
                        Jsonb(result["sources"]),
                        assistant_row[0],
                    ),
                )

            assistant_message = cursor.fetchone()

            save_retrieval_run(
                cursor=cursor,
                chat_id=chat_id,
                user_message_id=user_message_id,
                assistant_message_id=(
                    assistant_message[0]
                ),
                request_type="regenerate",
                result=result,
            )

            cursor.execute(
                """
                UPDATE chats
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND user_id = %s;
                """,
                (
                    chat_id,
                    user_id,
                ),
            )

    return {
        "chat_id": chat_id,
        "question": question,
        "assistant_message": {
            "id": assistant_message[0],
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "created_at": assistant_message[1],
        },
    }
    
    
@app.delete("/api/chats/{chat_id}")
def delete_chat(
    chat_id: int,
    request: Request,
):
    user_id = request.state.user_id

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM chats
                WHERE id = %s
                  AND user_id = %s
                RETURNING id;
                """,
                (
                    chat_id,
                    user_id,
                ),
            )

            deleted_chat = cursor.fetchone()

    if not deleted_chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    return {
        "message": "Chat and its messages were deleted successfully."
    }
    
    
@app.patch("/api/chats/{chat_id}")
def rename_chat(
    chat_id: int,
    payload: RenameChatRequest,
    request: Request,
):
    user_id = request.state.user_id
    new_title = payload.title.strip()

    if not new_title:
        raise HTTPException(
            status_code=400,
            detail="Chat title cannot be empty."
        )

    if len(new_title) > 100:
        raise HTTPException(
            status_code=400,
            detail="Chat title cannot exceed 100 characters."
        )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chats
                SET
                    title = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND user_id = %s
                RETURNING id, title;
                """,
                (
                    new_title,
                    chat_id,
                    user_id,
                ),
            )

            renamed_chat = cursor.fetchone()

            if renamed_chat is None:
                raise HTTPException(
                    status_code=404,
                    detail="Chat not found."
                )

    return {
        "message": "Chat renamed successfully.",
        "chat": {
            "id": renamed_chat[0],
            "title": renamed_chat[1],
        },
    }
    
# --------------------------------------------------
# Retrieval analytics endpoints
# --------------------------------------------------

@app.get("/api/retrieval-analytics")
def get_retrieval_analytics(request: Request):
    """Return retrieval statistics for the signed-in user."""

    user_id = request.state.user_id

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_runs,
                    COALESCE(
                        SUM(runs.context_count),
                        0
                    ) AS total_context_chunks,
                    COALESCE(
                        AVG(runs.context_count),
                        0
                    ) AS average_context_chunks,
                    COALESCE(
                        AVG(runs.highest_similarity),
                        0
                    ) AS average_similarity,
                    COUNT(*) FILTER (
                        WHERE runs.claude_called = TRUE
                    ) AS claude_call_count
                FROM retrieval_runs AS runs
                JOIN chats
                    ON chats.id = runs.chat_id
                WHERE chats.user_id = %s;
                """,
                (user_id,),
            )

            statistics_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    runs.id,
                    chats.id,
                    chats.title,
                    user_messages.content,
                    runs.request_type,
                    runs.vector_candidate_count,
                    runs.keyword_candidate_count,
                    runs.combined_candidate_count,
                    runs.seed_count,
                    runs.context_count,
                    runs.highest_similarity,
                    runs.minimum_similarity,
                    runs.claude_called,
                    runs.created_at
                FROM retrieval_runs AS runs
                JOIN chats
                    ON chats.id = runs.chat_id
                JOIN messages AS user_messages
                    ON user_messages.id = (
                        runs.user_message_id
                    )
                WHERE chats.user_id = %s
                ORDER BY runs.created_at DESC,
                         runs.id DESC
                LIMIT 100;
                """,
                (user_id,),
            )

            run_rows = cursor.fetchall()

    runs = []

    for row in run_rows:
        runs.append(
            {
                "id": int(row[0]),
                "chat_id": int(row[1]),
                "chat_title": row[2],
                "question": row[3],
                "request_type": row[4],
                "vector_candidate_count": row[5],
                "keyword_candidate_count": row[6],
                "combined_candidate_count": row[7],
                "seed_count": row[8],
                "context_count": row[9],
                "highest_similarity": (
                    float(row[10])
                    if row[10] is not None
                    else None
                ),
                "minimum_similarity": (
                    float(row[11])
                    if row[11] is not None
                    else None
                ),
                "claude_called": bool(row[12]),
                "created_at": row[13],
            }
        )

    return {
        "statistics": {
            "total_runs": int(statistics_row[0]),
            "total_context_chunks": int(
                statistics_row[1]
            ),
            "average_context_chunks": round(
                float(statistics_row[2]),
                2,
            ),
            "average_similarity": round(
                float(statistics_row[3]),
                4,
            ),
            "claude_call_count": int(
                statistics_row[4]
            ),
        },
        "runs": runs,
    }


@app.get(
    "/api/retrieval-analytics/{retrieval_run_id}"
)
def get_retrieval_run_details(
    retrieval_run_id: int,
    request: Request,
):
    """Return one retrieval run and its context chunks."""

    user_id = request.state.user_id

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    runs.id,
                    chats.id,
                    chats.title,
                    user_messages.content,
                    assistant_messages.content,
                    runs.request_type,
                    runs.retrieval_query,
                    runs.vector_candidate_count,
                    runs.keyword_candidate_count,
                    runs.combined_candidate_count,
                    runs.seed_count,
                    runs.context_count,
                    runs.highest_similarity,
                    runs.minimum_similarity,
                    runs.claude_called,
                    runs.created_at
                FROM retrieval_runs AS runs
                JOIN chats
                    ON chats.id = runs.chat_id
                JOIN messages AS user_messages
                    ON user_messages.id = (
                        runs.user_message_id
                    )
                JOIN messages AS assistant_messages
                    ON assistant_messages.id = (
                        runs.assistant_message_id
                    )
                WHERE runs.id = %s
                  AND chats.user_id = %s;
                """,
                (
                    retrieval_run_id,
                    user_id,
                ),
            )

            run_row = cursor.fetchone()

            if run_row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Retrieval run not found.",
                )

            cursor.execute(
                """
                SELECT
                    run_chunks.context_position,
                    chunks.id,
                    run_chunks.retrieval_type,
                    run_chunks.similarity_score,
                    run_chunks.keyword_score,
                    run_chunks.hybrid_score,
                    run_chunks.reranker_score,
                    documents.filename,
                    chunks.page_number,
                    chunks.chunk_index,
                    chunks.content
                FROM retrieval_run_chunks AS run_chunks
                JOIN document_chunks AS chunks
                    ON chunks.id = run_chunks.chunk_id
                JOIN documents
                    ON documents.id = chunks.document_id
                WHERE run_chunks.retrieval_run_id = %s
                ORDER BY run_chunks.context_position,
                         chunks.id;
                """,
                (retrieval_run_id,),
            )

            chunk_rows = cursor.fetchall()

    chunks = []

    for row in chunk_rows:
        chunks.append(
            {
                "context_position": row[0],
                "chunk_id": int(row[1]),
                "retrieval_type": row[2],
                "similarity_score": (
                    float(row[3])
                    if row[3] is not None
                    else None
                ),
                "keyword_score": (
                    float(row[4])
                    if row[4] is not None
                    else None
                ),
                "hybrid_score": (
                    float(row[5])
                    if row[5] is not None
                    else None
                ),
                "reranker_score": (
                    float(row[6])
                    if row[6] is not None
                    else None
                ),
                "filename": row[7],
                "page_number": row[8],
                "chunk_index": row[9],
                "content": row[10],
            }
        )

    return {
        "run": {
            "id": int(run_row[0]),
            "chat_id": int(run_row[1]),
            "chat_title": run_row[2],
            "question": run_row[3],
            "answer": run_row[4],
            "request_type": run_row[5],
            "retrieval_query": run_row[6],
            "vector_candidate_count": run_row[7],
            "keyword_candidate_count": run_row[8],
            "combined_candidate_count": run_row[9],
            "seed_count": run_row[10],
            "context_count": run_row[11],
            "highest_similarity": (
                float(run_row[12])
                if run_row[12] is not None
                else None
            ),
            "minimum_similarity": (
                float(run_row[13])
                if run_row[13] is not None
                else None
            ),
            "claude_called": bool(run_row[14]),
            "created_at": run_row[15],
        },
        "chunks": chunks,
    }


@app.get("/api/chats/{chat_id}/export/text")
def export_chat_as_text(
    chat_id: int,
    request: Request,
):
    chat = get_chat_export_data(
        chat_id=chat_id,
        user_id=request.state.user_id,
    )

    lines = [
        chat["title"],
        "=" * 70,
        "",
    ]

    for message in chat["messages"]:
        label = (
            "QUESTION"
            if message["role"] == "user"
            else "ANSWER"
        )

        lines.extend(
            [
                label,
                "-" * 70,
                message["content"],
            ]
        )

        if message["sources"]:
            lines.append("")
            lines.append("Sources:")

            for source in message["sources"]:
                lines.append(
                    "- "
                    f"{source.get('filename', 'Unknown')} "
                    f"· Page "
                    f"{source.get('page_number', '-')}"
                )

        lines.extend(["", ""])

    text_content = "\n".join(lines)

    return Response(
        content=text_content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition":
                f'attachment; filename="chat-{chat_id}.txt"'
        },
    )


@app.get("/api/chats/{chat_id}/export/pdf")
def export_chat_as_pdf(
    chat_id: int,
    request: Request,
):
    chat = get_chat_export_data(
        chat_id=chat_id,
        user_id=request.state.user_id,
    )

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph(
            escape(chat["title"]),
            styles["Title"],
        )
    )

    story.append(Spacer(1, 18))

    for message in chat["messages"]:
        label = (
            "Question"
            if message["role"] == "user"
            else "Answer"
        )

        story.append(
            Paragraph(
                label,
                styles["Heading3"],
            )
        )

        safe_content = escape(
            message["content"]
        ).replace(
            "\n",
            "<br/>",
        )

        story.append(
            Paragraph(
                safe_content,
                styles["BodyText"],
            )
        )

        if message["sources"]:
            story.append(Spacer(1, 6))

            story.append(
                Paragraph(
                    "Sources",
                    styles["Heading4"],
                )
            )

            for source in message["sources"]:
                source_text = (
                    f"{source.get('filename', 'Unknown')} "
                    f"· Page "
                    f"{source.get('page_number', '-')}"
                )

                story.append(
                    Paragraph(
                        f"• {escape(source_text)}",
                        styles["BodyText"],
                    )
                )

        story.append(Spacer(1, 18))

    document.build(story)

    pdf_content = pdf_buffer.getvalue()
    pdf_buffer.close()

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="chat-{chat_id}.pdf"'
        },
    )
