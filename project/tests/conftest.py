"""Test fixtures.

Runs against in-memory SQLite by default. Set TEST_DATABASE_URL to run the same suite
against PostgreSQL (required for the legacy-migration tests), e.g.
    TEST_DATABASE_URL=postgresql://user:pass@localhost/mail_organizer_test pytest
"""

import os
import re
import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from config import normalize_database_url  # noqa: E402
from database import init_db  # noqa: E402
from extensions import db  # noqa: E402

PASSWORD = "Passw0rd!"
TEST_DATABASE_URL = normalize_database_url(os.getenv("TEST_DATABASE_URL", "sqlite://"))


def make_app(**overrides):
    config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-that-is-long-enough-0123456789",
        "SQLALCHEMY_DATABASE_URI": TEST_DATABASE_URL,
        "AUTO_INIT_DB": False,
        "MAIL_BACKEND": "memory",
        "RATELIMIT_ENABLED": False,
        "BCRYPT_ROUNDS": 4,
        "CODE_RESEND_COOLDOWN": timedelta(0),
        "CORS_ORIGINS": [],
        "TRUST_PROXY": 0,
    }
    config.update(overrides)
    return create_app(config)


@pytest.fixture
def app_factory():
    """Build an app with custom config; its database is reset before and after the test."""
    created = []

    def factory(**overrides):
        application = make_app(**overrides)
        ctx = application.app_context()
        ctx.push()
        db.drop_all()
        init_db()
        created.append(ctx)
        return application

    yield factory
    for ctx in reversed(created):
        db.session.remove()
        db.drop_all()
        ctx.pop()


@pytest.fixture
def app(app_factory):
    return app_factory()


@pytest.fixture
def client(app):
    return app.test_client()


def outbox(app):
    return app.extensions.setdefault("mail_outbox", [])


def last_code(app, email):
    email = email.strip().lower()
    for message in reversed(outbox(app)):
        if message["to"] == email:
            match = re.search(r"\b(\d{6})\b", message["body"])
            if match:
                return match.group(1)
    raise AssertionError(f"no code was sent to {email}")


def verify_email(client, app, email, purpose="register"):
    response = client.post("/api/auth/request-code", json={"email": email, "purpose": purpose})
    assert response.status_code == 200, response.get_json()
    response = client.post("/api/auth/verify-code", json={"email": email, "code": last_code(app, email)})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["verification_token"]


def register(client, app, email="user@example.com", password=PASSWORD, name="User"):
    token = verify_email(client, app, email)
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password, "verification_token": token},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_alias(client, token, service="GitHub", service_url="github.com"):
    generated = client.post("/api/aliases/generate", headers=auth(token)).get_json()
    response = client.post(
        "/api/aliases",
        headers=auth(token),
        json={"alias_token": generated["alias_token"], "service": service, "service_url": service_url},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["alias"]
