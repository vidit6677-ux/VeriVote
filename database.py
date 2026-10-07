import sqlite3
import hashlib
import secrets
from datetime import datetime

from config import DATABASE_PATH
from services.crypto_service import sha256_hex


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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS replication_outbox (
                outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vote_id INTEGER NOT NULL UNIQUE,
                voter_identity TEXT NOT NULL,
                constituency TEXT NOT NULL,
                candidate TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                vote_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                attempts INTEGER NOT NULL DEFAULT 0,
                last_error TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ballot_issuances (
                issuance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_identity TEXT NOT NULL UNIQUE,
                constituency TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                issued_at TEXT NOT NULL,
                used_at TEXT DEFAULT ''
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS private_ballots (
                ballot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ballot_token_hash TEXT NOT NULL UNIQUE,
                constituency TEXT NOT NULL,
                candidate TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                ballot_hash TEXT NOT NULL
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
    limit=100,
    role=None,
    action=None,
    status=None,
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        clauses = []
        values = []

        if role:
            clauses.append("role = ?")
            values.append(role)
        if action:
            clauses.append("action = ?")
            values.append(action)
        if status:
            clauses.append("status = ?")
            values.append(status)

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        query = f"""
            SELECT
                audit_id,
                username,
                role,
                action,
                details,
                status,
                timestamp
            FROM admin_audit
            {where}
            ORDER BY audit_id DESC
            LIMIT ?
        """
        values.append(limit)
        cursor.execute(query, tuple(values))

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
# REPLICATION OUTBOX
# =========================================================

def enqueue_replication(
    vote_id,
    voter_identity,
    constituency,
    candidate,
    timestamp,
    previous_hash,
    vote_hash,
    error_message="",
    cursor=None,
):
    """Create a durable replication job.

    When a caller supplies a cursor, this insert participates in the caller's
    transaction.  ``cast_vote`` uses that form so a committed local vote can
    never exist without a recoverable replication job.
    """
    now = datetime.now().isoformat()
    own_connection = cursor is None
    connection = None

    if own_connection:
        connection = get_connection()
        cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO replication_outbox (
                vote_id, voter_identity, constituency, candidate,
                timestamp, previous_hash, vote_hash, status,
                attempts, last_error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', 0, ?, ?, ?)
            ON CONFLICT(vote_id) DO NOTHING
        """, (
            vote_id, voter_identity, constituency, candidate,
            timestamp, previous_hash, vote_hash, error_message, now, now,
        ))

        outbox_row = cursor.execute("""
            SELECT outbox_id
            FROM replication_outbox
            WHERE vote_id = ?
        """, (vote_id,)).fetchone()

        if outbox_row is None:
            raise RuntimeError("Replication outbox entry could not be created.")

        if own_connection:
            connection.commit()

        return outbox_row[0]
    except Exception:
        if own_connection:
            connection.rollback()
        raise
    finally:
        if own_connection:
            connection.close()


def get_pending_replication(limit=20):
    connection = get_connection()
    try:
        return connection.execute("""
            SELECT outbox_id, vote_id, voter_identity, constituency,
                   candidate, timestamp, previous_hash, vote_hash,
                   attempts, last_error, created_at, updated_at
            FROM replication_outbox
            WHERE status = 'PENDING'
            ORDER BY outbox_id ASC
            LIMIT ?
        """, (limit,)).fetchall()
    finally:
        connection.close()


# =========================================================
# PRIVACY-AWARE BALLOT TOKEN FLOW
# =========================================================

def issue_ballot_token(voter_identity, constituency):
    voter = get_voter(voter_identity)
    if voter is None:
        return None, "Voter not found."
    if not voter["eligible"]:
        return None, "Voter is not eligible."
    if voter["has_voted"]:
        return None, "This voter has already voted."
    if voter["constituency"] != constituency:
        return None, "Constituency mismatch."

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now().isoformat()
    connection = get_connection()
    try:
        connection.execute("""
            INSERT INTO ballot_issuances (
                voter_identity, constituency, token_hash, issued_at, used_at
            ) VALUES (?, ?, ?, ?, '')
        """, (voter_identity, constituency, token_hash, now))
        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        return None, "A ballot token has already been issued for this voter."
    finally:
        connection.close()
    return raw_token, "Ballot token issued."


def cast_private_ballot(raw_token, candidate):
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        connection.execute("BEGIN IMMEDIATE")
        issuance = cursor.execute("""
            SELECT issuance_id, voter_identity, constituency, used_at
            FROM ballot_issuances
            WHERE token_hash = ?
        """, (token_hash,)).fetchone()
        if issuance is None:
            raise ValueError("Invalid ballot token.")
        issuance_id, voter_identity, constituency, used_at = issuance
        if used_at:
            raise ValueError("Ballot token has already been used.")
        previous = cursor.execute("""
            SELECT ballot_hash FROM private_ballots
            ORDER BY ballot_id DESC LIMIT 1
        """).fetchone()
        previous_hash = previous[0] if previous else "GENESIS"
        timestamp = datetime.now().isoformat()
        ballot_hash = sha256_hex(
            constituency,
            candidate,
            timestamp,
            previous_hash,
        )
        cursor.execute("""
            INSERT INTO private_ballots (
                ballot_token_hash, constituency, candidate,
                timestamp, previous_hash, ballot_hash
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (token_hash, constituency, candidate, timestamp, previous_hash, ballot_hash))
        cursor.execute("""
            UPDATE ballot_issuances SET used_at = ? WHERE issuance_id = ?
        """, (timestamp, issuance_id))
        cursor.execute("""
            UPDATE voters SET has_voted = 1 WHERE identity = ? AND has_voted = 0
        """, (voter_identity,))
        if cursor.rowcount != 1:
            raise ValueError("Voter is no longer eligible for this ballot.")
        connection.commit()

        try:
            from services.four_level_sync import replicate_private_ballot_to_all_levels

            replication = replicate_private_ballot_to_all_levels(
                ballot_id=issuance_id,
                ballot_token_hash=token_hash,
                constituency=constituency,
                candidate=candidate,
                timestamp=timestamp,
                previous_hash=previous_hash,
                ballot_hash=ballot_hash,
            )
            synchronization_ok = bool(replication.get("replicated"))
            synchronization_message = "Anonymous ballot replicated to all four levels."
        except Exception as error:
            synchronization_ok = False
            synchronization_message = (
                f"Ballot recorded, but anonymous replication needs attention: {error}"
            )

        from services.notification_service import send_vote_confirmation_sms

        voter = get_voter(voter_identity)
        sms_result = send_vote_confirmation_sms(
            voter.get("phone", "") if voter else "",
            constituency,
            f"PV-{issuance_id:06d}-{ballot_hash[:8].upper()}",
        )

        return {
            "success": True,
            "message": "Private ballot recorded.",
            "ballot_id": cursor.lastrowid,
            "ballot_hash": ballot_hash,
            "vote_hash": ballot_hash,
            "vote_reference": f"PV-{issuance_id:06d}-{ballot_hash[:8].upper()}",
            "constituency": constituency,
            "candidate": candidate,
            "timestamp": timestamp,
            "sms_sent": sms_result["success"],
            "sms_message": sms_result["message"],
            "synchronization_ok": synchronization_ok,
            "synchronization_message": synchronization_message,
        }
    except ValueError as error:
        connection.rollback()
        return {"success": False, "message": str(error)}
    except Exception:
        connection.rollback()
        return {"success": False, "message": "Private ballot could not be recorded safely."}
    finally:
        connection.close()


def mark_replication_succeeded(outbox_id):
    connection = get_connection()
    try:
        connection.execute("""
            UPDATE replication_outbox
            SET status = 'COMPLETED', updated_at = ?
            WHERE outbox_id = ?
        """, (datetime.now().isoformat(), outbox_id))
        connection.commit()
    finally:
        connection.close()


def mark_replication_failed(outbox_id, error_message):
    connection = get_connection()
    try:
        connection.execute("""
            UPDATE replication_outbox
            SET attempts = attempts + 1,
                last_error = ?,
                updated_at = ?
            WHERE outbox_id = ?
        """, (error_message, datetime.now().isoformat(), outbox_id))
        connection.commit()
    finally:
        connection.close()


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
            DELETE FROM replication_outbox
        """)

        cursor.execute("""
            DELETE FROM ballot_issuances
        """)

        cursor.execute("""
            DELETE FROM private_ballots
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
