import sqlite3
from datetime import datetime

from database import (
    get_connection,
    get_voter,
    mark_voted,
    save_vote,
    add_security_event,
    enqueue_replication,
    mark_replication_failed,
    mark_replication_succeeded,
)

from services.integrity_service import (
    get_previous_hash,
    generate_vote_hash,
)

from services.notification_service import (
    send_vote_confirmation_sms,
)

from services.four_level_sync import (
    replicate_vote_to_all_levels,
)


def cast_vote(
    voter_identity,
    constituency,
    candidate
):

    # =====================================================
    # 1. APPLICATION-LEVEL CHECK
    # =====================================================

    voter = get_voter(
        voter_identity
    )

    if voter is None:

        return {
            "success": False,
            "message": "Voter not found."
        }

    # -----------------------------------------------------
    # ELIGIBILITY
    # -----------------------------------------------------

    if not voter["eligible"]:

        return {
            "success": False,
            "message": "Voter is not eligible."
        }

    # -----------------------------------------------------
    # DOUBLE-VOTE CHECK
    # -----------------------------------------------------

    if voter["has_voted"]:

        return {
            "success": False,
            "message": "This voter has already voted."
        }

    # -----------------------------------------------------
    # CONSTITUENCY CHECK
    # -----------------------------------------------------

    if voter["constituency"] != constituency:

        return {
            "success": False,
            "message": "Constituency mismatch."
        }

    # =====================================================
    # ATOMIC VOTE TRANSACTION
    # =====================================================

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # START WRITE TRANSACTION
        # -------------------------------------------------

        connection.execute(
            "BEGIN IMMEDIATE"
        )

        # -------------------------------------------------
        # FINAL VOTER CHECK INSIDE TRANSACTION
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                identity,
                name,
                constituency,
                eligible,
                has_voted,
                phone
            FROM voters
            WHERE identity = ?
        """, (
            voter_identity,
        ))

        current_voter = cursor.fetchone()

        if current_voter is None:

            raise ValueError(
                "Voter not found during final verification."
            )

        identity = current_voter[0]
        voter_constituency = current_voter[2]
        eligible = bool(current_voter[3])
        has_voted = bool(current_voter[4])
        phone = current_voter[5] or ""

        # -------------------------------------------------
        # FINAL ELIGIBILITY CHECK
        # -------------------------------------------------

        if not eligible:

            raise ValueError(
                "Voter is not eligible."
            )

        # -------------------------------------------------
        # FINAL DOUBLE-VOTE CHECK
        # -------------------------------------------------

        if has_voted:

            raise ValueError(
                "This voter has already voted."
            )

        # -------------------------------------------------
        # FINAL CONSTITUENCY CHECK
        # -------------------------------------------------

        if voter_constituency != constituency:

            raise ValueError(
                "Constituency mismatch."
            )

        # -------------------------------------------------
        # TIMESTAMP
        # -------------------------------------------------

        timestamp = datetime.now().isoformat()

        # -------------------------------------------------
        # PREVIOUS HASH
        # -------------------------------------------------

        previous_hash = get_previous_hash(
            cursor=cursor
        )

        # -------------------------------------------------
        # CURRENT HASH
        # -------------------------------------------------

        vote_hash = generate_vote_hash(
            identity,
            constituency,
            candidate,
            timestamp,
            previous_hash
        )

        # -------------------------------------------------
        # SAVE VOTE
        # -------------------------------------------------

        vote_id = save_vote(
            identity,
            constituency,
            candidate,
            timestamp,
            previous_hash,
            vote_hash,
            cursor=cursor
        )

        # -------------------------------------------------
        # MARK VOTER AS VOTED
        # -------------------------------------------------

        mark_voted(
            identity,
            cursor=cursor
        )

        # The local vote and its recovery record share one SQLite
        # transaction. If the process stops after commit but before the
        # network-style replication step, Central can still retry this vote.
        outbox_id = enqueue_replication(
            vote_id=vote_id,
            voter_identity=identity,
            constituency=constituency,
            candidate=candidate,
            timestamp=timestamp,
            previous_hash=previous_hash,
            vote_hash=vote_hash,
            cursor=cursor,
        )

        # -------------------------------------------------
        # ATOMIC COMMIT
        # -------------------------------------------------

        connection.commit()

    except sqlite3.IntegrityError as error:

        connection.rollback()

        error_text = str(error).lower()

        if (
            "unique" in error_text
            or "idx_votes_one_vote_per_voter" in error_text
            or "voter_identity" in error_text
        ):

            return {
                "success": False,
                "message": "This voter has already voted."
            }

        return {
            "success": False,
            "message": "Vote could not be recorded safely."
        }

    except ValueError as error:

        connection.rollback()

        return {
            "success": False,
            "message": str(error)
        }

    except Exception as error:

        connection.rollback()

        return {
            "success": False,
            "message": (
                f"Vote transaction failed: {error}"
            )
        }

    finally:

        connection.close()

    # =====================================================
    # FOUR-LEVEL VOTE REPLICATION
    # =====================================================
    #
    # The operational vote is already committed in verivote.db.
    # The four independent level databases are then updated in
    # a separate SQLite transaction across the four files.
    #
    # A replication failure never rolls back the already-committed
    # operational vote, but it is surfaced to the caller and
    # recorded as a security event for investigation.
    #
    # =====================================================

    synchronization_ok = True
    synchronization_message = (
        "Four-level checkpoints synchronized."
    )

    try:

        replicate_vote_to_all_levels(
            vote_id=vote_id,
            voter_identity=identity,
            constituency=constituency,
            candidate=candidate,
            timestamp=timestamp,
            previous_hash=previous_hash,
            vote_hash=vote_hash,
        )

        synchronization_message = (
            "Vote replicated to BOOTH, ZONAL, DEPUTY, "
            "and CENTRAL databases with synchronized checkpoints."
        )

        mark_replication_succeeded(outbox_id)

    except Exception as error:

        synchronization_ok = False

        synchronization_message = (
            f"Vote committed, but four-level replication "
            f"requires attention: {error}"
        )

        add_security_event(
            source_level="CENTRAL",
            event_type="SYNC_FAILURE",
            severity="HIGH",
            details=synchronization_message,
        )

        mark_replication_failed(outbox_id, synchronization_message)

    # =====================================================
    # VOTE REFERENCE
    # =====================================================

    vote_reference = (
        f"VV-{vote_id:06d}-"
        f"{vote_hash[:8].upper()}"
    )

    # =====================================================
    # SMS
    # =====================================================

    sms_result = send_vote_confirmation_sms(
        phone,
        constituency,
        vote_reference
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "success": True,

        "message": (
            "Vote successfully recorded."
        ),

        "vote_id": vote_id,

        "vote_reference": vote_reference,

        "vote_hash": vote_hash,

        "previous_hash": previous_hash,

        "constituency": constituency,

        "candidate": candidate,

        "timestamp": timestamp,

        # -------------------------------------------------
        # SYNCHRONIZATION
        # -------------------------------------------------

        "synchronization_ok": synchronization_ok,

        "synchronization_message": (
            synchronization_message
        ),

        # -------------------------------------------------
        # SMS
        # -------------------------------------------------

        "sms_sent": sms_result["success"],

        "sms_message": sms_result["message"],
    }
