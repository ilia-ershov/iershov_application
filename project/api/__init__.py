"""JSON API, served under /api so it never collides with the frontend's routes."""

from flask import Blueprint, jsonify
from sqlalchemy import text

from extensions import db, limiter

from . import account, aliases, auth

api = Blueprint("api", __name__, url_prefix="/api")
api.register_blueprint(auth.bp)
api.register_blueprint(account.bp)
api.register_blueprint(aliases.bp)


@api.get("/health")
@limiter.exempt
def health():
    db.session.execute(text("SELECT 1"))
    return jsonify(status="ok")
