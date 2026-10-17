"""Database models."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Uuid

from extensions import db


def utcnow():
    return datetime.now(UTC)


def as_utc(value):
    """SQLite drops tzinfo on read; treat naive datetimes from the database as UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def iso(value):
    return as_utc(value).astimezone(UTC).isoformat() if value else None


class User(db.Model):
    __tablename__ = "users"

    uuid = db.Column(Uuid, primary_key=True, default=uuid4)
    name = db.Column(String(255), nullable=False)
    # Stored lower-cased (see validation.normalize_email), so lookups can use the unique index.
    email = db.Column(String(255), unique=True, nullable=False)
    password_hash = db.Column(String(128), nullable=False)
    # Embedded in every access token; bumping it revokes all of the user's sessions.
    token_version = db.Column(Integer, nullable=False, default=0, server_default="0")
    totp_secret = db.Column(String(64))
    totp_last_step = db.Column(Integer)
    recovery_codes = db.Column(JSON)  # HMAC-SHA256 digests of the unused recovery codes

    aliases = db.relationship("Alias", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def mfa_enabled(self):
        return bool(self.totp_secret)

    def to_dict(self):
        return {
            "id": str(self.uuid),
            "name": self.name,
            "email": self.email,
            "mfa_enabled": self.mfa_enabled,
            "recovery_codes_left": len(self.recovery_codes or []),
        }


class Alias(db.Model):
    """A forwarding address <local_part>@MAIL_DOMAIN that belongs to one user."""

    __tablename__ = "aliases"

    uuid = db.Column(Uuid, primary_key=True, default=uuid4)
    user_id = db.Column(Uuid, ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    local_part = db.Column(String(64), unique=True, nullable=False)
    service = db.Column(String(100), nullable=False)
    service_url = db.Column(String(2048), nullable=False, default="")
    is_active = db.Column(Boolean, nullable=False, default=True)
    created_at = db.Column(DateTime(timezone=True), nullable=False, default=utcnow)
    deactivated_at = db.Column(DateTime(timezone=True))

    user = db.relationship("User", back_populates="aliases")

    # Serves the per-user listing (filter by owner and state, newest first).
    __table_args__ = (Index("ix_aliases_user_active_created", "user_id", "is_active", "created_at"),)

    def to_dict(self, domain):
        return {
            "id": str(self.uuid),
            "alias": self.local_part,
            "address": f"{self.local_part}@{domain}",
            "service": self.service,
            "service_url": self.service_url,
            "active": self.is_active,
            "created_at": iso(self.created_at),
            "deactivated_at": iso(self.deactivated_at),
        }


class EmailVerification(db.Model):
    """A pending one-time code sent to an address. Only an HMAC of the code is stored."""

    __tablename__ = "email_verifications"

    email = db.Column(String(255), primary_key=True)
    purpose = db.Column(String(32), nullable=False)
    code_hash = db.Column(String(64), nullable=False)
    attempts = db.Column(Integer, nullable=False, default=0)
    created_at = db.Column(DateTime(timezone=True), nullable=False, default=utcnow)
    expires_at = db.Column(DateTime(timezone=True), nullable=False)
