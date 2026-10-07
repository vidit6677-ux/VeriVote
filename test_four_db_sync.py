from config import ADMIN_LEVELS
from services.level_database import (
    initialize_all_level_databases,
)
from services.four_level_sync import (
    bootstrap_from_legacy_database,
    establish_initial_trust,
    verify_independent_databases,
)


def _connect(level):
    from config import LEVEL_DATABASE_PATHS
    import sqlite3

    return sqlite3.connect(
        LEVEL_DATABASE_PATHS[level],
        timeout=10
    )


def _tamper_level(level):

    connection = _connect(level)

    try:

        row = connection.execute("""
            SELECT
                vote_id,
                candidate
            FROM votes
            ORDER BY vote_id ASC
            LIMIT 1
        """).fetchone()

        if row is not None:

            vote_id = row[0]
            original_candidate = row[1]

            connection.execute("""
                UPDATE votes
                SET candidate = ?
                WHERE vote_id = ?
            """, (
                "TAMPERED-DEMO-VALUE",
                vote_id,
            ))

            connection.commit()

            return {
                "mode": "modified_existing_vote",
                "vote_id": vote_id,
                "original_candidate": original_candidate,
            }

        row = connection.execute("""
            SELECT COALESCE(MAX(vote_id), 0)
            FROM votes
        """).fetchone()

        vote_id = max(
            900000,
            int(row[0]) + 1
        )

        connection.execute("""
            INSERT INTO votes (
                vote_id,
                voter_identity,
                constituency,
                candidate,
                timestamp,
                previous_hash,
                vote_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            vote_id,
            f"TAMPER-TEST-{level}",
            "TEST",
            "TAMPERED-DEMO-VALUE",
            "2099-01-01T00:00:00",
            "GENESIS",
            f"TAMPERED-{level}",
        ))

        connection.commit()

        return {
            "mode": "inserted_temporary_vote",
            "vote_id": vote_id,
        }

    finally:
        connection.close()


def _restore_level(level, backup):

    connection = _connect(level)

    try:

        if backup["mode"] == "modified_existing_vote":

            connection.execute("""
                UPDATE votes
                SET candidate = ?
                WHERE vote_id = ?
            """, (
                backup["original_candidate"],
                backup["vote_id"],
            ))

        else:

            connection.execute("""
                DELETE FROM votes
                WHERE vote_id = ?
            """, (
                backup["vote_id"],
            ))

        connection.commit()

    finally:
        connection.close()


def _print_result(title, result):

    print()
    print("=" * 72)
    print(title)
    print("=" * 72)

    print(
        "OVERALL:",
        "SYNCED" if result["synchronized"] else "ALERT"
    )

    for observer in ADMIN_LEVELS:

        alerts = result["alerts_by_observer"][observer]

        print(
            f"{observer:7} detected {len(alerts)} alert(s)"
        )

        for alert in alerts:

            print(
                "   ",
                alert["type"],
                "| source:",
                alert["source_level"],
            )


def main():

    initialize_all_level_databases()

    # First initialization only: copy the existing operational
    # ledger into all four independent databases.
    bootstrap_from_legacy_database()

    # Establish the signed baseline and peer observations.
    establish_initial_trust()

    baseline = verify_independent_databases()

    _print_result(
        "BASELINE FOUR-DATABASE SYNCHRONIZATION",
        baseline,
    )

    if not baseline["synchronized"]:

        print(
            "\nBaseline is not synchronized. "
            "Stop here and investigate."
        )
        return

    print(
        "\nBaseline synchronization PASSED."
    )

    # -----------------------------------------------------
    # TAMPER TEST — ONE DATABASE AT A TIME
    # -----------------------------------------------------

    for tampered_level in ADMIN_LEVELS:

        print()
        print(
            "-" * 72
        )

        print(
            f"TAMPERING TEST: {tampered_level}"
        )

        backup = _tamper_level(
            tampered_level
        )

        try:

            result = verify_independent_databases()

            _print_result(
                f"AFTER TAMPERING {tampered_level}",
                result,
            )

            other_levels = [
                level
                for level in ADMIN_LEVELS
                if level != tampered_level
            ]

            detected_by = []

            for observer in other_levels:

                found = any(
                    alert["source_level"]
                    == tampered_level
                    for alert in
                    result[
                        "alerts_by_observer"
                    ][observer]
                )

                if found:
                    detected_by.append(
                        observer
                    )

            print(
                f"\n{tampered_level} tamper detected by "
                f"other DBs:",
                detected_by,
            )

            if set(detected_by) == set(other_levels):

                print(
                    "RESULT: PASSED — all other databases "
                    "flagged the tampered database."
                )

            else:

                print(
                    "RESULT: FAILED — not every other "
                    "database flagged the tampering."
                )

        finally:

            _restore_level(
                tampered_level,
                backup,
            )

            restored = verify_independent_databases()

            print(
                f"Restored {tampered_level}. "
                f"Overall synchronized:",
                restored["synchronized"],
            )


if __name__ == "__main__":
    main()
