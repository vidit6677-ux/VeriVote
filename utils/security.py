import hashlib


def generate_hash(data):
    """Generate a SHA-256 hash."""

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()


def create_vote_hash(
    vote_reference,
    constituency,
    candidate,
    timestamp,
    previous_hash=""
):
    """Create an integrity hash for a vote."""

    data = (
        f"{vote_reference}|"
        f"{constituency}|"
        f"{candidate}|"
        f"{timestamp}|"
        f"{previous_hash}"
    )

    return generate_hash(data)