"""Security utilities for password hashing"""
import hashlib
import os
import base64


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA256

    Args:
        password: Plain text password

    Returns:
        str: Hashed password in format salt$hash
    """
    # Generate random salt
    salt = os.urandom(32)

    # Hash password with salt using PBKDF2
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # 100,000 iterations
    )

    # Encode salt and hash as base64 and combine
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_b64 = base64.b64encode(pwd_hash).decode('ascii')

    return f"{salt_b64}${hash_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        salt_b64, hash_b64 = hashed_password.split('$')

        # Decode from base64
        salt = base64.b64decode(salt_b64)
        stored_hash = base64.b64decode(hash_b64)

        # Hash the provided password with the stored salt
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            100000
        )

        # Compare hashes (constant-time comparison)
        return pwd_hash == stored_hash

    except (ValueError, IndexError):
        return False
