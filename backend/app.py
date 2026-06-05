import os
import re
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------
# bfab.io newsletter API
# ---------------------------------------------------------------------
# This version deliberately DOES NOT use DATABASE_URL.
#
# Reason:
# DATABASE_URL was being parsed incorrectly and caused:
# OperationalError: [Errno -8] Servname not supported for ai_socktype
#
# Instead, configure these variables separately in Render:
#
# DB_HOST
# DB_PORT
# DB_NAME
# DB_USER
# DB_PASSWORD
# DB_SSLMODE
# ---------------------------------------------------------------------

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://bfab.io,https://www.bfab.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]


app = FastAPI(title="bfab.io newsletter API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


class NewsletterSubscription(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    consent: bool
    source: Optional[str] = Field(default="bfab.io/signup", max_length=180)


def validate_name(name: str) -> bool:
    return isinstance(name, str) and len(name.strip()) > 2


def validate_email(email: str) -> bool:
    if not isinstance(email, str):
        return False

    return re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email.strip()) is not None


def validate_newsletter_user(name: str, email: str, consent: bool) -> bool:
    if validate_name(name) is False:
        raise ValueError("Please make sure your name is greater than 2 characters.")

    if validate_email(email) is False:
        raise ValueError("Your email address is in the incorrect format, please enter a valid email.")

    if consent is not True:
        raise ValueError("Newsletter consent is required.")

    return True


def get_connection():
    missing = []

    if not DB_HOST:
        missing.append("DB_HOST")
    if not DB_USER:
        missing.append("DB_USER")
    if not DB_PASSWORD:
        missing.append("DB_PASSWORD")

    if missing:
        raise RuntimeError(f"Missing database environment variables: {', '.join(missing)}")

    try:
        port = int(DB_PORT)
    except ValueError as exc:
        raise RuntimeError(f"DB_PORT must be numeric. Current value: {DB_PORT!r}") from exc

    return psycopg.connect(
        host=DB_HOST,
        port=port,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=DB_SSLMODE,
        row_factory=dict_row,
    )


def init_db():
    """Create the newsletter table if it does not already exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL CHECK (char_length(trim(name)) > 2),
                    email TEXT NOT NULL UNIQUE CHECK (
                        email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}$'
                    ),
                    source TEXT,
                    user_agent TEXT,
                    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    unsubscribed_at TIMESTAMPTZ
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_email
                ON newsletter_subscribers (lower(email));
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_subscribed_at
                ON newsletter_subscribers (subscribed_at DESC);
                """
            )
            conn.commit()


@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as exc:
        # Keep the API online so /health and /health/db can diagnose the issue.
        print(f"Database initialization failed: {type(exc).__name__}: {exc}")


@app.get("/")
def root():
    return {
        "service": "bfab.io newsletter API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_configured": bool(DB_HOST and DB_USER and DB_PASSWORD),
        "db_host": DB_HOST,
        "db_port": DB_PORT,
        "db_name": DB_NAME,
        "db_user": DB_USER,
        "db_sslmode": DB_SSLMODE,
        "cors_origins": CORS_ORIGINS,
    }


@app.get("/health/db")
def health_db():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok;")
                row = cur.fetchone()

        return {"status": "ok", "database": row["ok"]}

    except Exception as exc:
        print(f"Database health check failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )


@app.get("/health/table")
def health_table():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'newsletter_subscribers'
                    ORDER BY ordinal_position;
                    """
                )
                columns = cur.fetchall()

        return {
            "status": "ok",
            "table_exists": len(columns) > 0,
            "columns": columns,
        }

    except Exception as exc:
        print(f"Table health check failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )


@app.post("/subscribe")
def subscribe(payload: NewsletterSubscription, request: Request):
    try:
        validate_newsletter_user(payload.name, str(payload.email), payload.consent)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    name = payload.name.strip()
    email = str(payload.email).strip().lower()
    source = (payload.source or "bfab.io/signup").strip()
    user_agent = request.headers.get("user-agent", "")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO newsletter_subscribers (name, email, source, user_agent)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        source = EXCLUDED.source,
                        user_agent = EXCLUDED.user_agent,
                        subscribed_at = NOW(),
                        unsubscribed_at = NULL
                    RETURNING id, name, email, subscribed_at;
                    """,
                    (name, email, source, user_agent),
                )
                row = cur.fetchone()
                conn.commit()

    except Exception as exc:
        print(f"Database write failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )

    return {
        "ok": True,
        "message": "Newsletter subscription saved.",
        "subscriber": {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "subscribed_at": row["subscribed_at"].isoformat(),
        },
    }
