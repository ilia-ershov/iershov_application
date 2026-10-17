"""Helpers for testing a running instance: reading the emails it sends, and calling its API."""

import email
import imaplib
import re
import subprocess
import time
import uuid
from email.header import decode_header, make_header
from email.utils import getaddresses

import dns.resolver
import requests

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CODE = re.compile(r"\b(\d{6})\b")


class Message:
    def __init__(self, to, subject, body, folder="log"):
        self.to = to.lower()
        self.subject = subject
        self.body = body
        self.folder = folder

    @property
    def code(self):
        match = CODE.search(self.body)
        return match.group(1) if match else None

    def __repr__(self):
        return f"<Message to={self.to} subject={self.subject!r} folder={self.folder}>"


class LogMailbox:
    """Reads messages the backend printed with MAIL_BACKEND=console, via a shell command
    that outputs the backend log (e.g. `docker compose logs --no-log-prefix backend`)."""

    timeout = 30

    def __init__(self, command):
        self.command = command

    def messages(self):
        output = subprocess.run(self.command, shell=True, capture_output=True, text=True, timeout=60).stdout  # noqa: S602
        text = ANSI.sub("", output)
        return [
            Message(to, subject, body)
            for to, subject, body in re.findall(r"To: (\S+)\nSubject: ([^\n]*)\n\n([^\n]*)", text)
        ]


class ImapMailbox:
    """Reads messages from a real mailbox (inbox and spam folder) over IMAP."""

    timeout = 180
    SPAM_FOLDERS = ("Spam", "Junk", "[Gmail]/Spam", "INBOX.Spam", "INBOX.Junk")

    def __init__(self, host, user, password, port=993):
        self.host, self.user, self.password, self.port = host, user, password, port

    def messages(self, last=40):
        found = []
        with imaplib.IMAP4_SSL(self.host, self.port) as imap:
            imap.login(self.user, self.password)
            for folder in ("INBOX", *self.SPAM_FOLDERS):
                status, _ = imap.select(f'"{folder}"', readonly=True)
                if status != "OK":
                    continue
                _, data = imap.uid("search", None, "ALL")
                for uid in data[0].split()[-last:]:
                    _, parts = imap.uid("fetch", uid, "(BODY.PEEK[])")
                    raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
                    if raw:
                        found.append(_parse(raw, "spam" if folder != "INBOX" else "inbox"))
        return found


def _parse(raw, folder):
    message = email.message_from_bytes(raw)
    to = ",".join(address for _, address in getaddresses(message.get_all("To", [])))
    subject = str(make_header(decode_header(message.get("Subject", ""))))
    part = message.get_body(("plain",)) if hasattr(message, "get_body") else None
    if part is None:
        part = next((p for p in message.walk() if p.get_content_type() == "text/plain"), message)
    payload = part.get_payload(decode=True) or b""
    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    return Message(to, subject, body, folder)


def wait_for(mailbox, matches, *, before, timeout=None):
    """Wait until a new message matching `matches` arrives (more matches than `before`)."""
    deadline = time.time() + (timeout or mailbox.timeout)
    while time.time() < deadline:
        found = [m for m in mailbox.messages() if matches(m)]
        if len(found) > before:
            return found[-1]
        time.sleep(1 if isinstance(mailbox, LogMailbox) else 5)
    raise AssertionError("expected email did not arrive in time")


def count(mailbox, matches):
    return sum(1 for m in mailbox.messages() if matches(m))


_resolver = dns.resolver.Resolver()
_resolver.lifetime = 10


def lookup(name, rtype):
    """DNS answers as plain strings ([] when the name or record does not exist)."""
    try:
        answer = _resolver.resolve(name, rtype)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return []
    if rtype == "TXT":
        return [b"".join(r.strings).decode() for r in answer]
    if rtype == "MX":
        return [r.exchange.to_text().rstrip(".") for r in sorted(answer, key=lambda r: r.preference)]
    return [r.to_text().rstrip(".") for r in answer]


class Api:
    def __init__(self, base_url, token=None):
        self.base = base_url.rstrip("/") + "/api"
        self.session = requests.Session()
        self.token = token

    def request(self, method, path, **kwargs):
        headers = kwargs.pop("headers", {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")
        return self.session.request(method, self.base + path, headers=headers, timeout=20, **kwargs)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def verify_email(self, mailbox, address, purpose="register"):
        """Request a code, read it from the mailbox and exchange it for a verification token."""
        is_code_mail = lambda m: m.to == address.lower() and m.code is not None  # noqa: E731
        before = count(mailbox, is_code_mail)
        for _ in range(2):
            response = self.post("/auth/request-code", json={"email": address, "purpose": purpose})
            if response.status_code != 429:
                break
            time.sleep(int(response.headers.get("Retry-After", 60)))  # per-minute limit from an earlier run
        assert response.status_code == 200, response.text
        code = wait_for(mailbox, is_code_mail, before=before).code
        response = self.post("/auth/verify-code", json={"email": address, "code": code})
        assert response.status_code == 200, response.text
        return response.json()["verification_token"]


def unique_suffix():
    return uuid.uuid4().hex[:10]
