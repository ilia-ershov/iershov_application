"""A real account goes through the main API flows. Needs BASE_URL and a way to read codes."""

import time

import pyotp

from conftest import PASSWORD
from live_support import Api


def test_profile(account):
    response = account["api"].get("/account")
    assert response.status_code == 200
    user = response.json()["user"]
    assert user["email"] == account["email"]
    assert user["mfa_enabled"] is False


def test_alias_lifecycle(account):
    api = account["api"]
    generated = api.post("/aliases/generate").json()
    created = api.post(
        "/aliases", json={"alias_token": generated["alias_token"], "service": "Live test", "service_url": "example.com"}
    )
    assert created.status_code == 201, created.text
    alias = created.json()["alias"]
    assert alias["address"] == generated["address"]
    assert alias["service_url"] == "https://example.com"

    replay = api.post("/aliases", json={"alias_token": generated["alias_token"], "service": "again"})
    assert replay.status_code == 409

    edited = api.patch(f"/aliases/{alias['id']}", json={"service": "Renamed"})
    assert edited.json()["alias"]["service"] == "Renamed"

    assert api.post(f"/aliases/{alias['id']}/deactivate").json()["alias"]["active"] is False
    inactive = api.get("/aliases", params={"status": "inactive"}).json()["aliases"]
    assert alias["id"] in [a["id"] for a in inactive]

    assert api.post(f"/aliases/{alias['id']}/activate").json()["alias"]["active"] is True
    active = api.get("/aliases", params={"status": "active"}).json()["aliases"]
    assert alias["id"] in [a["id"] for a in active]


def test_wrong_password_is_rejected_for_sensitive_actions(account):
    response = account["api"].delete("/account", json={"password": "Wrong-pass1!"})
    assert response.status_code == 403
    assert account["api"].get("/account").status_code == 200  # still there


def test_password_change_revokes_old_sessions(account, base_url):
    api = account["api"]
    old_session = Api(base_url, token=api.token)
    response = api.post("/account/password", json={"current_password": PASSWORD, "new_password": "Temp-Passw0rd!"})
    assert response.status_code == 200, response.text
    api.token = response.json()["token"]
    assert old_session.get("/account").status_code == 401
    # change it back so the session fixture can clean up
    response = api.post("/account/password", json={"current_password": "Temp-Passw0rd!", "new_password": PASSWORD})
    assert response.status_code == 200, response.text
    api.token = response.json()["token"]


def test_two_factor_login(account, base_url):
    api = account["api"]
    setup = api.post("/account/2fa/setup").json()
    totp = pyotp.TOTP(setup["secret"])
    enabled = api.post("/account/2fa/enable", json={"setup_token": setup["setup_token"], "code": totp.now()})
    assert enabled.status_code == 200, enabled.text
    recovery_codes = enabled.json()["recovery_codes"]
    try:
        login = Api(base_url).post("/auth/login", json={"email": account["email"], "password": PASSWORD}).json()
        assert login.get("mfa_required") is True and "token" not in login
        second = Api(base_url).post(
            "/auth/login/2fa", json={"mfa_token": login["mfa_token"], "code": recovery_codes[0]}
        )
        assert second.status_code == 200, second.text
        reused = Api(base_url).post("/auth/login", json={"email": account["email"], "password": PASSWORD}).json()
        again = Api(base_url).post(
            "/auth/login/2fa", json={"mfa_token": reused["mfa_token"], "code": recovery_codes[0]}
        )
        assert again.status_code == 401, "a recovery code worked twice"
    finally:
        # a code from the next 30 s window is always fresh (the current one was used to enable 2FA)
        next_code = totp.at(time.time() + 30)
        disabled = api.post("/account/2fa/disable", json={"password": PASSWORD, "code": next_code})
        assert disabled.status_code == 200, disabled.text
