from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.CREDENTIAL_ENCRYPTION_KEY
        if not key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY is not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string and return a base64-encoded ciphertext."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext and return the plaintext string."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
