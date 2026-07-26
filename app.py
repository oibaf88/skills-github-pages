import os
import re
from datetime import datetime, timezone

from flask import Flask, jsonify, make_response, request
from supabase import Client, create_client
from werkzeug.exceptions import HTTPException


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY")
NEWSLETTER_TABLE = os.environ.get("NEWSLETTER_TABLE", "newsletter_subscribers").strip()

MAX_NAME_LENGTH = 120
MAX_EMAIL_LENGTH = 254
MAX_SOURCE_LENGTH = 200
MAX_USER_AGENT_LENGTH = 512
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
if FLASK_SECRET_KEY:
    app.secret_key = FLASK_SECRET_KEY

ALLOWED_ORIGINS = {
    "https://bfab.io",
    "https://www.bfab.io",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
}

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def cors_origin() -> str:
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    return "https://bfab.io"


def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = cors_origin()
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    response.headers["Vary"] = "Origin"
    return response


@app.after_request
def after_request(response):
    return add_cors_headers(response)


def validate_payload(payload: object) -> tuple[str, str, str]:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    name_value = payload.get("name")
    email_value = payload.get("email")
    source_value = payload.get("source", "bfab.io/signup")

    name = name_value.strip() if isinstance(name_value, str) else ""
    email = email_value.strip().lower() if isinstance(email_value, str) else ""
    source = source_value.strip() if isinstance(source_value, str) else ""
    source = source or "bfab.io/signup"

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
            "service": "skills-github-pages newsletter API",
            "status": "ok",
            "endpoints": ["/healthz", "/subscribe"],
        }
    )


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/subscribe", methods=["POST", "OPTIONS"])
def subscribe():
    if request.method == "OPTIONS":
        return make_response(("", 204))

    payload = request.get_json(silent=True)

    try:
        name, email, source = validate_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    now = datetime.now(timezone.utc).isoformat()
    user_agent = request.headers.get("User-Agent", "").strip()[:MAX_USER_AGENT_LENGTH]

    record = {
        "name": name,
        "email": email,
        "source": source,
        "user_agent": user_agent,
        "subscribed_at": now,
        "unsubscribed_at": None,
    }

    supabase.table(NEWSLETTER_TABLE).upsert(record, on_conflict="email").execute()

    return jsonify({"message": "subscribed correctly!"}), 200


@app.errorhandler(413)
def handle_payload_too_large(_error):
    return jsonify({"error": "payload_too_large"}), 413


@app.errorhandler(Exception)
def handle_exception(error):
    if isinstance(error, HTTPException):
        return error

    app.logger.exception("Unhandled newsletter API error")
    return jsonify({"error": "internal_server_error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
