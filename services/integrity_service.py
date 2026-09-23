import hashlib

from database import get_connection


# =========================================================
# GET PREVIOUS HASH
# =========================================================
#
# cursor=None:
#     Function opens its own database connection.
#
# cursor=<existing cursor>:
#     Function uses the caller's connection/transaction.
#
# This second mode is important for Phase 4 because the
# previous hash and the new vote must be handled using the
# same database transaction.
#
# =========================================================


def get_previous_hash(cursor=None):

    own_connection = cursor is None

    if own_connection:

        connection = get_connection()
        cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT vote_hash
            FROM votes
            ORDER BY vote_id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

    finally:

        if own_connection:
            connection.close()

    if row is None:

        return "GENESIS"

    return row[0]


# =========================================================
# GENERATE VOTE HASH
# =========================================================


def generate_vote_hash(
    voter_identity,
    constituency,
    candidate,
    timestamp,
    previous_hash
):

    """
    Creates a SHA-256 hash for the vote.

    The previous hash becomes part of the new hash,
    creating a tamper-evident chain.
    """

    vote_data = (
        f"{voter_identity}|"
        f"{constituency}|"
        f"{candidate}|"
        f"{timestamp}|"
        f"{previous_hash}"
    )

    return hashlib.sha256(
        vote_data.encode("utf-8")
    ).hexdigest()


# =========================================================
# VERIFY LEDGER INTEGRITY
# =========================================================


def verify_integrity():

    """
    Checks whether the stored vote chain is intact.
    """

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

    previous_hash = "GENESIS"

    for vote in votes:

        (
            vote_id,
            voter_identity,
            constituency,
            candidate,
            timestamp,
            stored_previous_hash,
            stored_vote_hash
        ) = vote

        # -------------------------------------------------
        # CHECK PREVIOUS HASH LINK
        # -------------------------------------------------

        if stored_previous_hash != previous_hash:

            return False

        # -------------------------------------------------
        # RECALCULATE CURRENT HASH
        # -------------------------------------------------

        calculated_hash = generate_vote_hash(
            voter_identity,
            constituency,
            candidate,
            timestamp,
            stored_previous_hash
        )

        # -------------------------------------------------
        # COMPARE STORED AND CALCULATED HASH
        # -------------------------------------------------

        if calculated_hash != stored_vote_hash:

            return False

        previous_hash = stored_vote_hash

    return True