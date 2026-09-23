"""
One-time Central administrator TOTP enrollment.

Run this only when setting up or re-enrolling the Central
administrator's authenticator.

The TOTP secret is generated once and stored in the database.

IMPORTANT:
The secret is intentionally displayed during this one-time
enrollment step so it can be entered into an authenticator app.

It must NOT be displayed during normal Central login.
"""

import pyotp

from database import (
    get_admin_account,
    initialize_database,
    update_admin_totp_secret,
    append_admin_audit,
)


USERNAME = "central01"
ISSUER = "VeriVote"


def setup_central_2fa():

    # =====================================================
    # INITIALIZE DATABASE
    # =====================================================

    initialize_database()

    # =====================================================
    # GET CENTRAL ACCOUNT
    # =====================================================

    account = get_admin_account(
        USERNAME
    )

    if account is None:

        raise RuntimeError(
            "Central administrator account not found."
        )

    if account["role"] != "CENTRAL":

        raise RuntimeError(
            "The selected account is not a CENTRAL account."
        )

    # =====================================================
    # CHECK EXISTING SECRET
    # =====================================================

    if account["totp_secret"]:

        print()
        print("=" * 60)
        print("CENTRAL 2FA IS ALREADY CONFIGURED")
        print("=" * 60)
        print()
        print(
            "For security, the existing secret is not displayed."
        )
        print()
        print(
            "To re-enroll the authenticator, remove the old"
        )
        print(
            "authenticator entry and explicitly run this utility"
        )
        print(
            "with the re-enrollment option."
        )
        print()

        return

    # =====================================================
    # GENERATE SECRET
    # =====================================================

    secret = pyotp.random_base32()

    # =====================================================
    # STORE SECRET
    # =====================================================

    update_admin_totp_secret(
        USERNAME,
        secret
    )

    # =====================================================
    # CREATE TOTP URI
    # =====================================================

    totp = pyotp.TOTP(
        secret,
        interval=30,
        digits=6
    )

    provisioning_uri = (
        totp.provisioning_uri(
            name=USERNAME,
            issuer_name=ISSUER
        )
    )

    # =====================================================
    # AUDIT EVENT
    # =====================================================

    append_admin_audit(
        USERNAME,
        "CENTRAL",
        "2FA_SETUP",
        "Central TOTP authenticator enrolled.",
        "SUCCESS",
    )

    # =====================================================
    # ONE-TIME DISPLAY
    # =====================================================

    print()
    print("=" * 60)
    print("CENTRAL 2FA ENROLLMENT")
    print("=" * 60)
    print()

    print(
        "Enter this setup key into your authenticator app:"
    )

    print()

    print(
        secret
    )

    print()

    print(
        "The key above is shown ONLY during this setup step."
    )

    print(
        "Do not share it or store it in screenshots."
    )

    print()

    print(
        "Issuer:",
        ISSUER
    )

    print(
        "Account:",
        USERNAME
    )

    print()

    print(
        "Provisioning URI:"
    )

    print(
        provisioning_uri
    )

    print()

    print(
        "After adding it to the authenticator app,"
    )

    print(
        "verify that the generated 6-digit OTP works"
    )

    print(
        "from the Central login screen."
    )

    print()

    print("=" * 60)
    print("ENROLLMENT COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    setup_central_2fa()