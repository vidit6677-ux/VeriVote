import sqlite3
from datetime import datetime

from config import DATABASE_PATH


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_NAME = DATABASE_PATH


# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_NAME,
        timeout=10
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # =================================================
        # VOTERS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                constituency TEXT NOT NULL,
                eligible INTEGER NOT NULL DEFAULT 1,
                has_voted INTEGER NOT NULL DEFAULT 0,
                phone TEXT DEFAULT '',
                CHECK (eligible IN (0, 1)),
                CHECK (has_voted IN (0, 1))
            )
        """)

        # -------------------------------------------------
        # PHONE COLUMN MIGRATION
        # -------------------------------------------------

        cursor.execute("""
            PRAGMA table_info(voters)
        """)

        voter_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        if "phone" not in voter_columns:

            cursor.execute("""
                ALTER TABLE voters
                ADD COLUMN phone TEXT DEFAULT ''
            """)

        # =================================================
        # VOTES
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_identity TEXT NOT NULL,
                constituency TEXT NOT NULL,
                candidate TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                vote_hash TEXT NOT NULL
            )
        """)

        # =================================================
        # PHASE 4 — ONE VOTE PER VOTER
        # =================================================

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_votes_one_vote_per_voter
            ON votes(voter_identity)
        """)

        # =================================================
        # VOTER AUDIT
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voter_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_identity TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT DEFAULT ''
            )
        """)

        # =================================================
        # ADMIN ACCOUNTS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                face_identity TEXT DEFAULT '',
                totp_secret TEXT DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until REAL NOT NULL DEFAULT 0,
                last_login TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                CHECK (active IN (0, 1)),
                CHECK (failed_attempts >= 0)
            )
        """)

        # -------------------------------------------------
        # ADMIN TOTP MIGRATION
        # -------------------------------------------------
        #
        # Existing databases may have admin_accounts without
        # the totp_secret column.
        #
        # -------------------------------------------------

        cursor.execute("""
            PRAGMA table_info(admin_accounts)
        """)

        admin_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        if "totp_secret" not in admin_columns:

            cursor.execute("""
                ALTER TABLE admin_accounts
                ADD COLUMN totp_secret TEXT DEFAULT ''
            """)

        # =================================================
        # ADMIN AUDIT LOG
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT DEFAULT '',
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # =================================================
        # FOUR-LEVEL INTEGRITY CHECKPOINTS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrity_checkpoints (
                checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL UNIQUE,
                last_vote_id INTEGER NOT NULL DEFAULT 0,
                ledger_hash TEXT NOT NULL DEFAULT 'GENESIS',
                previous_checkpoint_hash TEXT NOT NULL DEFAULT 'GENESIS',
                checkpoint_hash TEXT NOT NULL DEFAULT '',
                signature TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            )
        """)

        # =================================================
        # SECURITY EVENTS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_level TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0,
                CHECK (acknowledged IN (0, 1))
            )
        """)

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# VOTER FUNCTIONS
# =========================================================

def add_demo_voter(
    identity,
    name,
    constituency,
    phone
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT OR IGNORE INTO voters (
                identity,
                name,
                constituency,
                eligible,
                has_voted,
                phone
            )
            VALUES (?, ?, ?, 1, 0, ?)
        """, (
            identity,
            name,
            constituency,
            phone
        ))

        cursor.execute("""
            UPDATE voters
            SET
                name = ?,
                constituency = ?,
                phone = ?
            WHERE identity = ?
        """, (
            name,
            constituency,
            phone,
            identity
        ))

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


def get_voter(identity):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                identity,
                name,
                constituency,
                eligible,
                has_voted,
                phone
            FROM voters
            WHERE identity = ?
        """, (
            identity,
        ))

        row = cursor.fetchone()

    finally:

        connection.close()

    if row is None:
        return None

    return {
        "identity": row[0],
        "name": row[1],
        "constituency": row[2],
        "eligible": bool(row[3]),
        "has_voted": bool(row[4]),
        "phone": row[5] or ""
    }


def get_all_voters():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                identity,
                name,
                constituency,
                eligible,
                has_voted,
                phone
            FROM voters
            ORDER BY name
        """)

        voters = cursor.fetchall()

    finally:

        connection.close()

    return voters


# =========================================================
# MARK VOTER AS VOTED
# =========================================================

def mark_voted(
    identity,
    cursor=None
):

    own_connection = cursor is None

    if own_connection:

        connection = get_connection()
        cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE voters
            SET has_voted = 1
            WHERE identity = ?
              AND has_voted = 0
        """, (
            identity,
        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Voter could not be marked as voted."
            )

        cursor.execute("""
            INSERT INTO voter_audit (
                voter_identity,
                action,
                timestamp,
                details
            )
            VALUES (?, ?, ?, ?)
        """, (
            identity,
            "VOTE_RECORDED",
            datetime.now().isoformat(),
            "Voter marked as voted."
        ))

        if own_connection:
            connection.commit()

    except Exception:

        if own_connection:
            connection.rollback()

        raise

    finally:

        if own_connection:
            connection.close()


# =========================================================
# VOTE FUNCTIONS
# =========================================================

def save_vote(
    voter_identity,
    constituency,
    candidate,
    timestamp,
    previous_hash,
    vote_hash,
    cursor=None
):

    own_connection = cursor is None

    if own_connection:

        connection = get_connection()
        cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO votes (
                voter_identity,
                constituency,
                candidate,
                timestamp,
                previous_hash,
                vote_hash
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            voter_identity,
            constituency,
            candidate,
            timestamp,
            previous_hash,
            vote_hash
        ))

        vote_id = cursor.lastrowid

        if own_connection:
            connection.commit()

        return vote_id

    except Exception:

        if own_connection:
            connection.rollback()

        raise

    finally:

        if own_connection:
            connection.close()


def get_vote_count():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM votes
        """)

        count = cursor.fetchone()[0]

    finally:

        connection.close()

    return count


def get_all_votes():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                vote_id,
                voter_identity,
                constituency,
                candidate,
                timestamp,
                previous_hash,
                vote_hash
            FROM votes
            ORDER BY vote_id ASC
        """)

        votes = cursor.fetchall()

    finally:

        connection.close()

    return votes


# =========================================================
# ADMIN ACCOUNT FUNCTIONS
# =========================================================

def create_admin_account(
    username,
    role,
    password_hash,
    password_salt,
    face_identity=""
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO admin_accounts (
                username,
                role,
                password_hash,
                password_salt,
                face_identity,
                totp_secret,
                active,
                failed_attempts,
                locked_until,
                last_login,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, '', 1, 0, 0, '', ?)
        """, (
            username,
            role,
            password_hash,
            password_salt,
            face_identity,
            datetime.now().isoformat()
        ))

        connection.commit()

    except sqlite3.IntegrityError:

        connection.rollback()

        return False

    finally:

        connection.close()

    return True


def get_admin_account(username):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                username,
                role,
                password_hash,
                password_salt,
                face_identity,
                totp_secret,
                active,
                failed_attempts,
                locked_until,
                last_login,
                created_at
            FROM admin_accounts
            WHERE username = ?
        """, (
            username,
        ))

        row = cursor.fetchone()

    finally:

        connection.close()

    if row is None:
        return None

    return {
        "username": row[0],
        "role": row[1],
        "password_hash": row[2],
        "password_salt": row[3],
        "face_identity": row[4] or "",
        "totp_secret": row[5] or "",
        "active": bool(row[6]),
        "failed_attempts": row[7],
        "locked_until": row[8],
        "last_login": row[9] or "",
        "created_at": row[10]
    }


def update_admin_auth_state(
    username,
    failed_attempts=None,
    locked_until=None,
    last_login=None
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        updates = []
        values = []

        if failed_attempts is not None:

            updates.append(
                "failed_attempts = ?"
            )

            values.append(
                failed_attempts
            )

        if locked_until is not None:

            updates.append(
                "locked_until = ?"
            )

            values.append(
                locked_until
            )

        if last_login is not None:

            updates.append(
                "last_login = ?"
            )

            values.append(
                last_login
            )

        if not updates:
            return

        values.append(
            username
        )

        query = f"""
            UPDATE admin_accounts
            SET {", ".join(updates)}
            WHERE username = ?
        """

        cursor.execute(
            query,
            tuple(values)
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# ADMIN TOTP
# =========================================================

def update_admin_totp_secret(
    username,
    totp_secret
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE admin_accounts
            SET totp_secret = ?
            WHERE username = ?
        """, (
            totp_secret,
            username
        ))

        if cursor.rowcount != 1:

            raise ValueError(
                "Administrator account not found."
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# ADMIN AUDIT LOG
# =========================================================

def append_admin_audit(
    username,
    role,
    action,
    details,
    status
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO admin_audit (
                username,
                role,
                action,
                details,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            username,
            role,
            action,
            details,
            status,
            datetime.now().isoformat()
        ))

        connection.commit()

    finally:

        connection.close()


def get_admin_audit_logs(
    limit=100
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                audit_id,
                username,
                role,
                action,
                details,
                status,
                timestamp
            FROM admin_audit
            ORDER BY audit_id DESC
            LIMIT ?
        """, (
            limit,
        ))

        logs = cursor.fetchall()

    finally:

        connection.close()

    return logs


# =========================================================
# SECURITY EVENTS
# =========================================================

def add_security_event(
    source_level,
    event_type,
    severity,
    details
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO security_events (
                source_level,
                event_type,
                severity,
                details,
                timestamp,
                acknowledged
            )
            VALUES (?, ?, ?, ?, ?, 0)
        """, (
            source_level,
            event_type,
            severity,
            details,
            datetime.now().isoformat()
        ))

        connection.commit()

    finally:

        connection.close()


def get_security_events(
    limit=100
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                event_id,
                source_level,
                event_type,
                severity,
                details,
                timestamp,
                acknowledged
            FROM security_events
            ORDER BY event_id DESC
            LIMIT ?
        """, (
            limit,
        ))

        events = cursor.fetchall()

    finally:

        connection.close()

    return events


# =========================================================
# INTEGRITY CHECKPOINTS
# =========================================================

def get_checkpoint(level):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                checkpoint_id,
                level,
                last_vote_id,
                ledger_hash,
                previous_checkpoint_hash,
                checkpoint_hash,
                signature,
                timestamp
            FROM integrity_checkpoints
            WHERE level = ?
        """, (
            level,
        ))

        row = cursor.fetchone()

    finally:

        connection.close()

    if row is None:
        return None

    return {
        "checkpoint_id": row[0],
        "level": row[1],
        "last_vote_id": row[2],
        "ledger_hash": row[3],
        "previous_checkpoint_hash": row[4],
        "checkpoint_hash": row[5],
        "signature": row[6] or "",
        "timestamp": row[7]
    }


def save_checkpoint(
    level,
    last_vote_id,
    ledger_hash,
    previous_checkpoint_hash,
    checkpoint_hash,
    signature="",
    timestamp=None
):

    if timestamp is None:

        timestamp = datetime.now().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO integrity_checkpoints (
                level,
                last_vote_id,
                ledger_hash,
                previous_checkpoint_hash,
                checkpoint_hash,
                signature,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(level)
            DO UPDATE SET
                last_vote_id = excluded.last_vote_id,
                ledger_hash = excluded.ledger_hash,
                previous_checkpoint_hash =
                    excluded.previous_checkpoint_hash,
                checkpoint_hash =
                    excluded.checkpoint_hash,
                signature =
                    excluded.signature,
                timestamp =
                    excluded.timestamp
        """, (
            level,
            last_vote_id,
            ledger_hash,
            previous_checkpoint_hash,
            checkpoint_hash,
            signature,
            timestamp
        ))

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


def get_all_checkpoints():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                checkpoint_id,
                level,
                last_vote_id,
                ledger_hash,
                previous_checkpoint_hash,
                checkpoint_hash,
                signature,
                timestamp
            FROM integrity_checkpoints
            ORDER BY
                CASE level
                    WHEN 'BOOTH' THEN 1
                    WHEN 'ZONAL' THEN 2
                    WHEN 'DEPUTY' THEN 3
                    WHEN 'CENTRAL' THEN 4
                    ELSE 5
                END
        """)

        checkpoints = cursor.fetchall()

    finally:

        connection.close()

    return checkpoints


# =========================================================
# DEMO RESET
# =========================================================

def reset_demo_voters():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            DELETE FROM votes
        """)

        cursor.execute("""
            UPDATE voters
            SET
                has_voted = 0,
                eligible = 1
        """)

        cursor.execute("""
            DELETE FROM voter_audit
        """)

        cursor.execute("""
            DELETE FROM integrity_checkpoints
        """)

        cursor.execute("""
            DELETE FROM security_events
        """)

        cursor.execute("""
            DELETE FROM sqlite_sequence
            WHERE name = 'votes'
        """)

        connection.commit()

        return True

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()