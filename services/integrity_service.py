import hashlib
from database import get_connection


def get_previous_hash():
    """
    Gets the hash of the most recently stored vote.

    If no votes exist, returns GENESIS.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT vote_hash
        FROM votes
        ORDER BY vote_id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return "GENESIS"

    return row[0]


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


def verify_integrity():
    """
    Checks whether the stored vote chain is intact.
    """

    connection = get_connection()
    cursor = connection.cursor()

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

        # Check previous hash
        if stored_previous_hash != previous_hash:
            return False

        # Recalculate hash
        calculated_hash = generate_vote_hash(
            voter_identity,
            constituency,
            candidate,
            timestamp,
            stored_previous_hash
        )

        # Compare hashes
        if calculated_hash != stored_vote_hash:
            return False

        previous_hash = stored_vote_hash

    return True