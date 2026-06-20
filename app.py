import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request, session
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


USER_KEYS = {"user1": 1, "user2": 2}
SLOT_KEYS = {1: "user1", 2: "user2"}


def get_session_key() -> str:
    """Return the browser-specific demo session key."""
    if "email_demo_session_key" not in session:
        session["email_demo_session_key"] = str(uuid.uuid4())
    return session["email_demo_session_key"]


def get_or_create_demo_session() -> dict:
    """Fetch or create the Supabase row for this browser session."""
    session_key = get_session_key()

    existing = (
        supabase.table("email_demo_sessions")
        .select("*")
        .eq("session_key", session_key)
        .limit(1)
        .execute()
    )

    if existing.data:
        return existing.data[0]

    created = (
        supabase.table("email_demo_sessions")
        .insert(
            {
                "session_key": session_key,
                "user1_name": "User1",
                "user2_name": "User2",
            }
        )
        .execute()
    )

    if not created.data:
        raise RuntimeError("Could not create demo session.")

    return created.data[0]


def slot_to_user_key(slot: int) -> str:
    return SLOT_KEYS.get(int(slot), "unknown")


def user_key_to_slot(user_key: str) -> int:
    if user_key not in USER_KEYS:
        raise KeyError("Invalid user.")
    return USER_KEYS[user_key]


def get_user_name(demo_session: dict, slot: int) -> str:
    if int(slot) == 1:
        return demo_session.get("user1_name") or "User1"
    if int(slot) == 2:
        return demo_session.get("user2_name") or "User2"
    return "Unknown"


def format_timestamp(value: str | None) -> str:
    if not value:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    clean_value = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(clean_value)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value[:16]


def fetch_emails_for_session(session_id: str) -> list[dict]:
    response = (
        supabase.table("email_demo_emails")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []


def serialize_email(email: dict, demo_session: dict, index: int, include_body: bool = False) -> dict:
    sender_slot = int(email["sender_slot"])
    receiver_slot = int(email["receiver_slot"])
    is_read = bool(email.get("is_read"))

    data = {
        "id": email["id"],
        "index": index,
        "sender": get_user_name(demo_session, sender_slot),
        "receiver": get_user_name(demo_session, receiver_slot),
        "sender_key": slot_to_user_key(sender_slot),
        "receiver_key": slot_to_user_key(receiver_slot),
        "subject": email.get("subject") or "",
        "timestamp": format_timestamp(email.get("created_at")),
        "read": is_read,
        "status": "Read" if is_read else "Unread",
    }

    if include_body:
        data["body"] = email.get("body") or ""

    return data


def serialize_state(demo_session: dict | None = None) -> dict:
    demo_session = demo_session or get_or_create_demo_session()
    emails = fetch_emails_for_session(demo_session["id"])

    inboxes = {"user1": [], "user2": []}
    counters = {"user1": 0, "user2": 0}

    for email in emails:
        receiver_key = slot_to_user_key(int(email["receiver_slot"]))
        if receiver_key not in inboxes:
            continue
        counters[receiver_key] += 1
        inboxes[receiver_key].append(
            serialize_email(email, demo_session, index=counters[receiver_key])
        )

    return {
        "users": {
            "user1": {
                "name": get_user_name(demo_session, 1),
                "inbox": inboxes["user1"],
            },
            "user2": {
                "name": get_user_name(demo_session, 2),
                "inbox": inboxes["user2"],
            },
        }
    }


def get_email_by_inbox_index(demo_session: dict, user_key: str, index: int) -> dict:
    if index < 1:
        raise IndexError("Invalid email number.")

    receiver_slot = user_key_to_slot(user_key)
    emails = fetch_emails_for_session(demo_session["id"])

    inbox_emails = [
        email
        for email in emails
        if int(email["receiver_slot"]) == receiver_slot
    ]

    actual_index = index - 1
    if actual_index >= len(inbox_emails):
        raise IndexError("Invalid email number.")

    return inbox_emails[actual_index]


@app.get("/")
def home():
    get_or_create_demo_session()
    return render_template("email_system.html")


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.get("/api/state")
def api_state():
    return jsonify(serialize_state())


@app.post("/api/users")
def api_set_users():
    payload = request.get_json(silent=True) or {}

    user1_name = str(payload.get("user1", "User1")).strip() or "User1"
    user2_name = str(payload.get("user2", "User2")).strip() or "User2"

    demo_session = get_or_create_demo_session()

    # The UI says "Create / reset users", so reset the inboxes too.
    supabase.table("email_demo_emails").delete().eq(
        "session_id", demo_session["id"]
    ).execute()

    updated = (
        supabase.table("email_demo_sessions")
        .update(
            {
                "user1_name": user1_name,
                "user2_name": user2_name,
            }
        )
        .eq("id", demo_session["id"])
        .execute()
    )

    if not updated.data:
        raise RuntimeError("Could not update users.")

    return jsonify(serialize_state(updated.data[0]))


@app.post("/api/send")
def api_send_email():
    payload = request.get_json(silent=True) or {}

    sender_key = payload.get("sender")
    subject = str(payload.get("subject", "")).strip()
    body = str(payload.get("body", "")).strip()

    if sender_key not in USER_KEYS:
        return jsonify({"error": "Invalid sender."}), 400
    if not subject:
        return jsonify({"error": "Subject is required."}), 400
    if not body:
        return jsonify({"error": "Body is required."}), 400

    demo_session = get_or_create_demo_session()
    sender_slot = user_key_to_slot(sender_key)
    receiver_slot = 2 if sender_slot == 1 else 1

    inserted = (
        supabase.table("email_demo_emails")
        .insert(
            {
                "session_id": demo_session["id"],
                "sender_slot": sender_slot,
                "receiver_slot": receiver_slot,
                "subject": subject,
                "body": body,
                "is_read": False,
            }
        )
        .execute()
    )

    if not inserted.data:
        raise RuntimeError("Could not send email.")

    sender_name = get_user_name(demo_session, sender_slot)
    receiver_name = get_user_name(demo_session, receiver_slot)

    return jsonify(
        {
            "message": f"Email sent from {sender_name} to {receiver_name}!",
            "state": serialize_state(demo_session),
        }
    ), 201


@app.post("/api/read/<user_key>/<int:index>")
def api_read_email(user_key, index):
    try:
        demo_session = get_or_create_demo_session()
        email = get_email_by_inbox_index(demo_session, user_key, index)
    except KeyError:
        return jsonify({"error": "Invalid user."}), 400
    except IndexError as exc:
        return jsonify({"error": str(exc)}), 404

    updated = (
        supabase.table("email_demo_emails")
        .update({"is_read": True})
        .eq("id", email["id"])
        .eq("session_id", demo_session["id"])
        .execute()
    )

    if not updated.data:
        raise RuntimeError("Could not mark email as read.")

    return jsonify(
        {
            "email": serialize_email(updated.data[0], demo_session, index=index, include_body=True),
            "state": serialize_state(demo_session),
        }
    )


@app.delete("/api/email/<user_key>/<int:index>")
def api_delete_email(user_key, index):
    try:
        demo_session = get_or_create_demo_session()
        email = get_email_by_inbox_index(demo_session, user_key, index)
    except KeyError:
        return jsonify({"error": "Invalid user."}), 400
    except IndexError as exc:
        return jsonify({"error": str(exc)}), 404

    deleted = (
        supabase.table("email_demo_emails")
        .delete()
        .eq("id", email["id"])
        .eq("session_id", demo_session["id"])
        .execute()
    )

    if not deleted.data:
        raise RuntimeError("Could not delete email.")

    return jsonify(
        {
            "message": "Email deleted.",
            "state": serialize_state(demo_session),
        }
    )


@app.post("/api/reset")
def api_reset():
    demo_session = get_or_create_demo_session()

    supabase.table("email_demo_emails").delete().eq(
        "session_id", demo_session["id"]
    ).execute()

    updated = (
        supabase.table("email_demo_sessions")
        .update(
            {
                "user1_name": "User1",
                "user2_name": "User2",
            }
        )
        .eq("id", demo_session["id"])
        .execute()
    )

    return jsonify(serialize_state(updated.data[0] if updated.data else demo_session))


@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.exception(error)
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
