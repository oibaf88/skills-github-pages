import os
import re
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field


DATABASE_URL = os.getenv("DATABASE_URL")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://bfab.io,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]


app = FastAPI(title="bfab.io newsletter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
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
    """Validate a newsletter subscriber.

    Args:
        name: Name that we're attempting to validate.
        email: Email address that we're attempting to validate.
        consent: Explicit newsletter consent.

    Returns:
        bool: True if all validation checks pass.

    Raises:
        ValueError: If any validation check fails.
    """
    if validate_name(name) is False:
        raise ValueError("Please make sure your name is greater than 2 characters.")

    if validate_email(email) is False:
        raise ValueError("Your email address is in the incorrect format, please enter a valid email.")

    if consent is not True:
        raise ValueError("Newsletter consent is required.")

    return True


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not configured.")

    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get("/health")
def health():
    return {"status": "ok"}


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
        raise HTTPException(status_code=500, detail="Database write failed.") from exc

    return {
        "ok": True,
        "message": "Newsletter subscription saved.",
        "subscriber": {
            "id": str(row["id"]),
            "name": row["name"],
            "email": row["email"],
            "subscribed_at": row["subscribed_at"].isoformat(),
        },
    }
