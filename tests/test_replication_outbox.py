from database import add_demo_voter, get_connection, initialize_database
from services import voting_service


TEST_IDENTITY = "OUTBOX-TEST-VOTER"
TEST_CONSTITUENCY = "Outbox City"


def _cleanup():
    connection = get_connection()
    try:
        connection.execute("DELETE FROM replication_outbox WHERE voter_identity = ?", (TEST_IDENTITY,))
        connection.execute("DELETE FROM voter_audit WHERE voter_identity = ?", (TEST_IDENTITY,))
        connection.execute("DELETE FROM votes WHERE voter_identity = ?", (TEST_IDENTITY,))
        connection.execute("DELETE FROM voters WHERE identity = ?", (TEST_IDENTITY,))
        connection.commit()
    finally:
        connection.close()


def test_replication_failure_leaves_a_durable_pending_outbox_job(monkeypatch):
    initialize_database()
    _cleanup()
    add_demo_voter(TEST_IDENTITY, "Outbox Test", TEST_CONSTITUENCY, "")
    monkeypatch.setattr(
        voting_service,
        "replicate_vote_to_all_levels",
        lambda **_: (_ for _ in ()).throw(RuntimeError("simulated replication failure")),
    )
    monkeypatch.setattr(
        voting_service,
        "send_vote_confirmation_sms",
        lambda *_: {"success": True, "message": "suppressed during test"},
    )

    try:
        result = voting_service.cast_vote(TEST_IDENTITY, TEST_CONSTITUENCY, "Candidate")
        assert result["success"]
        assert not result["synchronization_ok"]

        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT status, attempts FROM replication_outbox WHERE voter_identity = ?",
                (TEST_IDENTITY,),
            ).fetchone()
        finally:
            connection.close()

        assert row == ("PENDING", 1)
    finally:
        _cleanup()


def test_vote_is_rolled_back_if_its_outbox_job_cannot_be_created(monkeypatch):
    initialize_database()
    _cleanup()
    add_demo_voter(TEST_IDENTITY, "Outbox Test", TEST_CONSTITUENCY, "")
    monkeypatch.setattr(
        voting_service,
        "enqueue_replication",
        lambda **_: (_ for _ in ()).throw(RuntimeError("simulated outbox failure")),
    )

    try:
        result = voting_service.cast_vote(TEST_IDENTITY, TEST_CONSTITUENCY, "Candidate")
        assert not result["success"]

        connection = get_connection()
        try:
            vote_count = connection.execute(
                "SELECT COUNT(*) FROM votes WHERE voter_identity = ?",
                (TEST_IDENTITY,),
            ).fetchone()[0]
            has_voted = connection.execute(
                "SELECT has_voted FROM voters WHERE identity = ?",
                (TEST_IDENTITY,),
            ).fetchone()[0]
        finally:
            connection.close()

        assert vote_count == 0
        assert has_voted == 0
    finally:
        _cleanup()
