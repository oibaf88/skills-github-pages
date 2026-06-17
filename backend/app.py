import os
import re
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field


# Backend for bfab.io newsletter subscriptions.
# Required Render environment variable:
#   DATABASE_URL=<Supabase connection pooler URL>
# Optional aliases supported:
#   SUPABASE_DATABASE_URL=<Supabase connection pooler URL>
#   POSTGRES_URL=<Supabase connection pooler URL>
# Recommended Render environment variable:
#   CORS_ORIGINS=https://bfab.io,https://www.bfab.io,https://oibaf88.github.io
# Never commit real credentials to GitHub.

TABLE_NAME = "newsletter_subscribers"


def get_database_url() -> str | None:
    raw_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("SUPABASE_DATABASE_URL")
        or os.getenv("POSTGRES_URL")
    )

    if not raw_url:
        return None

    return normalize_database_url(raw_url.strip())


def normalize_database_url(database_url: str) -> str:
    """Ensure Supabase/Postgres URLs use SSL unless already configured."""
    parsed = urlsplit(database_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    query.setdefault("sslmode", "require")
    query.setdefault("connect_timeout", "10")

    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urlencode(query),
            parsed.fragment,
        )
    )


DATABASE_URL = get_database_url()

CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://bfab.io,https://www.bfab.io,https://oibaf88.github.io,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

app = FastAPI(title="bfab.io newsletter API", version="2.1.0")

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
    if not DATABASE_URL:
        raise RuntimeError(
            "Database URL is not configured. Set DATABASE_URL in Render to your Supabase connection pooler URL."
        )
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS public.{TABLE_NAME} (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL CHECK (char_length(trim(name)) > 2),
                    email TEXT NOT NULL UNIQUE CHECK (
                        email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{{2,}}$'
                    ),
                    source TEXT,
                    user_agent TEXT,
                    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    unsubscribed_at TIMESTAMPTZ
                );
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_email
                ON public.{TABLE_NAME} (lower(email));
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_subscribed_at
                ON public.{TABLE_NAME} (subscribed_at DESC);
                """
            )
            conn.commit()


@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as exc:
        print(f"Database initialization failed: {type(exc).__name__}: {exc}")


@app.get("/")
def root():
    return {
        "service": "bfab.io newsletter API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "health_db": "/health/db",
        "health_table": "/health/table",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_url_configured": bool(DATABASE_URL),
        "cors_origins": CORS_ORIGINS,
        "table": TABLE_NAME,
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
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (TABLE_NAME,),
                )
                columns = cur.fetchall()
        return {"status": "ok", "table_exists": len(columns) > 0, "columns": columns}
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
                    f"""
                    INSERT INTO public.{TABLE_NAME} (name, email, source, user_agent)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        source = EXCLUDED.source,
                        user_agent = EXCLUDED.user_agent,
                        subscribed_at = NOW(),
                        unsubscribed_at = NULL
                    RETURNING id, name, email, source, subscribed_at;
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
            "source": row["source"],
            "subscribed_at": row["subscribed_at"].isoformat(),
        },
    }
