"""Outgoing email: SMTP in production, the server log during development."""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app

log = logging.getLogger(__name__)


def send_email(to, subject, body):
    config = current_app.config
    backend = config["MAIL_BACKEND"]

    if backend == "memory":  # used by the test-suite
        current_app.extensions.setdefault("mail_outbox", []).append({"to": to, "subject": subject, "body": body})
        return
    if backend == "console":
        log.warning("MAIL_BACKEND=console, message not delivered.\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = config["MAIL_FROM"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    host, port, timeout = config["SMTP_HOST"], config["SMTP_PORT"], config["SMTP_TIMEOUT"]
    if config["SMTP_SSL"]:
        server = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
    else:
        server = smtplib.SMTP(host, port, timeout=timeout)
    with server:
        if config["SMTP_STARTTLS"] and not config["SMTP_SSL"]:
            server.starttls(context=context)
        if config["SMTP_USERNAME"]:
            server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        server.send_message(message)
