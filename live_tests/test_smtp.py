"""The mail server (port 25 of the MX host, or MAIL_SERVER) accepts mail only for active aliases and forwards it.

Needs MAIL_DOMAIN. The alias checks also need BASE_URL and a code source; the delivery check needs IMAP_*.
Apart from the delivery check, only the SMTP envelope is exchanged: no message is actually sent.
"""

import smtplib
import ssl
from contextlib import contextmanager
from email.message import EmailMessage

import pytest

from live_support import unique_suffix, wait_for


@pytest.fixture(scope="module")
def sender(mail_domain):
    return f"live-test@{mail_domain}"


@contextmanager
def smtp(target):
    host, port = target
    try:
        server = smtplib.SMTP(host, port, timeout=20)
    except OSError as error:
        pytest.fail(
            f"cannot connect to {host}:{port} ({error}). Either the server/provider blocks incoming port 25, "
            "or the network running the tests blocks outgoing port 25 (common on home connections)."
        )
    try:
        server.ehlo()
        yield server
    finally:
        try:
            server.quit()
        except smtplib.SMTPException:
            server.close()


def envelope(server, sender, recipient):
    """MAIL FROM + RCPT TO, then reset: returns the server's answer to RCPT."""
    code, reply = server.mail(sender)
    assert code == 250, f"MAIL FROM rejected: {code} {reply!r}"
    code, reply = server.rcpt(recipient)
    server.rset()
    return code, reply.decode(errors="replace")


@pytest.fixture
def alias(account):
    api = account["api"]
    generated = api.post("/aliases/generate").json()
    created = api.post("/aliases", json={"alias_token": generated["alias_token"], "service": "Live SMTP test"})
    assert created.status_code == 201, created.text
    return created.json()["alias"]


def test_greeting_and_hostname(smtp_target, settings):
    with smtp(smtp_target) as server:
        code, _ = server.docmd("NOOP")
        assert code == 250
        if settings.mail_server:
            return  # the name only has to match the MX host once DNS points at the server
        host = smtp_target[0]
        assert host in server.ehlo_resp.decode(errors="replace"), (
            f"EHLO reply does not name {host}; set myhostname = {host} in Postfix"
        )


def test_starttls(smtp_target, settings):
    host = smtp_target[0]
    with smtp(smtp_target) as server:
        assert server.has_extn("starttls"), "STARTTLS not offered: mail would travel unencrypted"
        context = ssl.create_default_context()
        if not settings.smtp_tls_verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        try:
            code, _ = server.starttls(context=context)
        except ssl.SSLCertVerificationError as error:
            pytest.fail(f"certificate not valid for {host} ({error.verify_message}); use a Let's Encrypt certificate")
        assert code == 220


def test_not_an_open_relay(smtp_target, sender):
    with smtp(smtp_target) as server:
        code, reply = envelope(server, sender, "someone@example.org")
    assert code >= 400, f"the server agreed to relay mail to another domain: {code} {reply}"


def test_unknown_alias_is_rejected(smtp_target, sender, mail_domain):
    with smtp(smtp_target) as server:
        code, reply = envelope(server, sender, f"no-such-alias-{unique_suffix()}@{mail_domain}")
    assert 500 <= code < 600, f"unknown address should be rejected permanently (550), got {code} {reply}"


def test_alias_is_accepted_only_while_active(smtp_target, sender, account, alias):
    api = account["api"]
    with smtp(smtp_target) as server:
        code, reply = envelope(server, sender, alias["address"])
        assert code == 250, f"active alias rejected: {code} {reply} (Postfix lookup not configured?)"

        api.post(f"/aliases/{alias['id']}/deactivate")
        code, reply = envelope(server, sender, alias["address"])
        assert 500 <= code < 600, f"deactivated alias still accepted: {code} {reply}"

        api.post(f"/aliases/{alias['id']}/activate")
        code, reply = envelope(server, sender, alias["address"])
        assert code == 250, f"reactivated alias rejected: {code} {reply}"


def test_mail_is_forwarded_to_the_inbox(smtp_target, sender, account, alias, imap_mailbox):
    token = unique_suffix()
    message = EmailMessage()
    message["From"] = sender
    message["To"] = alias["address"]
    message["Subject"] = f"Forwarding test {token}"
    message.set_content("If you can read this, forwarding works.")
    with smtp(smtp_target) as server:
        server.send_message(message)

    delivered = wait_for(imap_mailbox, lambda m: token in m.subject, before=0)
    assert delivered.folder == "inbox", "forwarded mail landed in spam: check SPF, DKIM, PTR and SRS"
