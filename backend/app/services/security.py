"""
Security Utilities for FinRAG.

Provides SHA256 secret hashing and timing-safe comparison
to prevent timing attacks on authentication/webhook verification.
"""

import hashlib
import hmac
import secrets
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def hash_secret_sha256(secret: str, salt: Optional[str] = None) -> str:
    """
    Hash a secret using SHA256 with an optional salt.

    Args:
        secret: The plaintext secret to hash.
        salt: Optional salt. If not provided, a random 16-byte salt is generated.

    Returns:
        A string in the format "salt$hash" for storage.
    """
    if not secret:
        raise ValueError("Secret cannot be empty")

    if salt is None:
        salt = secrets.token_hex(16)

    salted = f"{salt}{secret}".encode("utf-8")
    hashed = hashlib.sha256(salted).hexdigest()
    return f"{salt}${hashed}"


def verify_secret_sha256(secret: str, stored_hash: str) -> bool:
    """
    Verify a secret against a stored SHA256 hash using timing-safe comparison.

    Args:
        secret: The plaintext secret to verify.
        stored_hash: The stored hash in "salt$hash" format.

    Returns:
        True if the secret matches, False otherwise.
    """
    if not secret or not stored_hash:
        return False

    try:
        salt, expected_hash = stored_hash.split("$", 1)
    except ValueError:
        logger.warning("Invalid stored hash format — expected 'salt$hash'")
        return False

    salted = f"{salt}{secret}".encode("utf-8")
    computed_hash = hashlib.sha256(salted).hexdigest()

    # Timing-safe comparison to prevent timing attacks
    return hmac.compare_digest(computed_hash, expected_hash)


def timing_safe_compare(a: str, b: str) -> bool:
    """
    Perform a timing-safe string comparison.

    Uses hmac.compare_digest under the hood, which is constant-time
    and prevents timing attacks that could leak information about
    the expected value.

    Args:
        a: First string.
        b: Second string.

    Returns:
        True if strings are equal, False otherwise.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.

    Returns:
        A 64-character hex string suitable for use as an API key.
    """
    return secrets.token_hex(32)
