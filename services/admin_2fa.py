import pyotp

from database import (
    get_admin_account,
    update_admin_totp_secret,
    append_admin_audit,
)


# =========================================================
# TOTP CONFIGURATION
# =========================================================

TOTP_INTERVAL = 30
TOTP_DIGITS = 6
TOTP_ISSUER = "VeriVote"


# =========================================================
# CREATE CENTRAL TOTP SECRET
# =========================================================

def create_totp_secret(username):

    account = get_admin_account(
        username
    )

    if account is None:
        raise ValueError(
            "Administrator account not found."
        )

    existing_secret = account.get(
        "totp_secret",
        ""
    )

    # -----------------------------------------------------
    # Reuse existing secret.
    # -----------------------------------------------------

    if existing_secret:

        return existing_secret

    # -----------------------------------------------------
    # Generate a cryptographically random TOTP secret.
    # -----------------------------------------------------

    secret = pyotp.random_base32()

    update_admin_totp_secret(
        username,
        secret
    )

    append_admin_audit(
        username,
        account["role"],
        "2FA_SETUP",
        "TOTP secret provisioned.",
        "SUCCESS",
    )

    return secret


# =========================================================
# CREATE TOTP OBJECT
# =========================================================

def get_totp(username):

    # Always load the decrypted TOTP secret.
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
# GENERATE CURRENT OTP
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

    totp = get_totp(
        username
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
    # Strict six-digit OTP check
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
    # Verify current TOTP.
    #
    # valid_window=0 means we accept only the current
    # 30-second TOTP window.
    # -----------------------------------------------------

    valid = totp.verify(
        otp,
        valid_window=0
    )

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
# AUTHENTICATOR APP PROVISIONING URI
# =========================================================

def get_provisioning_uri(username):

    account = get_admin_account(
        username
    )

    if account is None:

        raise ValueError(
            "Administrator account not found."
        )

    secret = account.get(
        "totp_secret",
        ""
    )

    if not secret:

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