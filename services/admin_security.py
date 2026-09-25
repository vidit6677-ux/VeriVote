import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone

from config import (
    ADMIN_LEVELS,
    DEMO_ADMIN_ACCOUNTS,
    ADMIN_MAX_FAILED_ATTEMPTS,
    ADMIN_LOCKOUT_SECONDS,
)

from database import (
    append_admin_audit,
    create_admin_account,
    get_admin_account,
    update_admin_auth_state,
)


# =========================================================
# PASSWORD SECURITY
# =========================================================

PBKDF2_ITERATIONS = 310_000
SALT_BYTES = 16


def hash_password(password, salt_hex=None):
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    A new random salt is generated when salt_hex is not
    supplied.
    """

    if not password:
        raise ValueError("Password cannot be empty.")

    if salt_hex:

        salt = bytes.fromhex(
            salt_hex
        )

    else:

        salt = secrets.token_bytes(
            SALT_BYTES
        )

        salt_hex = salt.hex()

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return digest.hex(), salt_hex


def verify_password(
    password,
    stored_hash,
    stored_salt
):
    """
    Verify a password against its stored PBKDF2 hash.
    """

    calculated, _ = hash_password(
        password,
        stored_salt
    )

    return hmac.compare_digest(
        calculated,
        stored_hash
    )


# =========================================================
# DEMO ADMIN ACCOUNT SEEDING
# =========================================================

def seed_demo_admin_accounts():

    """
    Create the four demonstration administrator accounts
    on the first run.

    Passwords are converted into salted PBKDF2 hashes
    before being stored in the database.
    """

    for username, details in DEMO_ADMIN_ACCOUNTS.items():

        role = details["role"]

        if role not in ADMIN_LEVELS:

            raise ValueError(
                f"Unsupported admin role: {role}"
            )

        # -------------------------------------------------
        # DON'T RECREATE EXISTING ACCOUNT
        # -------------------------------------------------

        if get_admin_account(username) is not None:
            continue

        password_hash, password_salt = (
            hash_password(details["password"])
        )

        create_admin_account(
            username=username,
            role=role,
            password_hash=password_hash,
            password_salt=password_salt,
            face_identity=details.get(
                "face_identity",
                ""
            ),
        )


# =========================================================
# ADMIN AUTHENTICATION
# =========================================================

def authenticate_admin(
    username,
    password,
    selected_role
):

    username = username.strip()

    selected_role = (
        selected_role
        .strip()
        .upper()
    )

    account = get_admin_account(
        username
    )

    # -----------------------------------------------------
    # ACCOUNT NOT FOUND
    # -----------------------------------------------------

    if account is None:

        return (
            False,
            None,
            "Invalid administrator credentials."
        )

    now = time.time()

    # -----------------------------------------------------
    # CHECK ACTIVE STATUS
    # -----------------------------------------------------

    if not account["active"]:

        append_admin_audit(
            username,
            account["role"],
            "LOGIN",
            "Inactive administrator account used.",
            "BLOCKED",
        )

        return (
            False,
            None,
            "This administrator account is inactive."
        )

    # -----------------------------------------------------
    # CHECK ROLE
    # -----------------------------------------------------

    if account["role"] != selected_role:

        append_admin_audit(
            username,
            account["role"],
            "LOGIN",
            "Role mismatch during authentication.",
            "BLOCKED",
        )

        return (
            False,
            None,
            "Selected role does not match the administrator account."
        )

    # -----------------------------------------------------
    # CHECK LOCKOUT
    # -----------------------------------------------------

    if account["locked_until"] > now:

        remaining = int(
            account["locked_until"] - now
        ) + 1

        append_admin_audit(
            username,
            account["role"],
            "LOGIN",
            "Login attempted while account is locked.",
            "BLOCKED",
        )

        return (
            False,
            None,
            f"Account temporarily locked. "
            f"Try again in {remaining} seconds."
        )

    # -----------------------------------------------------
    # VERIFY PASSWORD
    # -----------------------------------------------------

    if not verify_password(
        password,
        account["password_hash"],
        account["password_salt"]
    ):

        failures = (
            account["failed_attempts"] + 1
        )

        locked_until = 0

        message = (
            "Invalid administrator credentials."
        )

        # -------------------------------------------------
        # LOCK ACCOUNT AFTER TOO MANY FAILURES
        # -------------------------------------------------

        if failures >= ADMIN_MAX_FAILED_ATTEMPTS:

            locked_until = (
                now + ADMIN_LOCKOUT_SECONDS
            )

            failures = 0

            message = (
                "Too many failed attempts. "
                "Administrator account is temporarily locked."
            )

        update_admin_auth_state(
            username,
            failed_attempts=failures,
            locked_until=locked_until,
        )

        append_admin_audit(
            username,
            account["role"],
            "LOGIN",
            "Password authentication failed.",
            "FAILED",
        )

        return (
            False,
            None,
            message
        )

    # -----------------------------------------------------
    # SUCCESSFUL LOGIN
    # -----------------------------------------------------

    update_admin_auth_state(
        username,
        failed_attempts=0,
        locked_until=0,
        last_login=(
            datetime.now(timezone.utc)
            .isoformat(
                timespec="seconds"
            )
            + "Z"
        ),
    )

    append_admin_audit(
        username,
        account["role"],
        "LOGIN",
        "Password authentication successful.",
        "SUCCESS",
    )

    return (
        True,
        get_admin_account(username),
        "Password authentication successful."
    )


# =========================================================
# CENTRAL FACE FAILURE
# =========================================================

def record_central_face_failure(account):

    failures = (
        account["failed_attempts"] + 1
    )

    locked_until = 0

    # Central gets an additional face-failure lockout.
    if failures >= 3:

        failures = 0

        locked_until = (
            time.time()
            + ADMIN_LOCKOUT_SECONDS
        )

    update_admin_auth_state(
        account["username"],
        failed_attempts=failures,
        locked_until=locked_until,
    )

    append_admin_audit(
        account["username"],
        account["role"],
        "FACE_AUTH",
        "Central face verification failed.",
        "FAILED",
    )


# =========================================================
# CENTRAL FACE SUCCESS
# =========================================================

def record_central_face_success(account):

    update_admin_auth_state(
        account["username"],
        failed_attempts=0,
        locked_until=0,
    )

    append_admin_audit(
        account["username"],
        account["role"],
        "FACE_AUTH",
        "Central face verification successful.",
        "SUCCESS",
    )
