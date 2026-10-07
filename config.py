import os
import sys


# =========================================================
# APPLICATION
# =========================================================

APP_NAME = "VeriVote"
APP_VERSION = "2.0.0"


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# Packaged Windows builds must keep databases outside the replaceable
# executable directory so upgrades do not reset voter/admin state.
if getattr(sys, "frozen", False):
    RUNTIME_DIR = os.path.join(
        os.getenv("APPDATA", BASE_DIR),
        "VeriVote",
    )
    os.makedirs(RUNTIME_DIR, exist_ok=True)
else:
    RUNTIME_DIR = BASE_DIR


# =========================================================
# DATABASE
# =========================================================
#
# PHASE 5:
# Keep DATABASE_PATH as the existing database location for
# backward compatibility while we build and migrate the
# four independent administrative databases.
#
# After migration, database.py will use the BOOTH database
# as the primary operational database.
# =========================================================

DATABASE_PATH = os.path.join(
    RUNTIME_DIR,
    "verivote.db"
)


# =========================================================
# FOUR INDEPENDENT DATABASE PATHS
# =========================================================

LEVEL_DATABASE_PATHS = {

    "BOOTH": os.path.join(
        RUNTIME_DIR,
        "booth.db"
    ),

    "ZONAL": os.path.join(
        RUNTIME_DIR,
        "zonal.db"
    ),

    "DEPUTY": os.path.join(
        RUNTIME_DIR,
        "deputy.db"
    ),

    "CENTRAL": os.path.join(
        RUNTIME_DIR,
        "central.db"
    ),
}


# =========================================================
# POLLING CENTRE
# =========================================================

DEMO_CENTRE_ID = "PC-001"

DEMO_CENTRE_NAME = (
    "VeriVote Demo Polling Centre"
)


# =========================================================
# FOUR-LEVEL ADMIN HIERARCHY
# =========================================================

ADMIN_LEVELS = (
    "BOOTH",
    "ZONAL",
    "DEPUTY",
    "CENTRAL",
)


ADMIN_LEVEL_LABELS = {

    "BOOTH":
        "Booth Officer",

    "ZONAL":
        "Zonal Officer",

    "DEPUTY":
        "Deputy Officer",

    "CENTRAL":
        "Central Administrator",
}


# =========================================================
# DEMO ADMINISTRATOR ACCOUNTS
# =========================================================
#
# These are ONLY for the college demonstration.
#
# admin_security.py converts the passwords into salted
# PBKDF2 hashes before storing them in SQLite.
#
# In a real deployment, credentials would be provisioned
# securely and would not be stored in source code.
# =========================================================

DEMO_ADMIN_ACCOUNTS = {

    "booth01": {
        "role": "BOOTH",
        "password": "Booth@2026",
        "face_identity": "",
    },

    "zonal01": {
        "role": "ZONAL",
        "password": "Zonal@2026",
        "face_identity": "",
    },

    "deputy01": {
        "role": "DEPUTY",
        "password": "Deputy@2026",
        "face_identity": "",
    },

    "central01": {
        "role": "CENTRAL",
        "password": "Central@2026!Secure",
        "face_identity": "central_admin",
    },
}


# =========================================================
# FOUR-LEVEL INTEGRITY SIGNING KEYS
# =========================================================
#
# Each administrative level has a separate signing secret.
#
# For the college prototype, environment variables may
# override the demo defaults.
#
# Production systems should use securely provisioned keys
# outside the application source and preferably hardware
# backed key storage / HSM infrastructure.
# =========================================================

LEVEL_SIGNING_SECRETS = {

    "BOOTH": os.getenv(
        "VERIVOTE_BOOTH_SIGNING_KEY",
        "demo-booth-signing-key-change-me",
    ),

    "ZONAL": os.getenv(
        "VERIVOTE_ZONAL_SIGNING_KEY",
        "demo-zonal-signing-key-change-me",
    ),

    "DEPUTY": os.getenv(
        "VERIVOTE_DEPUTY_SIGNING_KEY",
        "demo-deputy-signing-key-change-me",
    ),

    "CENTRAL": os.getenv(
        "VERIVOTE_CENTRAL_SIGNING_KEY",
        "demo-central-signing-key-change-me",
    ),
}


# =========================================================
# ADMIN SESSION SECURITY
# =========================================================

ADMIN_SESSION_TIMEOUT_SECONDS = (
    10 * 60
)


# Maximum consecutive failed password attempts before
# temporary lockout.
ADMIN_MAX_FAILED_ATTEMPTS = 5


# Temporary lockout duration.
ADMIN_LOCKOUT_SECONDS = (
    5 * 60
)


# =========================================================
# CENTRAL FACE IDENTITY
# =========================================================

CENTRAL_FACE_IDENTITY = (
    "central_admin"
)
