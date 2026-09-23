from datetime import datetime

from database import (
    get_voter,
    mark_voted,
    save_vote
)

from services.integrity_service import (
    get_previous_hash,
    generate_vote_hash
)

from services.notification_service import (
    send_vote_confirmation_sms
)


def cast_vote(
    voter_identity,
    constituency,
    candidate
):

    # ---------------------------------------
    # CHECK VOTER
    # ---------------------------------------

    voter = get_voter(
        voter_identity
    )

    if voter is None:

        return {
            "success": False,
            "message": "Voter not found."
        }

    # ---------------------------------------
    # CHECK ELIGIBILITY
    # ---------------------------------------

    if not voter["eligible"]:

        return {
            "success": False,
            "message": "Voter is not eligible."
        }

    # ---------------------------------------
    # PREVENT DOUBLE VOTING
    # ---------------------------------------

    if voter["has_voted"]:

        return {
            "success": False,
            "message": "This voter has already voted."
        }

    # ---------------------------------------
    # VERIFY CONSTITUENCY
    # ---------------------------------------

    if voter["constituency"] != constituency:

        return {
            "success": False,
            "message": "Constituency mismatch."
        }

    # ---------------------------------------
    # TIMESTAMP
    # ---------------------------------------

    timestamp = datetime.now().isoformat()

    # ---------------------------------------
    # PREVIOUS HASH
    # ---------------------------------------

    previous_hash = get_previous_hash()

    # ---------------------------------------
    # CURRENT HASH
    # ---------------------------------------

    vote_hash = generate_vote_hash(
        voter_identity,
        constituency,
        candidate,
        timestamp,
        previous_hash
    )

    # ---------------------------------------
    # SAVE VOTE
    # ---------------------------------------

    vote_id = save_vote(
        voter_identity,
        constituency,
        candidate,
        timestamp,
        previous_hash,
        vote_hash
    )

    # ---------------------------------------
    # MARK VOTER AS VOTED
    # ---------------------------------------

    mark_voted(
        voter_identity
    )

    # ---------------------------------------
    # VOTE REFERENCE
    # ---------------------------------------

    vote_reference = (
        f"VV-{vote_id:06d}-"
        f"{vote_hash[:8].upper()}"
    )

    # ---------------------------------------
    # SEND SMS
    # ---------------------------------------

    sms_result = send_vote_confirmation_sms(
        voter["phone"],
        constituency,
        vote_reference
    )

    # ---------------------------------------
    # RETURN RESULT
    # ---------------------------------------

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

        # SMS information
        "sms_sent": sms_result["success"],

        "sms_message": sms_result["message"]
    }