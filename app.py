import os
import re
from datetime import datetime, timezone

from flask import Flask, jsonify, make_response, request
from supabase import Client, create_client
from werkzeug.exceptions import HTTPException


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
NEWSLETTER_TABLE = os.environ.get("NEWSLETTER_TABLE", "newsletter_subscribers").strip()
APP_RELEASE = os.environ.get("APP_RELEASE", "2.0.0").strip() or "2.0.0"

MAX_NAME_LENGTH = 120
MAX_EMAIL_LENGTH = 254
MAX_SOURCE_LENGTH = 200
MAX_REQUEST_BYTES = 16 * 1024

if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL environment variable.")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY environment variable.")

if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", NEWSLETTER_TABLE):
    raise RuntimeError("NEWSLETTER_TABLE must be a valid table identifier.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

ALLOWED_ORIGINS = {
    "https://bfab.io",
    "https://www.bfab.io",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
}

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def cors_origin() -> str | None:
    origin = request.headers.get("Origin", "")
    return origin if origin in ALLOWED_ORIGINS else None


def origin_allowed() -> bool:
    origin = request.headers.get("Origin", "")
    return not origin or origin in ALLOWED_ORIGINS


@app.after_request
def add_response_headers(response):
    allowed_origin = cors_origin()
    if allowed_origin:
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    response.headers["Access-Control-Max-Age"] = "600"
    response.headers["Vary"] = "Origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def validate_payload(payload: object) -> tuple[str, str, str]:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    name_value = payload.get("name")
    email_value = payload.get("email")
    source_value = payload.get("source", "bfab.io/signup")
    website_value = payload.get("website", "")

    name = name_value.strip() if isinstance(name_value, str) else ""
    email = email_value.strip().lower() if isinstance(email_value, str) else ""
    source = source_value.strip() if isinstance(source_value, str) else ""
    source = source or "bfab.io/signup"

    if not isinstance(website_value, str) or website_value.strip():
        raise ValueError("Invalid submission.")

    if len(name) <= 2:
        raise ValueError("Please make sure your name is greater than 2 characters.")

    if len(name) > MAX_NAME_LENGTH:
        raise ValueError("Your name is too long.")

    if len(email) > MAX_EMAIL_LENGTH or not EMAIL_RE.fullmatch(email):
        raise ValueError("Your email address is in the incorrect format, please enter a valid email.")

    if payload.get("consent") is not True:
        raise ValueError("Please accept the newsletter consent checkbox before subscribing.")

    if len(source) > MAX_SOURCE_LENGTH:
        raise ValueError("The subscription source is too long.")

    return name, email, source


@app.get("/")
def home():
    return jsonify(
        {
            "service": "bfab.io newsletter API",
            "status": "ok",
            "release": APP_RELEASE,
            "endpoints": ["/healthz", "/subscribe"],
        }
    )


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "release": APP_RELEASE}), 200


@app.route("/subscribe", methods=["POST", "OPTIONS"])
def subscribe():
    if not origin_allowed():
        return jsonify({"error": "origin_not_allowed"}), 403

    if request.method == "OPTIONS":
        return make_response(("", 204))

    payload = request.get_json(silent=True)

    try:
        name, email, source = validate_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    record = {
        "name": name,
        "email": email,
        "source": source,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    }

    (
        supabase.table(NEWSLETTER_TABLE)
        .upsert(record, on_conflict="email", ignore_duplicates=True)
        .execute()
    )

    return (
        jsonify(
            {
                "message": (
                    "If this address is eligible, the subscription has been recorded."
                )
            }
        ),
        200,
    )


@app.errorhandler(413)
def handle_payload_too_large(_error):
    return jsonify({"error": "payload_too_large"}), 413


@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return jsonify({"error": error.name, "message": error.description}), error.code

    app.logger.exception("Unhandled newsletter API error")
    return jsonify({"error": "internal_server_error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
