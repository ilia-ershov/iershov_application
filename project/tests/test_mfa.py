import time

import pyotp
import pytest

from conftest import PASSWORD, auth, register


def code_at(secret, offset_steps=0):
    return pyotp.TOTP(secret).at(time.time() + offset_steps * 30)


@pytest.fixture
def mfa_user(client, app):
    """A registered user with 2FA enabled: (token, secret, recovery_codes)."""
    token = register(client, app, email="mfa@example.com")
    setup = client.post("/api/account/2fa/setup", headers=auth(token)).get_json()
    assert setup["otpauth_uri"].startswith("otpauth://totp/")
    response = client.post(
        "/api/account/2fa/enable",
        headers=auth(token),
        json={"setup_token": setup["setup_token"], "code": code_at(setup["secret"])},
    )
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["user"]["mfa_enabled"] is True
    assert len(body["recovery_codes"]) == 10
    return token, setup["secret"], body["recovery_codes"]


def start_login(client):
    response = client.post("/api/auth/login", json={"email": "mfa@example.com", "password": PASSWORD})
    assert response.status_code == 200
    body = response.get_json()
    assert body["mfa_required"] is True and "token" not in body
    return body["mfa_token"]


def test_login_requires_second_factor(client, mfa_user):
    _, secret, _ = mfa_user
    mfa_token = start_login(client)
    # the intermediate token is not a session
    assert client.get("/api/account", headers=auth(mfa_token)).status_code == 401

    bad = client.post("/api/auth/login/2fa", json={"mfa_token": mfa_token, "code": "000000"})
    assert bad.status_code == 401

    # the code used to enable 2FA was for the current step; the next step's code is fresh
    good = client.post("/api/auth/login/2fa", json={"mfa_token": mfa_token, "code": code_at(secret, 1)})
    assert good.status_code == 200
    assert client.get("/api/account", headers=auth(good.get_json()["token"])).status_code == 200


def test_totp_codes_cannot_be_replayed(client, mfa_user):
    _, secret, _ = mfa_user
    code = code_at(secret, 1)
    assert client.post("/api/auth/login/2fa", json={"mfa_token": start_login(client), "code": code}).status_code == 200
    replay = client.post("/api/auth/login/2fa", json={"mfa_token": start_login(client), "code": code})
    assert replay.status_code == 401


def test_recovery_codes_work_once(client, mfa_user):
    _, _, recovery_codes = mfa_user
    code = recovery_codes[0]
    first = client.post("/api/auth/login/2fa", json={"mfa_token": start_login(client), "code": code.upper()})
    assert first.status_code == 200
    assert first.get_json()["user"]["recovery_codes_left"] == 9
    second = client.post("/api/auth/login/2fa", json={"mfa_token": start_login(client), "code": code})
    assert second.status_code == 401


def test_enable_rejects_wrong_code_and_foreign_setup(client, app):
    alice = register(client, app, email="alice@example.com")
    bob = register(client, app, email="bob@example.com")
    setup = client.post("/api/account/2fa/setup", headers=auth(alice)).get_json()

    wrong = client.post(
        "/api/account/2fa/enable", headers=auth(alice), json={"setup_token": setup["setup_token"], "code": "123456"}
    )
    assert wrong.status_code == 400

    foreign = client.post(
        "/api/account/2fa/enable",
        headers=auth(bob),
        json={"setup_token": setup["setup_token"], "code": code_at(setup["secret"])},
    )
    assert foreign.status_code == 400
    assert foreign.get_json()["code"] == "invalid_setup_token"


def test_disable_requires_password_and_code(client, mfa_user):
    token, secret, _ = mfa_user
    no_password = client.post(
        "/api/account/2fa/disable", headers=auth(token), json={"password": "x", "code": code_at(secret, 1)}
    )
    assert no_password.status_code == 403
    no_code = client.post(
        "/api/account/2fa/disable", headers=auth(token), json={"password": PASSWORD, "code": "000000"}
    )
    assert no_code.status_code == 403

    ok = client.post(
        "/api/account/2fa/disable", headers=auth(token), json={"password": PASSWORD, "code": code_at(secret, 1)}
    )
    assert ok.status_code == 200
    assert ok.get_json()["user"]["mfa_enabled"] is False
    login = client.post("/api/auth/login", json={"email": "mfa@example.com", "password": PASSWORD})
    assert "token" in login.get_json()


def test_pending_2fa_login_dies_with_a_password_change(client, app, mfa_user):
    """A pending 2FA login started before a password change must not complete afterwards."""
    token, secret, _ = mfa_user
    mfa_token = start_login(client)
    client.post(
        "/api/account/password",
        headers=auth(token),
        json={"current_password": PASSWORD, "new_password": "An0ther-pass"},
    )
    response = client.post("/api/auth/login/2fa", json={"mfa_token": mfa_token, "code": code_at(secret, 1)})
    assert response.status_code == 401
    assert response.get_json()["code"] == "mfa_expired"
