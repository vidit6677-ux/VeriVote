import sqlite3


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_NAME = "verivote.db"


# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # VOTERS TABLE
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                constituency TEXT NOT NULL,
                eligible INTEGER DEFAULT 1,
                has_voted INTEGER DEFAULT 0,
                phone TEXT DEFAULT ''
            )
        """)

        # -------------------------------------------------
        # ADD PHONE COLUMN TO OLD DATABASES
        # -------------------------------------------------

        cursor.execute("""
            PRAGMA table_info(voters)
        """)

        voter_columns = [
            row[1]
            for row in cursor.fetchall()
        ]

        if "phone" not in voter_columns:

            cursor.execute("""
                ALTER TABLE voters
                ADD COLUMN phone TEXT DEFAULT ''
            """)

        # -------------------------------------------------
        # CHECK VOTES TABLE
        # -------------------------------------------------

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='votes'
        """)

        votes_exists = cursor.fetchone()

        if votes_exists:

            cursor.execute("""
                PRAGMA table_info(votes)
            """)

            columns = [
                row[1]
                for row in cursor.fetchall()
            ]

            required_columns = {
                "vote_id",
                "voter_identity",
                "constituency",
                "candidate",
                "timestamp",
                "previous_hash",
                "vote_hash"
            }

            # -------------------------------------------------
            # RECREATE OLD / INCOMPATIBLE VOTES TABLE
            # -------------------------------------------------

            if not required_columns.issubset(
                set(columns)
            ):

                cursor.execute("""
                    DROP TABLE votes
                """)

        # -------------------------------------------------
        # VOTES TABLE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SAVE ALL DATABASE CHANGES
        # -------------------------------------------------

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

        # -------------------------------------------------
        # INSERT VOTER
        # -------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO voters
            (
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

        # -------------------------------------------------
        # UPDATE EXISTING VOTER
        # -------------------------------------------------

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


# =========================================================
# GET VOTER
# =========================================================


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
        """, (identity,))

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
        "phone": row[5]
    }


# =========================================================
# MARK VOTER AS VOTED
# =========================================================


def mark_voted(identity):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE voters
            SET has_voted = 1
            WHERE identity = ?
        """, (identity,))

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# GET ALL VOTERS
# =========================================================


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
# VOTE FUNCTIONS
# =========================================================


def save_vote(
    voter_identity,
    constituency,
    candidate,
    timestamp,
    previous_hash,
    vote_hash
):

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

        connection.commit()

        vote_id = cursor.lastrowid

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()

    return vote_id


# =========================================================
# GET VOTE COUNT
# =========================================================


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


# =========================================================
# GET ALL VOTES
# =========================================================


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
# RESET ALL DEMO VOTES
# =========================================================


def reset_demo_voters():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # DELETE ALL RECORDED VOTES
        # -------------------------------------------------

        cursor.execute("""
            DELETE FROM votes
        """)

        # -------------------------------------------------
        # RESET EVERY VOTER
        # -------------------------------------------------

        cursor.execute("""
            UPDATE voters
            SET
                has_voted = 0,
                eligible = 1
        """)

        # -------------------------------------------------
        # RESET VOTE ID COUNTER
        # -------------------------------------------------

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