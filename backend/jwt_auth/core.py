"""
jwt_auth/core.py
Business logic for /register, /login, /refresh, /logout, /me endpoints.

Refresh token flow
──────────────────
  Login    → issue access_token (15 min) + refresh_token (30 days, stored in DB)
  /refresh → verify refresh_token against DB hash
             → revoke old token row
             → issue new access_token + new refresh_token  (rotation)
             → if a revoked token arrives → nuke ALL tokens for that user (theft detected)
  /logout  → revoke the supplied refresh_token (or all tokens if requested)
"""

import uuid
from datetime import datetime, timezone
from flask import request, jsonify, g

from server_db.connection import get_connection
from jwt_auth.utils import JWTUtil


def _issue_token_pair(user_id: str, email: str) -> tuple[str, str]:
    """
    Create an access token + refresh token, persist the refresh token hash,
    and return (access_token, raw_refresh_token).
    """
    access_token               = JWTUtil.create_access_token(user_id, email)
    raw_rt, rt_hash, rt_expiry = JWTUtil.generate_refresh_token()

    token_id = str(uuid.uuid4())
    conn     = get_connection()
    with conn:
        conn.execute(
            """INSERT INTO refresh_tokens (token_id, user_id, token_hash, expires_at)
               VALUES (?, ?, ?, ?)""",
            (token_id, user_id, rt_hash, rt_expiry.isoformat()),
        )
    conn.close()
    return access_token, raw_rt


class JWTAuth:

    # ─── POST /register ───────────────────────────────────────────────────────
    @staticmethod
    def register():
        data      = request.get_json(silent=True) or {}
        full_name = (data.get("full_name") or "").strip()
        email     = (data.get("email")     or "").strip().lower()
        password  = (data.get("password")  or "")

        errors = []
        if not full_name:              errors.append("full_name is required.")
        if not email:                  errors.append("email is required.")
        if not password:               errors.append("password is required.")
        elif len(password) < 6:        errors.append("password must be at least 6 characters.")
        if errors:
            return jsonify({"error": " ".join(errors)}), 400

        user_id       = str(uuid.uuid4())
        password_hash = JWTUtil.hash_password(password)

        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (user_id, full_name, email, password_hash) VALUES (?,?,?,?)",
                    (user_id, full_name, email, password_hash),
                )
        except Exception as exc:
            if "UNIQUE" in str(exc):
                return jsonify({"error": "An account with this email already exists."}), 409
            return jsonify({"error": "Registration failed. Please try again."}), 500
        finally:
            conn.close()

        access_token, refresh_token = _issue_token_pair(user_id, email)
        return jsonify({
            "message":       "Account created successfully.",
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "user": {"user_id": user_id, "full_name": full_name, "email": email},
        }), 201

    # ─── POST /login ──────────────────────────────────────────────────────────
    @staticmethod
    def login():
        data     = request.get_json(silent=True) or {}
        email    = (data.get("email")    or "").strip().lower()
        password = (data.get("password") or "")

        if not email or not password:
            return jsonify({"error": "Email and password are required."}), 400

        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT user_id, full_name, email, password_hash FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        finally:
            conn.close()

        if row is None or not JWTUtil.verify_password(password, row["password_hash"]):
            return jsonify({"error": "Invalid email or password."}), 401

        access_token, refresh_token = _issue_token_pair(row["user_id"], row["email"])
        return jsonify({
            "message":       "Login successful.",
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "user": {
                "user_id":   row["user_id"],
                "full_name": row["full_name"],
                "email":     row["email"],
            },
        }), 200

    # ─── POST /refresh ────────────────────────────────────────────────────────
    @staticmethod
    def refresh():
        """
        Silently exchange a valid refresh token for a new token pair.
        The old refresh token is revoked immediately (rotation).
        If a previously-revoked token is presented, ALL tokens for the user
        are revoked (refresh token theft detection).
        """
        data    = request.get_json(silent=True) or {}
        raw_rt  = (data.get("refresh_token") or "").strip()

        if not raw_rt:
            return jsonify({"error": "refresh_token is required.", "code": "NO_REFRESH_TOKEN"}), 400

        rt_hash = JWTUtil.hash_refresh_token(raw_rt)
        conn    = get_connection()

        try:
            row = conn.execute(
                "SELECT token_id, user_id, expires_at, revoked FROM refresh_tokens WHERE token_hash = ?",
                (rt_hash,),
            ).fetchone()

            # ── Token not found in DB at all ──────────────────────────────────
            if row is None:
                return jsonify({"error": "Invalid refresh token.", "code": "INVALID_REFRESH_TOKEN"}), 401

            # ── Theft detection: token was already revoked ─────────────────────
            if row["revoked"]:
                with conn:
                    conn.execute(
                        "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?",
                        (row["user_id"],),
                    )
                return jsonify({
                    "error": "Refresh token already used. All sessions revoked. Please log in again.",
                    "code":  "REFRESH_TOKEN_REUSE",
                }), 401

            # ── Expiry check ───────────────────────────────────────────────────
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(tz=timezone.utc) > expires_at:
                with conn:
                    conn.execute(
                        "UPDATE refresh_tokens SET revoked = 1 WHERE token_id = ?",
                        (row["token_id"],),
                    )
                return jsonify({"error": "Refresh token expired. Please log in again.", "code": "REFRESH_TOKEN_EXPIRED"}), 401

            # ── Revoke old token ───────────────────────────────────────────────
            with conn:
                conn.execute(
                    "UPDATE refresh_tokens SET revoked = 1 WHERE token_id = ?",
                    (row["token_id"],),
                )

            user_id = row["user_id"]

            # Fetch user email
            user_row = conn.execute(
                "SELECT email FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if user_row is None:
                return jsonify({"error": "User not found.", "code": "USER_NOT_FOUND"}), 404

        finally:
            conn.close()

        # ── Issue new token pair (rotation) ────────────────────────────────────
        new_access, new_refresh = _issue_token_pair(user_id, user_row["email"])
        return jsonify({
            "access_token":  new_access,
            "refresh_token": new_refresh,
        }), 200

    # ─── POST /logout ─────────────────────────────────────────────────────────
    @staticmethod
    def logout():
        """
        Revoke the supplied refresh token.
        Pass  all_devices=true  to revoke every refresh token for the user.
        """
        data       = request.get_json(silent=True) or {}
        raw_rt     = (data.get("refresh_token") or "").strip()
        all_devices = data.get("all_devices", False)

        if not raw_rt:
            return jsonify({"error": "refresh_token is required."}), 400

        rt_hash = JWTUtil.hash_refresh_token(raw_rt)
        conn    = get_connection()
        try:
            row = conn.execute(
                "SELECT token_id, user_id FROM refresh_tokens WHERE token_hash = ?",
                (rt_hash,),
            ).fetchone()

            if row is None:
                return jsonify({"message": "Already logged out."}), 200

            with conn:
                if all_devices:
                    conn.execute(
                        "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?",
                        (row["user_id"],),
                    )
                else:
                    conn.execute(
                        "UPDATE refresh_tokens SET revoked = 1 WHERE token_id = ?",
                        (row["token_id"],),
                    )
        finally:
            conn.close()

        msg = "Logged out from all devices." if all_devices else "Logged out successfully."
        return jsonify({"message": msg}), 200

    # ─── GET /me  (protected) ─────────────────────────────────────────────────
    @staticmethod
    def me():
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT user_id, full_name, email, created_at FROM users WHERE user_id = ?",
                (g.user_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            return jsonify({"error": "User not found."}), 404

        return jsonify({"user": {
            "user_id":    row["user_id"],
            "full_name":  row["full_name"],
            "email":      row["email"],
            "created_at": row["created_at"],
        }}), 200

