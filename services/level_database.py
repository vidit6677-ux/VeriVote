import sqlite3
from datetime import datetime

from config import LEVEL_DATABASE_PATHS


LEVELS = (
    "BOOTH",
    "ZONAL",
    "DEPUTY",
    "CENTRAL",
)


def get_level_connection(level):
    level = str(level).upper()

    if level not in LEVEL_DATABASE_PATHS:
        raise ValueError(
            f"Unsupported database level: {level}"
        )

    connection = sqlite3.connect(
        LEVEL_DATABASE_PATHS[level],
        timeout=10
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def _ensure_column(cursor, table, column, definition):
    cursor.execute(
        f"PRAGMA table_info({table})"
    )

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if column not in columns:
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def initialize_level_database(level):

    level = str(level).upper()

    connection = get_level_connection(level)
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # DATABASE IDENTITY
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS database_identity (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                level TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            SELECT level
            FROM database_identity
            WHERE id = 1
        """)

        row = cursor.fetchone()

        if row is None:

            cursor.execute("""
                INSERT INTO database_identity (
                    id,
                    level,
                    created_at
                )
                VALUES (1, ?, ?)
            """, (
                level,
                datetime.now().isoformat()
            ))

        elif row[0] != level:

            raise ValueError(
                f"Database identity mismatch: "
                f"expected {level}, found {row[0]}"
            )

        # -------------------------------------------------
        # VOTE LEDGER
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                vote_id INTEGER PRIMARY KEY,
                voter_identity TEXT NOT NULL,
                constituency TEXT NOT NULL,
                candidate TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                vote_hash TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_level_votes_one_per_voter
            ON votes(voter_identity)
        """)

        # -------------------------------------------------
        # LOCAL CHECKPOINT
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS level_checkpoint (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                level TEXT NOT NULL UNIQUE,
                last_vote_id INTEGER NOT NULL DEFAULT 0,
                ledger_hash TEXT NOT NULL DEFAULT 'GENESIS',
                fingerprint TEXT NOT NULL DEFAULT '',
                checkpoint_hash TEXT NOT NULL DEFAULT '',
                signature TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
        """)

        # Migration for databases created by the first version.
        _ensure_column(
            cursor,
            "level_checkpoint",
            "fingerprint",
            "TEXT NOT NULL DEFAULT ''"
        )

        cursor.execute("""
            SELECT level
            FROM level_checkpoint
            WHERE id = 1
        """)

        row = cursor.fetchone()

        if row is None:

            cursor.execute("""
                INSERT INTO level_checkpoint (
                    id,
                    level,
                    last_vote_id,
                    ledger_hash,
                    fingerprint,
                    checkpoint_hash,
                    signature,
                    updated_at
                )
                VALUES (
                    1,
                    ?,
                    0,
                    'GENESIS',
                    '',
                    '',
                    '',
                    ?
                )
            """, (
                level,
                datetime.now().isoformat()
            ))

        elif row[0] != level:

            raise ValueError(
                f"Checkpoint identity mismatch: "
                f"expected {level}, found {row[0]}"
            )

        # -------------------------------------------------
        # PEER OBSERVATIONS
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS peer_checkpoints (
                peer_level TEXT PRIMARY KEY,
                last_vote_id INTEGER NOT NULL DEFAULT 0,
                ledger_hash TEXT NOT NULL DEFAULT 'GENESIS',
                fingerprint TEXT NOT NULL DEFAULT '',
                checkpoint_hash TEXT NOT NULL DEFAULT '',
                signature TEXT NOT NULL DEFAULT '',
                observed_at TEXT NOT NULL
            )
        """)

        _ensure_column(
            cursor,
            "peer_checkpoints",
            "fingerprint",
            "TEXT NOT NULL DEFAULT ''"
        )

        # -------------------------------------------------
        # SECURITY EVENTS
        # -------------------------------------------------

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


def initialize_all_level_databases():

    for level in LEVELS:
        initialize_level_database(level)


def get_level_database_path(level):

    level = str(level).upper()

    if level not in LEVEL_DATABASE_PATHS:
        raise ValueError(
            f"Unsupported database level: {level}"
        )

    return LEVEL_DATABASE_PATHS[level]
