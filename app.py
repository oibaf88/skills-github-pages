import os
import re
from datetime import datetime, timezone

from flask import Flask, jsonify, make_response, request
from supabase import Client, create_client


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
FLASK_SECRET_KEY = (
    os.environ.get("FLASK_SECRET_KEY")
    or os.environ.get("SECRET_KEY")
    or "dev-secret-key-change-me"
)

if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL environment variable.")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY environment variable.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

ALLOWED_ORIGINS = {
    "https://bfab.io",
    "https://www.bfab.io",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
}

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


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


def validate_payload(payload: dict) -> tuple[str, str, bool, str]:
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    consent = bool(payload.get("consent"))
    source = str(payload.get("source", "bfab.io/signup")).strip() or "bfab.io/signup"

    if len(name) <= 2:
        raise ValueError("Please make sure your name is greater than 2 characters.")

    if not EMAIL_RE.match(email):
        raise ValueError("Your email address is in the incorrect format, please enter a valid email.")

    if consent is not True:
        raise ValueError("Please accept the newsletter consent checkbox before subscribing.")

    return name, email, consent, source


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

    payload = request.get_json(silent=True) or {}

    try:
        name, email, consent, source = validate_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    existing = (
        supabase.table("newsletter_subscriptions")
        .select("id,email")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    now = datetime.now(timezone.utc).isoformat()

    if existing.data:
        updated = (
            supabase.table("newsletter_subscriptions")
            .update(
                {
                    "name": name,
                    "consent": consent,
                    "source": source,
                    "status": "active",
                    "updated_at": now,
                }
            )
            .eq("email", email)
            .execute()
        )

        if not updated.data:
            raise RuntimeError("Could not update newsletter subscription.")

        return jsonify({"message": "subscribed correctly!"}), 200

    inserted = (
        supabase.table("newsletter_subscriptions")
        .insert(
            {
                "name": name,
                "email": email,
                "consent": consent,
                "source": source,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            }
        )
        .execute()
    )

    if not inserted.data:
        raise RuntimeError("Could not create newsletter subscription.")

    return jsonify({"message": "subscribed correctly!"}), 201


@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.exception(error)
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
