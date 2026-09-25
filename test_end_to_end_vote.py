import sqlite3

from config import DATABASE_PATH, LEVEL_DATABASE_PATHS
from database import initialize_database, get_all_votes
from services import voting_service
from services.four_level_sync import (
    verify_independent_databases,
    establish_initial_trust,
)

TEST_VOTER = "PHASE5-E2E-TEST"
TEST_NAME = "Phase5 Test Voter"
TEST_CONSTITUENCY = "TEST-CONSTITUENCY"
TEST_CANDIDATE = "TEST-CANDIDATE"


def fake_sms(phone, constituency, vote_reference):
    return {
        "success": True,
        "message": "SMS suppressed during automated test."
    }


voting_service.send_vote_confirmation_sms = fake_sms

initialize_database()

legacy_votes_before = get_all_votes()

if legacy_votes_before:
    raise RuntimeError(
        "ABORTED: verivote.db already contains votes. "
        "This controlled end-to-end cleanup test expects zero votes."
    )

for level, path in LEVEL_DATABASE_PATHS.items():
    connection = sqlite3.connect(path)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM votes"
        ).fetchone()[0]

        if count != 0:
            raise RuntimeError(
                f"ABORTED: {level} database contains {count} vote(s)."
            )
    finally:
        connection.close()

baseline = verify_independent_databases()

if not baseline["synchronized"]:
    raise RuntimeError(
        "ABORTED: Four databases are not synchronized before E2E test."
    )

print("BASELINE: SYNCHRONIZED")

connection = sqlite3.connect(DATABASE_PATH)

try:
    connection.execute("""
        INSERT INTO voters (
            identity,
            name,
            constituency,
            eligible,
            has_voted,
            phone
        )
        VALUES (?, ?, ?, 1, 0, '')
    """, (
        TEST_VOTER,
        TEST_NAME,
        TEST_CONSTITUENCY,
    ))

    connection.commit()

finally:
    connection.close()

print("Temporary voter created.")

result = voting_service.cast_vote(
    TEST_VOTER,
    TEST_CONSTITUENCY,
    TEST_CANDIDATE,
)

print("cast_vote success:", result["success"])
print("synchronization_ok:", result.get("synchronization_ok"))
print("message:", result.get("message"))

if not result["success"]:
    raise RuntimeError(
        f"E2E TEST FAILED: {result}"
    )

if not result.get("synchronization_ok"):
    raise RuntimeError(
        "E2E TEST FAILED: vote succeeded but four-level replication failed."
    )

vote_id = result["vote_id"]

for level, path in LEVEL_DATABASE_PATHS.items():

    connection = sqlite3.connect(path)

    try:
        row = connection.execute("""
            SELECT
                vote_id,
                voter_identity,
                constituency,
                candidate,
                timestamp,
                previous_hash,
                vote_hash
            FROM votes
            WHERE vote_id = ?
        """, (vote_id,)).fetchone()

    finally:
        connection.close()

    if row is None:
        raise RuntimeError(
            f"E2E TEST FAILED: {level} does not contain vote {vote_id}."
        )

    print(f"{level}: vote replicated")

print("FOUR DATABASE REPLICATION: PASSED")

duplicate_result = voting_service.cast_vote(
    TEST_VOTER,
    TEST_CONSTITUENCY,
    TEST_CANDIDATE,
)

print(
    "Duplicate attempt:",
    duplicate_result["success"],
    duplicate_result["message"]
)

if duplicate_result["success"]:
    raise RuntimeError(
        "E2E TEST FAILED: duplicate vote was accepted."
    )

if "already voted" not in duplicate_result["message"].lower():
    raise RuntimeError(
        "E2E TEST FAILED: duplicate vote was rejected for an unexpected reason."
    )

print("DUPLICATE VOTE PROTECTION: PASSED")

# ---------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------

connection = sqlite3.connect(DATABASE_PATH)

try:
    connection.execute(
        "DELETE FROM votes WHERE voter_identity = ?",
        (TEST_VOTER,)
    )

    connection.execute(
        "DELETE FROM voter_audit WHERE voter_identity = ?",
        (TEST_VOTER,)
    )
    connection.execute(
        "DELETE FROM replication_outbox WHERE voter_identity = ?",
        (TEST_VOTER,)
    )

    connection.execute(
        "DELETE FROM voters WHERE identity = ?",
        (TEST_VOTER,)
    )

    connection.commit()

finally:
    connection.close()

for level, path in LEVEL_DATABASE_PATHS.items():

    connection = sqlite3.connect(path)

    try:
        connection.execute(
            "DELETE FROM votes WHERE voter_identity = ?",
            (TEST_VOTER,)
        )
        connection.commit()

    finally:
        connection.close()

establish_initial_trust()

final_check = verify_independent_databases()

print("Cleanup synchronized:", final_check["synchronized"])

if not final_check["synchronized"]:
    raise RuntimeError(
        "CLEANUP FAILED: four databases are not synchronized."
    )

print("E2E TEST: PASSED")
