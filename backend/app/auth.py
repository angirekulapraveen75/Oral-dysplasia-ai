"""Authentication utilities — JWT tokens, password hashing, patient-data encryption."""

import datetime
import hashlib
import binascii
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import settings

# ── AES-256 Fernet for patient PII ──────────────────────────────────
# Generate a proper key on first run if the default is still set.
try:
    _fernet = Fernet(settings.PATIENT_ENCRYPTION_KEY.encode())
except Exception:
    # Auto-generate and warn
    _key = Fernet.generate_key()
    _fernet = Fernet(_key)
    print(f"[WARN] Invalid PATIENT_ENCRYPTION_KEY. Auto-generated: {_key.decode()}")


def encrypt_pii(plain: str) -> str:
    if not plain:
        return ""
    return _fernet.encrypt(plain.encode()).decode()


def decrypt_pii(cipher: str) -> str:
    if not cipher:
        return ""
    try:
        return _fernet.decrypt(cipher.encode()).decode()
    except Exception:
        return "[decryption-error]"


# ── Password hashing (PBKDF2-SHA256, 100k rounds) ──────────────────
def hash_password(password: str) -> str:
    salt = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest().encode()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return binascii.hexlify(hashed).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ── JWT ─────────────────────────────────────────────────────────────
def create_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.datetime.utcnow() + (
        expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
