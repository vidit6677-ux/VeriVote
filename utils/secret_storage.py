import os

from cryptography.fernet import Fernet, InvalidToken


# =========================================================
# CONFIGURATION
# =========================================================

ENV_KEY_NAME = "VERIVOTE_CENTRAL_TOTP_KEY"

ENCRYPTED_PREFIX = "enc:v1:"


# =========================================================
# GET ENCRYPTION KEY
# =========================================================

def _get_fernet():
    """
    Return a Fernet encryption object using the key stored
    outside the database and outside the source code.
    """

    key = os.getenv(
        ENV_KEY_NAME
    )

    if not key:

        raise RuntimeError(
            f"{ENV_KEY_NAME} is not configured."
        )

    try:

        return Fernet(
            key.encode("utf-8")
        )

    except Exception as error:

        raise RuntimeError(
            "Central TOTP encryption key is invalid."
        ) from error


# =========================================================
# ENCRYPT SECRET
# =========================================================

def encrypt_secret(secret):

    if not secret:

        raise ValueError(
            "Cannot encrypt an empty secret."
        )

    # Prevent accidental double-encryption.
    if secret.startswith(
        ENCRYPTED_PREFIX
    ):

        return secret

    fernet = _get_fernet()

    encrypted = fernet.encrypt(
        secret.encode("utf-8")
    ).decode("utf-8")

    return (
        ENCRYPTED_PREFIX
        + encrypted
    )


# =========================================================
# DECRYPT SECRET
# =========================================================

def decrypt_secret(value):

    if not value:

        return ""

    # Already plaintext.
    #
    # This is intentionally supported so that our existing
    # demo TOTP secret can be migrated without changing the
    # authenticator configuration.
    if not value.startswith(
        ENCRYPTED_PREFIX
    ):

        return value

    encrypted = value[
        len(ENCRYPTED_PREFIX):
    ]

    fernet = _get_fernet()

    try:

        return fernet.decrypt(
            encrypted.encode("utf-8")
        ).decode("utf-8")

    except InvalidToken as error:

        raise RuntimeError(
            "Central TOTP secret could not be decrypted."
        ) from error