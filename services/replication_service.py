"""Retry worker for votes whose four-level replication needs attention."""

from database import (
    get_pending_replication,
    mark_replication_failed,
    mark_replication_succeeded,
)
from services.four_level_sync import replicate_vote_to_all_levels


def retry_pending_replication(limit=20):
    results = []
    for row in get_pending_replication(limit):
        (
            outbox_id, vote_id, voter_identity, constituency,
            candidate, timestamp, previous_hash, vote_hash,
            attempts, last_error, created_at, updated_at,
        ) = row
        try:
            replicate_vote_to_all_levels(
                vote_id=vote_id,
                voter_identity=voter_identity,
                constituency=constituency,
                candidate=candidate,
                timestamp=timestamp,
                previous_hash=previous_hash,
                vote_hash=vote_hash,
            )
            mark_replication_succeeded(outbox_id)
            results.append({"vote_id": vote_id, "status": "COMPLETED"})
        except Exception as error:
            mark_replication_failed(outbox_id, str(error))
            results.append({"vote_id": vote_id, "status": "PENDING", "error": str(error)})
    return results
