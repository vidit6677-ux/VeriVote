import sqlite3

from config import DATABASE_PATH

from services.sync_service import (
    get_four_level_security_summary,
)


def tamper_booth_checkpoint():
    """
    Temporarily modify the BOOTH checkpoint to simulate
    unauthorized tampering.

    The original checkpoint is restored after the test.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    original_hash = None

    try:

        # =================================================
        # GET ORIGINAL BOOTH CHECKPOINT
        # =================================================

        cursor.execute("""
            SELECT ledger_hash
            FROM integrity_checkpoints
            WHERE level = 'BOOTH'
        """)

        row = cursor.fetchone()

        if row is None:

            raise RuntimeError(
                "BOOTH checkpoint does not exist. "
                "Initialize four-level synchronization first."
            )

        original_hash = row[0]

        # =================================================
        # SIMULATE TAMPERING
        # =================================================

        cursor.execute("""
            UPDATE integrity_checkpoints
            SET ledger_hash = ?
            WHERE level = 'BOOTH'
        """, (
            "TAMPERED_DEMO_HASH",
        ))

        connection.commit()

        print()
        print("=" * 60)
        print("SIMULATING BOOTH TAMPERING")
        print("=" * 60)

        # =================================================
        # RUN SECURITY CHECK
        # =================================================

        result = get_four_level_security_summary()

        print()
        print(
            "Overall Status:",
            result["overall"]
        )

        print()

        for level, info in result["levels"].items():

            print(
                f"{level:<10} -> {info['status']}"
            )

        # =================================================
        # SHOW ALERTS
        # =================================================

        print()
        print("Alerts:")

        alerts = result.get(
            "alerts",
            []
        )

        if not alerts:

            print(
                "No alerts reported."
            )

        else:

            for alert in alerts:

                print(
                    f"- {alert['level']}: "
                    f"{alert['type']} - "
                    f"{alert['message']}"
                )

        # =================================================
        # TEST RESULT
        # =================================================

        booth_status = (
            result["levels"]
            .get("BOOTH", {})
            .get("status")
        )

        print()

        if booth_status in (
            "TAMPERED",
            "MISMATCH",
        ):

            print(
                "✓ TEST PASSED: "
                "BOOTH tampering was detected."
            )

        else:

            print(
                "✗ TEST FAILED: "
                "BOOTH tampering was not detected."
            )

    finally:

        # =================================================
        # RESTORE ORIGINAL CHECKPOINT
        # =================================================

        if original_hash is not None:

            cursor.execute("""
                UPDATE integrity_checkpoints
                SET ledger_hash = ?
                WHERE level = 'BOOTH'
            """, (
                original_hash,
            ))

            connection.commit()

        connection.close()

        print()
        print(
            "BOOTH checkpoint restored."
        )


# =========================================================
# RUN TEST
# =========================================================

if __name__ == "__main__":

    tamper_booth_checkpoint()