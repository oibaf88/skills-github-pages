import datetime
import os
import uuid

from flask import Flask, jsonify, render_template, request, session


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# In-memory demo storage keyed by browser session.
# This is intentionally simple for a portfolio demo. Render restarts will clear it.
SESSIONS = {}


class Email:
    def __init__(self, sender, receiver, subject, body):
        self.sender = sender
        self.receiver = receiver
        self.subject = subject
        self.body = body
        self.timestamp = datetime.datetime.now()
        self.read = False

    def mark_as_read(self):
        self.read = True

    def to_summary(self, index):
        return {
            "index": index,
            "sender": self.sender.name,
            "receiver": self.receiver.name,
            "subject": self.subject,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M"),
            "read": self.read,
            "status": "Read" if self.read else "Unread",
        }

    def to_detail(self, index):
        data = self.to_summary(index)
        data["body"] = self.body
        return data


class User:
    def __init__(self, name):
        self.name = name
        self.inbox = Inbox()

    def send_email(self, receiver, subject, body):
        email = Email(sender=self, receiver=receiver, subject=subject, body=body)
        receiver.inbox.receive_email(email)
        return email


class Inbox:
    def __init__(self):
        self.emails = []

    def receive_email(self, email):
        self.emails.append(email)

    def list_emails(self):
        return [email.to_summary(index=i) for i, email in enumerate(self.emails, start=1)]

    def read_email(self, index):
        actual_index = index - 1
        if actual_index < 0 or actual_index >= len(self.emails):
            raise IndexError("Invalid email number.")
        email = self.emails[actual_index]
        email.mark_as_read()
        return email.to_detail(index=index)

    def delete_email(self, index):
        actual_index = index - 1
        if actual_index < 0 or actual_index >= len(self.emails):
            raise IndexError("Invalid email number.")
        del self.emails[actual_index]


def create_demo_state(user1_name="User1", user2_name="User2"):
    return {
        "user1": User(user1_name or "User1"),
        "user2": User(user2_name or "User2"),
    }


def get_session_id():
    current_id = session.get("email_demo_session_id")
    if not current_id or current_id not in SESSIONS:
        current_id = str(uuid.uuid4())
        session["email_demo_session_id"] = current_id
        SESSIONS[current_id] = create_demo_state()
    return current_id


def get_state():
    return SESSIONS[get_session_id()]


def get_user(state, key):
    if key not in ("user1", "user2"):
        raise KeyError("Invalid user key.")
    return state[key]


def serialize_state(state):
    return {
        "users": {
            "user1": {
                "name": state["user1"].name,
                "inbox": state["user1"].inbox.list_emails(),
            },
            "user2": {
                "name": state["user2"].name,
                "inbox": state["user2"].inbox.list_emails(),
            },
        }
    }


@app.get("/")
def home():
    get_state()
    return render_template("email_system.html")


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.get("/api/state")
def api_state():
    return jsonify(serialize_state(get_state()))


@app.post("/api/users")
def api_set_users():
    payload = request.get_json(silent=True) or {}
    user1_name = str(payload.get("user1", "User1")).strip() or "User1"
    user2_name = str(payload.get("user2", "User2")).strip() or "User2"

    session_id = get_session_id()
    SESSIONS[session_id] = create_demo_state(user1_name, user2_name)
    return jsonify(serialize_state(SESSIONS[session_id]))


@app.post("/api/send")
def api_send_email():
    payload = request.get_json(silent=True) or {}
    sender_key = payload.get("sender")
    subject = str(payload.get("subject", "")).strip()
    body = str(payload.get("body", "")).strip()

    if sender_key not in ("user1", "user2"):
        return jsonify({"error": "Invalid sender."}), 400
    if not subject:
        return jsonify({"error": "Subject is required."}), 400
    if not body:
        return jsonify({"error": "Body is required."}), 400

    state = get_state()
    receiver_key = "user2" if sender_key == "user1" else "user1"
    sender = get_user(state, sender_key)
    receiver = get_user(state, receiver_key)
    sender.send_email(receiver, subject, body)

    return jsonify({
        "message": f"Email sent from {sender.name} to {receiver.name}!",
        "state": serialize_state(state),
    })


@app.post("/api/read/<user_key>/<int:index>")
def api_read_email(user_key, index):
    try:
        state = get_state()
        user = get_user(state, user_key)
        email = user.inbox.read_email(index)
    except KeyError:
        return jsonify({"error": "Invalid user."}), 400
    except IndexError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify({
        "email": email,
        "state": serialize_state(state),
    })


@app.delete("/api/email/<user_key>/<int:index>")
def api_delete_email(user_key, index):
    try:
        state = get_state()
        user = get_user(state, user_key)
        user.inbox.delete_email(index)
    except KeyError:
        return jsonify({"error": "Invalid user."}), 400
    except IndexError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify({
        "message": "Email deleted.",
        "state": serialize_state(state),
    })


@app.post("/api/reset")
def api_reset():
    session_id = get_session_id()
    SESSIONS[session_id] = create_demo_state()
    return jsonify(serialize_state(SESSIONS[session_id]))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
