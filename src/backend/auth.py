"""Login, password hashing and JWT checks. The role is never taken from the client:
it is looked up in the database for the user named in a signed token."""
import hashlib
import hmac
import logging
import os
import secrets
import time
from collections import defaultdict

import jwt
from fastapi import Depends, Header, HTTPException

import db

SECRET = os.environ.get("FINGUARD_SECRET", "dev-only-change-me")
DEMO_PASSWORD = os.environ.get("FINGUARD_DEMO_PASSWORD", "finguard-demo")
TOKEN_HOURS, ITERATIONS = 8, 200_000
MAX_FAILS, WINDOW = 5, 60  # 5 wrong passwords per username per minute
FAILS: dict[str, list[float]] = defaultdict(list)

if SECRET == "dev-only-change-me":
    logging.warning("FINGUARD_SECRET is not set. Using an insecure development key. Set it before deploying.")


def hash_password(password: str, salt: str | None = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return salt, digest


def verify_password(password: str, salt: str, expected: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt)[1], expected)


def authenticate(username: str, password: str) -> dict:
    now = time.time()
    FAILS[username] = [t for t in FAILS[username] if now - t < WINDOW]
    if len(FAILS[username]) >= MAX_FAILS:
        raise HTTPException(429, "Too many failed attempts. Try again in a minute.")
    user = db.get_user(username)
    # Hash even for unknown users so response time does not reveal which usernames exist.
    ok = verify_password(password, user["salt"], user["pw_hash"]) if user else (hash_password(password) and False)
    if not ok:
        FAILS[username].append(now)
        raise HTTPException(401, "Wrong username or password")
    return user


def make_token(user: dict) -> str:
    return jwt.encode({"sub": user["username"], "exp": int(time.time()) + TOKEN_HOURS * 3600}, SECRET, algorithm="HS256")


def current_user(authorization: str | None = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in required")
    try:
        data = jwt.decode(authorization[7:], SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired or invalid. Sign in again.")
    user = db.get_user(data.get("sub", ""))
    if user is None:
        raise HTTPException(401, "Account no longer exists")
    return user


def require(*roles: str):
    def dep(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, "This role is not allowed to do that")
        return user
    return dep
