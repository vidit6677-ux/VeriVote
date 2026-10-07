import sqlite3

from config import LEVEL_DATABASE_PATHS
from database import (
    add_demo_voter,
    get_connection,
    initialize_database,
)
from services import notification_service
from services.level_database import initialize_all_level_databases
from services.privacy_service import issue_one_time_ballot, submit_tokenized_ballot


TEST_IDENTITY = "PRIVATE-FLOW-TEST"


def test_tokenized_ballot_replicates_without_identity(monkeypatch):

    initialize_database()
    initialize_all_level_databases()
    add_demo_voter(TEST_IDENTITY, "Private Flow Test", "Test City", "")

    monkeypatch.setattr(
        notification_service,
        "send_vote_confirmation_sms",
        lambda *args: {"success": True, "message": "suppressed"},
    )

    try:
        token, message = issue_one_time_ballot(TEST_IDENTITY, "Test City")
        assert token is not None, message

        result = submit_tokenized_ballot(token, "Candidate A")

        assert result["success"] is True
        assert result["synchronization_ok"] is True

        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT ballot_token_hash FROM private_ballots"
            ).fetchone()
            assert row is not None
            assert TEST_IDENTITY not in row[0]
        finally:
            connection.close()

    finally:
        connection = get_connection()
        try:
            connection.execute(
                "DELETE FROM private_ballots WHERE ballot_token_hash IN "
                "(SELECT token_hash FROM ballot_issuances WHERE voter_identity = ?)",
                (TEST_IDENTITY,),
            )
            connection.execute(
                "DELETE FROM ballot_issuances WHERE voter_identity = ?",
                (TEST_IDENTITY,),
            )
            connection.execute(
                "DELETE FROM voters WHERE identity = ?",
                (TEST_IDENTITY,),
            )
            connection.commit()
        finally:
            connection.close()

        for path in LEVEL_DATABASE_PATHS.values():
            level_connection = sqlite3.connect(path)
            try:
                level_connection.execute("DELETE FROM private_ballots")
                level_connection.commit()
            finally:
                level_connection.close()
