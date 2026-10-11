# RAG Chatbot with PostgreSQL and pgvector

A document chatbot built with Python, FastAPI, PostgreSQL,
pgvector, SentenceTransformers, and Claude.

## Project contents

- Backend and authentication code in `app/`
- Frontend files in `static/` and `templates/`
- Document ingestion, search, and evaluation scripts in `scripts/`
- Database initialization SQL and Docker Compose configuration

## Setup after a fresh clone

1. Install and start Docker Desktop.
2. Create `.env` using `.env.example` as the template.
3. Set your Anthropic API key and database password in `.env`.
4. Run `docker compose up --build -d`.
5. Open http://localhost:8000 after the application starts.

## Database connection

Inside Docker, the database address is `database:5432`.
From tools on your laptop, use `localhost:5433`.

## Data migration

The repository excludes credentials, uploaded documents,
database backups, AWS keys, and generated files.

Existing database records and uploaded documents must be
transferred separately when moving to another laptop.