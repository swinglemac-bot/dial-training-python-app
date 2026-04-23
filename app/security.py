from __future__ import annotations

import hashlib
import hmac
import secrets


def create_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), n=2**14, r=8, p=1)
    return f"{salt}:{digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, existing_hex = stored.split(":", 1)
    except ValueError:
        return False
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), n=2**14, r=8, p=1)
    return hmac.compare_digest(digest.hex(), existing_hex)
