import hashlib
import sqlite3

from config import LEVEL_DATABASE_PATHS
from services.four_level_sync import (
    verify_independent_databases,
    replicate_vote_to_all_levels,
    establish_initial_trust,
)

TEST_VOTE_ID = 900001
TEST_VOTER = "PHASE5-TEST-VOTER"
TEST_CONSTITUENCY = "TEST-CONSTITUENCY"
TEST_CANDIDATE = "TEST-CANDIDATE"
TEST_TIMESTAMP = "2026-09-25T10:20:00"
TEST_PREVIOUS_HASH = "GENESIS"

TEST_VOTE_HASH = hashlib.sha256(
    f"{TEST_VOTER}|{TEST_CONSTITUENCY}|{TEST_CANDIDATE}|{TEST_TIMESTAMP}|{TEST_PREVIOUS_HASH}".encode()
).hexdigest()

TEST_VOTE = (
    TEST_VOTE_ID,
    TEST_VOTER,
    TEST_CONSTITUENCY,
    TEST_CANDIDATE,
    TEST_TIMESTAMP,
    TEST_PREVIOUS_HASH,
    TEST_VOTE_HASH,
)

print("Checking baseline...")
baseline = verify_independent_databases()
print("Baseline synchronized:", baseline["synchronized"])

if not baseline["synchronized"]:
    raise RuntimeError(
        "ABORTED: Four databases are not synchronized before the test."
    )

for level, path in LEVEL_DATABASE_PATHS.items():
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(
            "SELECT vote_id FROM votes WHERE vote_id = ? OR voter_identity = ?",
            (TEST_VOTE_ID, TEST_VOTER),
        ).fetchone()
    finally:
        connection.close()

    if row is not None:
        raise RuntimeError(
            f"ABORTED: Test record already exists in {level}."
        )

print("Replicating synthetic vote...")
snapshots = replicate_vote_to_all_levels(*TEST_VOTE)

print("Replication returned:", len(snapshots), "snapshots")

after_replication = verify_independent_databases()
print("After replication synchronized:", after_replication["synchronized"])

if not after_replication["synchronized"]:
    raise RuntimeError(
        "REPLICATION TEST FAILED: integrity verification reported an alert."
    )

print("REPLICATION TEST: PASSED")

print("Cleaning up synthetic vote...")

for level, path in LEVEL_DATABASE_PATHS.items():
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "DELETE FROM votes WHERE vote_id = ? AND voter_identity = ?",
            (TEST_VOTE_ID, TEST_VOTER),
        )
        connection.commit()
    finally:
        connection.close()

establish_initial_trust()

final_check = verify_independent_databases()

print("Cleanup complete.")
print("Final synchronized:", final_check["synchronized"])

if not final_check["synchronized"]:
    raise RuntimeError(
        "CLEANUP FAILED: databases are not synchronized."
    )

print("OVERALL: PASSED")
