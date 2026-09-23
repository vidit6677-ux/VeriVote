import os


# =========================================================
# APPLICATION
# =========================================================

APP_NAME = "VeriVote"
APP_VERSION = "2.0.0"


# =========================================================
# DATABASE
# =========================================================

# Keep the database beside main.py so the project uses
# one consistent database file.
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "verivote.db"
)


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