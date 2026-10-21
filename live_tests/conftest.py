"""Tests against a RUNNING instance: the local Docker stack or a real deployment.

Each group of checks turns on when its settings are present and is skipped otherwise.

  BASE_URL           site to test, e.g. http://127.0.0.1:8080 or https://example.com  (web, API, browser)
  CODE_LOG_COMMAND   command printing the backend log, to read verification codes when MAIL_BACKEND=console,
                     e.g. "docker compose logs --no-log-prefix backend"
  IMAP_HOST, IMAP_USER, IMAP_PASSWORD
                     a real mailbox that supports plus-addressing (Gmail, Yandex, Outlook...). Test accounts
                     use addresses like user+mo1a2b3c@gmail.com; codes and forwarded mail are read from it
  MAIL_DOMAIN        alias domain, e.g. example.com                                          (DNS, SMTP)
  MAIL_SERVER        host[:port] for the SMTP checks instead of the MX host, e.g. to test the mail server
                     before the MX record points at it
  SERVER_IP          public IPv4 of the server                                     (address, PTR, SPF checks)
  DKIM_SELECTOR      default "mail"
  SMTP_TLS_VERIFY    "0" to accept a self-signed certificate on port 25

Every value can also be passed as an option, e.g. --base-url=https://example.com.
"""

import os
from dataclasses import dataclass
from urllib.parse import urlsplit

import pytest

from live_support import Api, ImapMailbox, LogMailbox, lookup, unique_suffix

PASSWORD = "Live-test-Passw0rd!"
OPTIONS = {
    "base_url": "BASE_URL",
    "code_log_command": "CODE_LOG_COMMAND",
    "imap_host": "IMAP_HOST",
    "imap_user": "IMAP_USER",
    "imap_password": "IMAP_PASSWORD",
    "mail_domain": "MAIL_DOMAIN",
    "mail_server": "MAIL_SERVER",
    "server_ip": "SERVER_IP",
    "dkim_selector": "DKIM_SELECTOR",
    "smtp_tls_verify": "SMTP_TLS_VERIFY",
}


def pytest_addoption(parser):
    for name, env in OPTIONS.items():
        parser.addoption("--" + name.replace("_", "-"), default=None, help=f"defaults to ${env}")


@dataclass
class Settings:
    base_url: str | None
    code_log_command: str | None
    imap_host: str | None
    imap_user: str | None
    imap_password: str | None
    mail_domain: str | None
    mail_server: str | None
    server_ip: str | None
    dkim_selector: str
    smtp_tls_verify: bool

    @property
    def web_host(self):
        return urlsplit(self.base_url).hostname if self.base_url else None


@pytest.fixture(scope="session")
def settings(pytestconfig):
    def value(name):
        return pytestconfig.getoption(name) or os.getenv(OPTIONS[name]) or None

    return Settings(
        base_url=(value("base_url") or "").rstrip("/") or None,
        code_log_command=value("code_log_command"),
        imap_host=value("imap_host"),
        imap_user=value("imap_user"),
        imap_password=value("imap_password"),
        mail_domain=(value("mail_domain") or "").lower() or None,
        mail_server=value("mail_server"),
        server_ip=value("server_ip"),
        dkim_selector=value("dkim_selector") or "mail",
        smtp_tls_verify=(value("smtp_tls_verify") or "1") != "0",
    )


@pytest.fixture(scope="session")
def base_url(settings):
    if not settings.base_url:
        pytest.skip("set BASE_URL to test the website and API")
    return settings.base_url


@pytest.fixture(scope="session")
def mail_domain(settings):
    if not settings.mail_domain:
        pytest.skip("set MAIL_DOMAIN to test DNS and the mail server")
    return settings.mail_domain


@pytest.fixture(scope="session")
def mx_host(mail_domain):
    hosts = lookup(mail_domain, "MX")
    assert hosts, f"no MX record for {mail_domain}: add  MX @ -> mail.{mail_domain}  (priority 10)"
    return hosts[0]


@pytest.fixture(scope="session")
def smtp_target(settings, mail_domain):
    """(host, port) of the mail server: MAIL_SERVER if given, else the MX host on port 25."""
    if settings.mail_server:
        host, _, port = settings.mail_server.partition(":")
        return host, int(port or 25)
    hosts = lookup(mail_domain, "MX")
    assert hosts, f"no MX record for {mail_domain}: add  MX @ -> mail.{mail_domain}  (priority 10)"
    return hosts[0], 25


@pytest.fixture(scope="session")
def imap_mailbox(settings):
    if not (settings.imap_host and settings.imap_user and settings.imap_password):
        pytest.skip("set IMAP_HOST, IMAP_USER and IMAP_PASSWORD to test real mail delivery")
    return ImapMailbox(settings.imap_host, settings.imap_user, settings.imap_password)


@pytest.fixture(scope="session")
def mailbox(settings):
    """Where verification codes can be read: a real IMAP mailbox, else the backend log."""
    if settings.imap_host and settings.imap_user and settings.imap_password:
        return ImapMailbox(settings.imap_host, settings.imap_user, settings.imap_password)
    if settings.code_log_command:
        return LogMailbox(settings.code_log_command)
    pytest.skip("set CODE_LOG_COMMAND (console mail) or IMAP_* (real mail) so tests can read verification codes")


@pytest.fixture(scope="session")
def new_email(settings, mailbox):
    """Factory for unique main addresses that the mailbox can read."""

    def make():
        if isinstance(mailbox, ImapMailbox):
            local, domain = settings.imap_user.split("@")
            return f"{local}+mo{unique_suffix()}@{domain}"
        return f"live-{unique_suffix()}@example.com"

    return make


@pytest.fixture(scope="session")
def account(base_url, mailbox, new_email):
    """A fresh account for the test session; deleted (and checked to be gone) at the end."""
    api = Api(base_url)
    address = new_email()
    token = api.verify_email(mailbox, address)
    response = api.post(
        "/auth/register",
        json={"name": "Live test", "email": address, "password": PASSWORD, "verification_token": token},
    )
    assert response.status_code == 201, response.text
    api.token = response.json()["token"]
    state = {"api": api, "email": address, "password": PASSWORD}
    yield state

    api.token = state["api"].token
    response = api.delete("/account", json={"password": state["password"]})
    assert response.status_code == 200, f"cleanup failed: {response.text}"
    login = Api(base_url).post("/auth/login", json={"email": address, "password": state["password"]})
    assert login.status_code == 401, "account still exists after deletion"
