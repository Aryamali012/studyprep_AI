"""
jwt_auth/utils.py
JWT token creation, verification, refresh token helpers, and route decorator.

Token strategy
──────────────
  Access token  – short-lived JWT (15 min).  Sent in Authorization header.
  Refresh token – opaque 64-byte random hex (30 days).  Stored as SHA-256
                  hash in DB.  Rotated on every /refresh call (old one is
                  revoked, new one issued).  If a revoked token is reused it
                  means theft → all tokens for that user are revoked.
"""

import jwt
import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g


# ── Config ────────────────────────────────────────────────────────────────────
JWT_SECRET            = os.getenv("JWT_SECRET",            "change_me_in_production")
JWT_ALGORITHM         = "HS256"
ACCESS_TOKEN_MINUTES  = int(os.getenv("ACCESS_TOKEN_MINUTES",  "15"))
REFRESH_TOKEN_DAYS    = int(os.getenv("REFRESH_TOKEN_DAYS",    "30"))


class JWTUtil:

    # ── Password helpers ───────────────────────────────────────────────────────

    @staticmethod
    def hash_password(plain: str) -> str:
        """PBKDF2-HMAC-SHA256, 260k iterations, random 256-bit salt."""
        salt = secrets.token_hex(32)
        dk   = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), iterations=260_000)
        return f"{salt}${dk.hex()}"

    @staticmethod
    def verify_password(plain: str, stored: str) -> bool:
        try:
            salt, dk_hex = stored.split("$", 1)
        except ValueError:
            return False
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), iterations=260_000)
        return secrets.compare_digest(dk.hex(), dk_hex)

    # ── Access token (JWT) ─────────────────────────────────────────────────────

    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """Short-lived JWT (ACCESS_TOKEN_MINUTES, default 15 min)."""
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub":   user_id,
            "email": email,
            "type":  "access",
            "iat":   now,
            "exp":   now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """
        Decode and verify an access JWT.
        Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
        """
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Not an access token.")
        return payload

    # ── Refresh token (opaque) ─────────────────────────────────────────────────

    @staticmethod
    def generate_refresh_token() -> tuple[str, str, datetime]:
        """
        Returns (raw_token, token_hash, expires_at).
        raw_token  → sent to the client, never stored in DB.
        token_hash → stored in DB for safe comparison.
        """
        raw        = secrets.token_hex(64)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
        return raw, token_hash, expires_at

    @staticmethod
    def hash_refresh_token(raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Route decorator ────────────────────────────────────────────────────────

    @staticmethod
    def require_auth(f):
        """
        Protect an endpoint with a short-lived access JWT.
        Expects:  Authorization: Bearer <access_token>
        Sets g.user_id and g.email for the route handler.
        Returns 401 with {"code": "TOKEN_EXPIRED"} when expired so the
        frontend knows to attempt a silent refresh.
        """
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Missing Authorization header.", "code": "NO_TOKEN"}), 401
            token = auth[len("Bearer "):]
            try:
                payload   = JWTUtil.decode_access_token(token)
                g.user_id = payload["sub"]
                g.email   = payload["email"]
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Access token expired.", "code": "TOKEN_EXPIRED"}), 401
            except jwt.InvalidTokenError as exc:
                return jsonify({"error": f"Invalid token: {exc}", "code": "INVALID_TOKEN"}), 401
            return f(*args, **kwargs)
        return wrapper
