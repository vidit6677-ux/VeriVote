"""Cryptographic primitives used by integrity and checkpoint services."""

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature


def sha256_hex(*parts: object) -> str:
    """Hash length-delimited fields to avoid ambiguous concatenation."""
    digest = hashlib.sha256()
    for part in parts:
        encoded = str(part).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def generate_ed25519_keypair() -> tuple[str, str]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    private_b64 = base64.b64encode(
        private.private_bytes_raw()
    ).decode("ascii")
    public_b64 = base64.b64encode(
        public.public_bytes_raw()
    ).decode("ascii")
    return private_b64, public_b64


def _configured_keys(level: str) -> tuple[str | None, str | None]:
    prefix = f"VERIVOTE_{level.upper()}_ED25519_"
    return os.getenv(prefix + "PRIVATE_KEY"), os.getenv(prefix + "PUBLIC_KEY")


def sign_checkpoint(level: str, message: str, fallback_secret: str) -> str:
    private_b64, public_b64 = _configured_keys(level)
    if private_b64 and public_b64:
        private = Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(private_b64)
        )
        signature = private.sign(message.encode("utf-8"))
        return "ed25519:" + base64.b64encode(signature).decode("ascii")

    return hmac.new(
        fallback_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_checkpoint(level: str, message: str, signature: str, fallback_secret: str) -> bool:
    if signature.startswith("ed25519:"):
        _, encoded_signature = signature.split(":", 1)
        _, public_b64 = _configured_keys(level)
        if not public_b64:
            return False
        try:
            public = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_b64))
            public.verify(
                base64.b64decode(encoded_signature),
                message.encode("utf-8"),
            )
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False

    expected = hmac.new(
        fallback_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
