# -*- coding: utf-8 -*-
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


def hash_password(password: str) -> str:
    """Store salt + hash for verification."""
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    derived = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(salt + derived).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        stored = base64.urlsafe_b64decode(password_hash.encode())
        salt = stored[:16]
        expected = stored[16:]
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        derived = kdf.derive(password.encode())
        return derived == expected
    except Exception:
        return False
