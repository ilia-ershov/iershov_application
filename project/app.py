"""Mail organizer API: application factory, CLI commands and development entry point.

Run locally:      python app.py                    (reads .env)
Production:       gunicorn wsgi:app
Maintenance:      flask --app app init-db | migrate-legacy
"""

import json
import logging
import os

import click
from flask import Flask
from flask_cors import CORS
from sqlalchemy import event
from werkzeug.middleware.proxy_fix import ProxyFix

from api import api
from config import load_config, validate_config
from database import init_db, migrate_legacy
from errors import register_error_handlers
from extensions import db, limiter


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    app.config.update(overrides or {})
    validate_config(app.config)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if app.config["TRUST_PROXY"]:
        hops = app.config["TRUST_PROXY"]
        # Behind nginx: take the client IP/scheme from X-Forwarded-* (used by the rate limiter).
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops)
    if app.config["CORS_ORIGINS"]:
        # Only needed when the frontend is served from another origin; same-origin setups need no CORS.
        CORS(
            app,
            resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
            allow_headers=["Content-Type", "Authorization"],
            methods=["GET", "POST", "PATCH", "DELETE"],
            max_age=600,
        )

    db.init_app(app)
    limiter.init_app(app)
    register_error_handlers(app)
    app.register_blueprint(api)
    app.after_request(_security_headers)
    _register_commands(app)

    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            event.listen(db.engine, "connect", _enable_sqlite_foreign_keys)
        if app.config["AUTO_INIT_DB"]:
            init_db()
    return app


def _enable_sqlite_foreign_keys(dbapi_connection, _record):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


def _security_headers(response):
    headers = response.headers
    headers.setdefault("X-Content-Type-Options", "nosniff")
    headers.setdefault("X-Frame-Options", "DENY")
    headers.setdefault("Referrer-Policy", "no-referrer")
    headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    headers.setdefault("Cache-Control", "no-store")  # responses carry tokens and personal data
    return response


def _register_commands(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Create missing tables and columns."""
        init_db()
        click.echo("Database schema is up to date.")

    @app.cli.command("migrate-legacy")
    @click.option("--drop-legacy", is_flag=True, help="Drop the old emails/deactivated tables afterwards.")
    @click.option("--force", is_flag=True, help="Drop even if some legacy rows could not be migrated.")
    def migrate_legacy_command(drop_legacy, force):
        """Move aliases from the original emails/deactivated tables into the aliases table."""
        report = migrate_legacy(drop=drop_legacy, force=force)
        click.echo(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    # Debug mode (and its interactive debugger) is only enabled with FLASK_DEBUG=1.
    create_app().run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
