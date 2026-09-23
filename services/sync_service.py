import hashlib
import hmac
from datetime import datetime

from config import (
    ADMIN_LEVELS,
    LEVEL_SIGNING_SECRETS,
)

from database import (
    add_security_event,
    get_all_checkpoints,
    get_all_votes,
    get_checkpoint,
    save_checkpoint,
)


# =========================================================
# LEDGER FINGERPRINT
# =========================================================

def calculate_ledger_fingerprint():
    """
    Create a fingerprint of the complete vote ledger.

    We include every vote_id and vote_hash so that changes
    such as modification, insertion, or deletion affect
    the fingerprint.
    """

    votes = get_all_votes()

    payload = "|".join(
        f"{vote[0]}:{vote[6]}"
        for vote in votes
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


# =========================================================
# CURRENT LEDGER STATE
# =========================================================

def get_current_ledger_state():

    votes = get_all_votes()

    if not votes:

        return {
            "last_vote_id": 0,
            "ledger_hash": "GENESIS",
            "fingerprint": calculate_ledger_fingerprint(),
        }

    last_vote = votes[-1]

    return {
        "last_vote_id": last_vote[0],
        "ledger_hash": last_vote[6],
        "fingerprint": calculate_ledger_fingerprint(),
    }


# =========================================================
# CHECKPOINT PAYLOAD
# =========================================================

def build_checkpoint_hash(
    level,
    last_vote_id,
    ledger_hash,
    previous_checkpoint_hash,
    timestamp,
):

    payload = (
        f"{level}|"
        f"{last_vote_id}|"
        f"{ledger_hash}|"
        f"{previous_checkpoint_hash}|"
        f"{timestamp}"
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


# =========================================================
# SIGN CHECKPOINT
# =========================================================

def sign_checkpoint(
    level,
    checkpoint_hash,
):

    secret = LEVEL_SIGNING_SECRETS[level]

    return hmac.new(
        secret.encode("utf-8"),
        checkpoint_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# =========================================================
# VERIFY CHECKPOINT SIGNATURE
# =========================================================

def verify_checkpoint_signature(
    checkpoint
):

    level = checkpoint["level"]

    if level not in LEVEL_SIGNING_SECRETS:

        return False

    expected = sign_checkpoint(
        level,
        checkpoint["checkpoint_hash"],
    )

    return hmac.compare_digest(
        expected,
        checkpoint["signature"],
    )


# =========================================================
# CREATE / UPDATE ONE LEVEL CHECKPOINT
# =========================================================

def synchronize_level(level):

    if level not in ADMIN_LEVELS:

        raise ValueError(
            f"Unsupported administrative level: {level}"
        )

    state = get_current_ledger_state()

    current = get_checkpoint(level)

    if current is None:

        previous_checkpoint_hash = "GENESIS"

    else:

        previous_checkpoint_hash = (
            current["checkpoint_hash"]
            or "GENESIS"
        )

    timestamp = datetime.now().isoformat()

    checkpoint_hash = build_checkpoint_hash(
        level,
        state["last_vote_id"],
        state["ledger_hash"],
        previous_checkpoint_hash,
        timestamp,
    )

    signature = sign_checkpoint(
        level,
        checkpoint_hash,
    )

    save_checkpoint(
        level=level,
        last_vote_id=state["last_vote_id"],
        ledger_hash=state["ledger_hash"],
        previous_checkpoint_hash=(
            previous_checkpoint_hash
        ),
        checkpoint_hash=checkpoint_hash,
        signature=signature,
        timestamp=timestamp,
    )

    return {
        "level": level,
        "last_vote_id": state["last_vote_id"],
        "ledger_hash": state["ledger_hash"],
        "checkpoint_hash": checkpoint_hash,
        "signature": signature,
        "timestamp": timestamp,
    }


# =========================================================
# SYNCHRONIZE ALL FOUR LEVELS
# =========================================================

def synchronize_all_levels():

    results = []

    for level in ADMIN_LEVELS:

        results.append(
            synchronize_level(level)
        )

    return results


# =========================================================
# VERIFY FOUR-LEVEL SYNCHRONIZATION
# =========================================================

def verify_four_level_sync():

    checkpoints = get_all_checkpoints()

    checkpoint_map = {
        checkpoint[1]: {
            "checkpoint_id": checkpoint[0],
            "level": checkpoint[1],
            "last_vote_id": checkpoint[2],
            "ledger_hash": checkpoint[3],
            "previous_checkpoint_hash": checkpoint[4],
            "checkpoint_hash": checkpoint[5],
            "signature": checkpoint[6],
            "timestamp": checkpoint[7],
        }
        for checkpoint in checkpoints
    }

    alerts = []

    # -----------------------------------------------------
    # CHECK THAT ALL FOUR LEVELS EXIST
    # -----------------------------------------------------

    for level in ADMIN_LEVELS:

        if level not in checkpoint_map:

            alerts.append({
                "level": level,
                "type": "MISSING_CHECKPOINT",
                "message": (
                    f"{level} checkpoint is missing."
                ),
            })

    if alerts:

        return {
            "synchronized": False,
            "alerts": alerts,
            "checkpoints": checkpoint_map,
        }

    # -----------------------------------------------------
    # VERIFY EACH LEVEL'S SIGNATURE
    # -----------------------------------------------------

    for level in ADMIN_LEVELS:

        checkpoint = checkpoint_map[level]

        if not verify_checkpoint_signature(
            checkpoint
        ):

            alerts.append({
                "level": level,
                "type": "INVALID_SIGNATURE",
                "message": (
                    f"{level} checkpoint signature "
                    f"does not match."
                ),
            })

    # -----------------------------------------------------
    # COMPARE ALL LEVELS AGAINST CENTRAL
    # -----------------------------------------------------

    central = checkpoint_map["CENTRAL"]

    for level in ADMIN_LEVELS:

        checkpoint = checkpoint_map[level]

        if (
            checkpoint["last_vote_id"]
            != central["last_vote_id"]
        ):

            alerts.append({
                "level": level,
                "type": "VOTE_ID_MISMATCH",
                "message": (
                    f"{level} last vote ID does not "
                    f"match CENTRAL."
                ),
            })

        if (
            checkpoint["ledger_hash"]
            != central["ledger_hash"]
        ):

            alerts.append({
                "level": level,
                "type": "LEDGER_HASH_MISMATCH",
                "message": (
                    f"{level} ledger hash does not "
                    f"match CENTRAL."
                ),
            })

    # -----------------------------------------------------
    # ALSO CHECK CURRENT LEDGER AGAINST CHECKPOINTS
    # -----------------------------------------------------

    current_state = get_current_ledger_state()

    for level in ADMIN_LEVELS:

        checkpoint = checkpoint_map[level]

        if (
            checkpoint["last_vote_id"]
            != current_state["last_vote_id"]
            or
            checkpoint["ledger_hash"]
            != current_state["ledger_hash"]
        ):

            alerts.append({
                "level": level,
                "type": "STALE_CHECKPOINT",
                "message": (
                    f"{level} checkpoint does not "
                    f"represent the current ledger."
                ),
            })

    # -----------------------------------------------------
    # RECORD SECURITY EVENTS
    # -----------------------------------------------------

    for alert in alerts:

        add_security_event(
            source_level=alert["level"],
            event_type=alert["type"],
            severity="HIGH",
            details=alert["message"],
        )

    return {
        "synchronized": len(alerts) == 0,
        "alerts": alerts,
        "checkpoints": checkpoint_map,
    }


# =========================================================
# CENTRAL SECURITY SUMMARY
# =========================================================

def get_four_level_security_summary():

    result = verify_four_level_sync()

    status = {}

    for level in ADMIN_LEVELS:

        level_checkpoint = (
            result["checkpoints"]
            .get(level)
        )

        if level_checkpoint is None:

            status[level] = {
                "status": "MISSING",
                "last_vote_id": 0,
            }

            continue

        valid_signature = (
            verify_checkpoint_signature(
                level_checkpoint
            )
        )

        has_alert = any(
            alert["level"] == level
            for alert in result["alerts"]
        )

        if not valid_signature:

            level_status = "TAMPERED"

        elif has_alert:

            level_status = "MISMATCH"

        else:

            level_status = "SYNCED"

        status[level] = {
            "status": level_status,
            "last_vote_id": (
                level_checkpoint["last_vote_id"]
            ),
            "ledger_hash": (
                level_checkpoint["ledger_hash"]
            ),
        }

    return {
        "overall": (
            "SECURE"
            if result["synchronized"]
            else "ALERT"
        ),
        "levels": status,
        "alerts": result["alerts"],
    }