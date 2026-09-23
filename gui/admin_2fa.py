import pyotp

from database import (
    get_admin_account,
    update_admin_totp_secret,
    append_admin_audit,
)

from utils.secret_storage import (
    encrypt_secret,
    decrypt_secret,
)


# =========================================================
# TOTP CONFIGURATION
# =========================================================

TOTP_INTERVAL = 30
TOTP_DIGITS = 6
TOTP_ISSUER = "VeriVote"

ENCRYPTED_PREFIX = "enc:v1:"


# =========================================================
# LOAD AND DECRYPT TOTP SECRET
# =========================================================

def _load_totp_secret(username):
    """
    Load the Central administrator's TOTP secret.

    The database may contain either:
        1. an encrypted secret, or
        2. an older plaintext secret.

    The function always returns ONLY the decrypted Base32
    secret to the caller.
    """

    account = get_admin_account(username)

    if account is None:
        raise ValueError(
            "Administrator account not found."
        )

    stored_value = account.get(
        "totp_secret",
        ""
    )

    if not stored_value:
        return None

    # -----------------------------------------------------
    # ENCRYPTED SECRET
    # -----------------------------------------------------

    if stored_value.startswith(
        ENCRYPTED_PREFIX
    ):

        secret = decrypt_secret(
            stored_value
        )

    # -----------------------------------------------------
    # OLD PLAINTEXT SECRET
    # -----------------------------------------------------

    else:

        secret = stored_value.strip()

        # Migrate plaintext to encrypted storage.
        encrypted_value = encrypt_secret(
            secret
        )

        update_admin_totp_secret(
            username,
            encrypted_value
        )

        append_admin_audit(
            username,
            account["role"],
            "2FA_MIGRATION",
            "Existing TOTP secret migrated to encrypted storage.",
            "SUCCESS",
        )

    # -----------------------------------------------------
    # NORMALIZE
    # -----------------------------------------------------

    secret = secret.strip().upper()

    # -----------------------------------------------------
    # VALIDATE BASE32 SECRET
    # -----------------------------------------------------

    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    )

    if (
        len(secret) != 32
        or bool(set(secret) - allowed)
    ):

        raise ValueError(
            "Stored Central TOTP secret is invalid."
        )

    return secret


# =========================================================
# CREATE TOTP SECRET
# =========================================================

def create_totp_secret(username):

    account = get_admin_account(
        username
    )

    if account is None:
        raise ValueError(
            "Administrator account not found."
        )

    # -----------------------------------------------------
    # USE EXISTING SECRET
    # -----------------------------------------------------

    existing_secret = _load_totp_secret(
        username
    )

    if existing_secret:
        return existing_secret

    # -----------------------------------------------------
    # GENERATE NEW SECRET
    # -----------------------------------------------------

    secret = pyotp.random_base32()

    encrypted_value = encrypt_secret(
        secret
    )

    update_admin_totp_secret(
        username,
        encrypted_value
    )

    append_admin_audit(
        username,
        account["role"],
        "2FA_SETUP",
        "Central TOTP secret generated and encrypted.",
        "SUCCESS",
    )

    return secret


# =========================================================
# GET TOTP OBJECT
# =========================================================

def get_totp(username):

    # Load the decrypted TOTP secret.
    secret = _load_totp_secret(
        username
    )

    if secret is None:
        return None

    return pyotp.TOTP(
        secret,
        interval=TOTP_INTERVAL,
        digits=TOTP_DIGITS,
    )


# =========================================================
# GET CURRENT OTP
# =========================================================

def get_current_otp(username):

    totp = get_totp(
        username
    )

    if totp is None:
        return None

    return totp.now()


# =========================================================
# VERIFY OTP
# =========================================================

def verify_totp(
    username,
    otp
):

    account = get_admin_account(
        username
    )

    if account is None:

        return (
            False,
            "Administrator account not found."
        )

    try:

        totp = get_totp(
            username
        )

    except Exception:

        append_admin_audit(
            username,
            account["role"],
            "2FA",
            "Central TOTP secret could not be loaded securely.",
            "BLOCKED",
        )

        return (
            False,
            "Central 2FA configuration is invalid."
        )

    if totp is None:

        append_admin_audit(
            username,
            account["role"],
            "2FA",
            "TOTP verification attempted before setup.",
            "BLOCKED",
        )

        return (
            False,
            "Central 2FA has not been configured."
        )

    otp = str(
        otp
    ).strip()

    # -----------------------------------------------------
    # STRICT SIX-DIGIT VALIDATION
    # -----------------------------------------------------

    if (
        len(otp) != TOTP_DIGITS
        or not otp.isdigit()
    ):

        append_admin_audit(
            username,
            account["role"],
            "2FA",
            "Invalid OTP format.",
            "FAILED",
        )

        return (
            False,
            "Enter the 6-digit authenticator code."
        )

    # -----------------------------------------------------
    # VERIFY CURRENT OTP WINDOW
    # -----------------------------------------------------

    try:

        valid = totp.verify(
            otp,
            valid_window=0
        )

    except Exception:

        valid = False

    if not valid:

        append_admin_audit(
            username,
            account["role"],
            "2FA",
            "TOTP verification failed.",
            "FAILED",
        )

        return (
            False,
            "Invalid or expired OTP."
        )

    append_admin_audit(
        username,
        account["role"],
        "2FA",
        "TOTP verification successful.",
        "SUCCESS",
    )

    return (
        True,
        "2FA verification successful."
    )


# =========================================================
# AUTHENTICATOR PROVISIONING URI
# =========================================================

def get_provisioning_uri(username):

    secret = _load_totp_secret(
        username
    )

    if secret is None:

        secret = create_totp_secret(
            username
        )

    totp = pyotp.TOTP(
        secret,
        interval=TOTP_INTERVAL,
        digits=TOTP_DIGITS,
    )

    return totp.provisioning_uri(
        name=username,
        issuer_name=TOTP_ISSUER,
    )