import importlib
import os
import sys
import types

import pytest


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.pending = None

    def upsert(self, record, **kwargs):
        self.pending = {"table": self.table_name, "record": record, "kwargs": kwargs}
        return self

    def execute(self):
        self.client.calls.append(self.pending)
        return types.SimpleNamespace(data=[])


class FakeSupabase:
    def __init__(self):
        self.calls = []

    def table(self, table_name):
        return FakeQuery(self, table_name)


fake_supabase = FakeSupabase()
fake_module = types.ModuleType("supabase")
fake_module.Client = FakeSupabase
fake_module.create_client = lambda _url, _key: fake_supabase
sys.modules["supabase"] = fake_module

os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role"
os.environ["APP_RELEASE"] = "2.0.0"

app_module = importlib.import_module("app")


@pytest.fixture
def client():
    fake_supabase.calls.clear()
    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


def valid_payload():
    return {
        "name": "Fabio",
        "email": "Fabio@example.com",
        "website": "",
        "consent": True,
        "source": "bfab.io/signup",
    }


def test_health_exposes_release_and_security_headers(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"release": "2.0.0", "status": "ok"}
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_subscription_is_minimal_and_duplicate_safe(client):
    response = client.post(
        "/subscribe",
        json=valid_payload(),
        headers={"Origin": "https://bfab.io", "User-Agent": "not-stored"},
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://bfab.io"
    assert "eligible" in response.get_json()["message"]

    assert len(fake_supabase.calls) == 1
    call = fake_supabase.calls[0]
    assert call["table"] == "newsletter_subscribers"
    assert call["kwargs"] == {"ignore_duplicates": True, "on_conflict": "email"}
    assert call["record"]["email"] == "fabio@example.com"
    assert set(call["record"]) == {"email", "name", "source", "subscribed_at"}


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("name", "x", "name"),
        ("email", "invalid", "email"),
        ("consent", False, "consent"),
        ("website", "https://spam.invalid", "invalid"),
    ],
)
def test_invalid_subscriptions_are_rejected(client, field, value, expected):
    payload = valid_payload()
    payload[field] = value

    response = client.post("/subscribe", json=payload, headers={"Origin": "https://bfab.io"})

    assert response.status_code == 400
    assert expected in response.get_json()["error"].lower()
    assert fake_supabase.calls == []


def test_untrusted_browser_origin_is_rejected(client):
    response = client.post(
        "/subscribe",
        json=valid_payload(),
        headers={"Origin": "https://attacker.invalid"},
    )

    assert response.status_code == 403
    assert response.get_json() == {"error": "origin_not_allowed"}
    assert "Access-Control-Allow-Origin" not in response.headers
    assert fake_supabase.calls == []


def test_preflight_only_allows_portfolio_origins(client):
    allowed = client.options("/subscribe", headers={"Origin": "https://bfab.io"})
    denied = client.options("/subscribe", headers={"Origin": "https://attacker.invalid"})

    assert allowed.status_code == 204
    assert allowed.headers["Access-Control-Allow-Origin"] == "https://bfab.io"
    assert denied.status_code == 403


def test_request_size_limit(client):
    response = client.post(
        "/subscribe",
        data="{" + ("x" * app_module.MAX_REQUEST_BYTES) + "}",
        headers={"Content-Type": "application/json", "Origin": "https://bfab.io"},
    )

    assert response.status_code == 413
    assert response.get_json() == {"error": "payload_too_large"}


def test_database_errors_do_not_leak_details(client, monkeypatch):
    def failed_table(_table_name):
        raise RuntimeError("private database detail")

    monkeypatch.setattr(fake_supabase, "table", failed_table)
    response = client.post(
        "/subscribe",
        json=valid_payload(),
        headers={"Origin": "https://bfab.io"},
    )

    assert response.status_code == 500
    assert response.get_json() == {"error": "internal_server_error"}
    assert b"private database detail" not in response.data
