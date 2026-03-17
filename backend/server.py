"""
server.py  –  StudyPrep AI  |  Flask + MySQL + JWT Auth
Run:  python server.py

Before first run, apply the schema:
    mysql -u root -p < schema.sql

Endpoints
─────────
  POST /register   – create account  → access_token + refresh_token
  POST /login      – sign in         → access_token + refresh_token
  POST /refresh    – silent refresh  → new access_token + new refresh_token
  POST /logout     – revoke session  (pass all_devices=true for all sessions)
  GET  /me         – protected, returns current user profile
  GET  /health     – status check
"""

import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from flask import Flask, jsonify
from jwt_auth.core import JWTAuth
from jwt_auth.utils import JWTUtil

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/register", methods=["OPTIONS"])
@app.route("/login",    methods=["OPTIONS"])
@app.route("/refresh",  methods=["OPTIONS"])
@app.route("/logout",   methods=["OPTIONS"])
@app.route("/me",       methods=["OPTIONS"])
def handle_preflight():
    return "", 204

# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/register")
def register():
    return JWTAuth.register()

@app.post("/login")
def login():
    return JWTAuth.login()

@app.post("/refresh")
def refresh():
    return JWTAuth.refresh()

@app.post("/logout")
def logout():
    return JWTAuth.logout()

@app.get("/me")
@JWTUtil.require_auth
def me():
    return JWTAuth.me()

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "StudyPrep AI Auth"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
