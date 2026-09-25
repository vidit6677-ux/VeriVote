import sqlite3
from datetime import datetime

from config import (
    LEVEL_DATABASE_PATHS,
    LEVEL_SIGNING_SECRETS,
)

from database import get_all_votes

from services.level_database import (
    initialize_all_level_databases,
)
from services.crypto_service import (
    sha256_hex,
    sign_checkpoint as crypto_sign_checkpoint,
    verify_checkpoint as crypto_verify_checkpoint,
)


LEVELS = (
    "BOOTH",
    "ZONAL",
    "DEPUTY",
    "CENTRAL",
)


# =========================================================
# CONNECTION / STATE
# =========================================================

def _connect(level):

    level = str(level).upper()

    if level not in LEVEL_DATABASE_PATHS:
        raise ValueError(
            f"Unsupported level: {level}"
        )

    return sqlite3.connect(
        LEVEL_DATABASE_PATHS[level],
        timeout=10
    )


def _get_votes(level):

    connection = _connect(level)

    try:

        return connection.execute("""
            SELECT
                vote_id,
                voter_identity,
                constituency,
                candidate,
                timestamp,
                previous_hash,
                vote_hash
            FROM votes
            ORDER BY vote_id ASC
        """).fetchall()

    finally:
        connection.close()


def _ledger_fingerprint(votes):

    return sha256_hex(*(
        value
        for vote in votes
        for value in vote
    ))


def get_level_state(level):

    votes = _get_votes(level)

    if not votes:

        return {
            "last_vote_id": 0,
            "ledger_hash": "GENESIS",
            "fingerprint": _ledger_fingerprint(votes),
            "vote_count": 0,
        }

    last_vote = votes[-1]

    return {
        "last_vote_id": last_vote[0],
        "ledger_hash": last_vote[6],
        "fingerprint": _ledger_fingerprint(votes),
        "vote_count": len(votes),
    }


# =========================================================
# SIGNED SNAPSHOTS
# =========================================================

def _build_checkpoint_hash(
    level,
    last_vote_id,
    ledger_hash,
    fingerprint,
    timestamp,
):

    return sha256_hex(
        level,
        last_vote_id,
        ledger_hash,
        fingerprint,
        timestamp,
    )


def _sign(level, checkpoint_hash):

    return crypto_sign_checkpoint(
        level,
        checkpoint_hash,
        LEVEL_SIGNING_SECRETS[level],
    )


def _verify_signature(snapshot):

    level = snapshot["level"]

    if level not in LEVEL_SIGNING_SECRETS:
        return False

    return crypto_verify_checkpoint(
        level,
        snapshot["checkpoint_hash"],
        snapshot["signature"],
        LEVEL_SIGNING_SECRETS[level],
    )


def build_snapshot(level):

    state = get_level_state(level)
    timestamp = datetime.now().isoformat()

    checkpoint_hash = _build_checkpoint_hash(
        level,
        state["last_vote_id"],
        state["ledger_hash"],
        state["fingerprint"],
        timestamp,
    )

    return {
        "level": level,
        "last_vote_id": state["last_vote_id"],
        "ledger_hash": state["ledger_hash"],
        "fingerprint": state["fingerprint"],
        "vote_count": state["vote_count"],
        "checkpoint_hash": checkpoint_hash,
        "signature": _sign(
            level,
            checkpoint_hash,
        ),
        "timestamp": timestamp,
    }


# =========================================================
# LOCAL CHECKPOINTS
# =========================================================

def _get_local_checkpoint(level):

    connection = _connect(level)

    try:

        row = connection.execute("""
            SELECT
                level,
                last_vote_id,
                ledger_hash,
                fingerprint,
                checkpoint_hash,
                signature,
                updated_at
            FROM level_checkpoint
            WHERE id = 1
        """).fetchone()

    finally:
        connection.close()

    if row is None:
        return None

    return {
        "level": row[0],
        "last_vote_id": row[1],
        "ledger_hash": row[2],
        "fingerprint": row[3],
        "checkpoint_hash": row[4],
        "signature": row[5],
        "timestamp": row[6],
    }


def _save_local_checkpoint(level, snapshot):

    connection = _connect(level)

    try:

        connection.execute("""
            UPDATE level_checkpoint
            SET
                level = ?,
                last_vote_id = ?,
                ledger_hash = ?,
                fingerprint = ?,
                checkpoint_hash = ?,
                signature = ?,
                updated_at = ?
            WHERE id = 1
        """, (
            level,
            snapshot["last_vote_id"],
            snapshot["ledger_hash"],
            snapshot["fingerprint"],
            snapshot["checkpoint_hash"],
            snapshot["signature"],
            snapshot["timestamp"],
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# PEER CHECKPOINTS
# =========================================================

def _save_peer_snapshot(observer, snapshot):

    connection = _connect(observer)

    try:

        connection.execute("""
            INSERT INTO peer_checkpoints (
                peer_level,
                last_vote_id,
                ledger_hash,
                fingerprint,
                checkpoint_hash,
                signature,
                observed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(peer_level) DO UPDATE SET
                last_vote_id = excluded.last_vote_id,
                ledger_hash = excluded.ledger_hash,
                fingerprint = excluded.fingerprint,
                checkpoint_hash = excluded.checkpoint_hash,
                signature = excluded.signature,
                observed_at = excluded.observed_at
        """, (
            snapshot["level"],
            snapshot["last_vote_id"],
            snapshot["ledger_hash"],
            snapshot["fingerprint"],
            snapshot["checkpoint_hash"],
            snapshot["signature"],
            snapshot["timestamp"],
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _get_peer_snapshots(observer):

    connection = _connect(observer)

    try:

        rows = connection.execute("""
            SELECT
                peer_level,
                last_vote_id,
                ledger_hash,
                fingerprint,
                checkpoint_hash,
                signature,
                observed_at
            FROM peer_checkpoints
        """).fetchall()

    finally:
        connection.close()

    return {
        row[0]: {
            "level": row[0],
            "last_vote_id": row[1],
            "ledger_hash": row[2],
            "fingerprint": row[3],
            "checkpoint_hash": row[4],
            "signature": row[5],
            "timestamp": row[6],
        }
        for row in rows
    }


# =========================================================
# SECURITY EVENTS
# =========================================================

def _record_event(
    observer,
    source_level,
    event_type,
    details,
    severity="HIGH",
):

    connection = _connect(observer)

    try:

        # Avoid flooding one observer with the exact same event
        # repeatedly within the same minute.
        existing = connection.execute("""
            SELECT event_id
            FROM security_events
            WHERE source_level = ?
              AND event_type = ?
              AND details = ?
              AND timestamp >= ?
            ORDER BY event_id DESC
            LIMIT 1
        """, (
            source_level,
            event_type,
            details,
            datetime.now().replace(
                second=0,
                microsecond=0
            ).isoformat(),
        )).fetchone()

        if existing is None:

            connection.execute("""
                INSERT INTO security_events (
                    source_level,
                    event_type,
                    severity,
                    details,
                    timestamp,
                    acknowledged
                )
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                source_level,
                event_type,
                severity,
                details,
                datetime.now().isoformat(),
            ))

            connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# INITIAL TRUST ESTABLISHMENT
# =========================================================

def bootstrap_from_legacy_database():

    legacy_votes = get_all_votes()

    for level in LEVELS:

        current_votes = _get_votes(level)

        if current_votes:

            if current_votes != legacy_votes:

                raise RuntimeError(
                    f"{level} database is non-empty and differs "
                    "from the existing operational ledger."
                )

            continue

        connection = _connect(level)

        try:

            for vote in legacy_votes:

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
                """, vote)

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()


def establish_initial_trust():

    snapshots = {
        level: build_snapshot(level)
        for level in LEVELS
    }

    for level, snapshot in snapshots.items():

        _save_local_checkpoint(
            level,
            snapshot
        )

    for observer in LEVELS:

        for peer in LEVELS:

            _save_peer_snapshot(
                observer,
                snapshots[peer]
            )

    return snapshots


# =========================================================
# VERIFY EVERY DATABASE
# =========================================================

def verify_independent_databases():

    actual = {
        level: get_level_state(level)
        for level in LEVELS
    }

    alerts_by_observer = {
        level: []
        for level in LEVELS
    }

    # -----------------------------------------------------
    # EACH DATABASE CHECKS ITSELF
    # -----------------------------------------------------

    for observer in LEVELS:

        checkpoint = _get_local_checkpoint(
            observer
        )

        if checkpoint is None:

            alerts_by_observer[observer].append({
                "source_level": observer,
                "type": "MISSING_LOCAL_CHECKPOINT",
                "message": (
                    "Local checkpoint is missing."
                ),
            })

            continue

        if not _verify_signature(checkpoint):

            alerts_by_observer[observer].append({
                "source_level": observer,
                "type": "INVALID_LOCAL_SIGNATURE",
                "message": (
                    f"{observer} local checkpoint signature "
                    "is invalid."
                ),
            })

        current = actual[observer]

        if (
            checkpoint["last_vote_id"]
            != current["last_vote_id"]
            or
            checkpoint["ledger_hash"]
            != current["ledger_hash"]
            or
            checkpoint["fingerprint"]
            != current["fingerprint"]
        ):

            alerts_by_observer[observer].append({
                "source_level": observer,
                "type": "LOCAL_LEDGER_MISMATCH",
                "message": (
                    f"{observer} ledger no longer matches "
                    "its signed checkpoint."
                ),
            })

    # -----------------------------------------------------
    # EVERY DATABASE CHECKS EVERY PEER
    # -----------------------------------------------------

    for observer in LEVELS:

        peers = _get_peer_snapshots(
            observer
        )

        for peer in LEVELS:

            if peer == observer:
                continue

            snapshot = peers.get(peer)

            if snapshot is None:

                alerts_by_observer[observer].append({
                    "source_level": peer,
                    "type": "MISSING_PEER_CHECKPOINT",
                    "message": (
                        f"{observer} has no signed checkpoint "
                        f"for {peer}."
                    ),
                })

                continue

            if not _verify_signature(snapshot):

                alerts_by_observer[observer].append({
                    "source_level": peer,
                    "type": "INVALID_PEER_SIGNATURE",
                    "message": (
                        f"{observer} detected an invalid "
                        f"signature for {peer}."
                    ),
                })

                continue

            peer_state = actual[peer]

            if (
                snapshot["last_vote_id"]
                != peer_state["last_vote_id"]
                or
                snapshot["ledger_hash"]
                != peer_state["ledger_hash"]
                or
                snapshot["fingerprint"]
                != peer_state["fingerprint"]
            ):

                alerts_by_observer[observer].append({
                    "source_level": peer,
                    "type": "PEER_LEDGER_MISMATCH",
                    "message": (
                        f"{observer} detected that {peer} "
                        "no longer matches its signed snapshot."
                    ),
                })

    # -----------------------------------------------------
    # WRITE ALERTS INTO EACH OBSERVER'S OWN DB
    # -----------------------------------------------------

    for observer, alerts in alerts_by_observer.items():

        for alert in alerts:

            _record_event(
                observer=observer,
                source_level=alert["source_level"],
                event_type=alert["type"],
                details=alert["message"],
            )

    return {
        "synchronized": all(
            not alerts
            for alerts in alerts_by_observer.values()
        ),
        "alerts_by_observer": alerts_by_observer,
        "states": actual,
    }


# =========================================================
# ATOMIC FOUR-DATABASE VOTE REPLICATION
# =========================================================

def _state_from_votes(votes):

    if not votes:

        return {
            "last_vote_id": 0,
            "ledger_hash": "GENESIS",
            "fingerprint": _ledger_fingerprint(votes),
            "vote_count": 0,
        }

    last_vote = votes[-1]

    return {
        "last_vote_id": last_vote[0],
        "ledger_hash": last_vote[6],
        "fingerprint": _ledger_fingerprint(votes),
        "vote_count": len(votes),
    }


def replicate_vote_to_all_levels(
    vote_id,
    voter_identity,
    constituency,
    candidate,
    timestamp,
    previous_hash,
    vote_hash,
):
    """
    Replicate one already-committed operational vote into all
    four independent level databases.

    The four SQLite files are attached to one SQLite connection so
    the vote rows, local checkpoints, and peer observations are
    committed in one SQLite transaction on the same host.

    Existing identical rows are treated as idempotent. Conflicting
    rows or duplicate voter identities cause the transaction to fail.
    """

    initialize_all_level_databases()

    preflight = verify_independent_databases()

    if not preflight["synchronized"]:

        raise RuntimeError(
            "Four-level replication blocked because the independent "
            "databases are not currently synchronized. Investigate "
            "the reported integrity alerts before accepting another vote."
        )

    vote = (
        int(vote_id),
        str(voter_identity),
        str(constituency),
        str(candidate),
        str(timestamp),
        str(previous_hash),
        str(vote_hash),
    )

    aliases = {
        "BOOTH": "main",
        "ZONAL": "db_zonal",
        "DEPUTY": "db_deputy",
        "CENTRAL": "db_central",
    }

    connection = sqlite3.connect(
        LEVEL_DATABASE_PATHS["BOOTH"],
        timeout=10,
    )

    attached_aliases = []

    try:

        for level, alias in aliases.items():

            if level == "BOOTH":
                continue

            connection.execute(
                f"ATTACH DATABASE ? AS {alias}",
                (LEVEL_DATABASE_PATHS[level],),
            )

            attached_aliases.append(alias)

        connection.execute("BEGIN IMMEDIATE")

        # -------------------------------------------------
        # PRE-INSERT CONSISTENCY / IDEMPOTENCY CHECK
        # -------------------------------------------------

        for level, alias in aliases.items():

            existing = connection.execute(
                f"""
                SELECT
                    vote_id,
                    voter_identity,
                    constituency,
                    candidate,
                    timestamp,
                    previous_hash,
                    vote_hash
                FROM {alias}.votes
                WHERE vote_id = ?
                """,
                (vote_id,),
            ).fetchone()

            if existing is not None:

                if tuple(existing) != vote:

                    raise RuntimeError(
                        f"{level} database contains a conflicting "
                        f"record for vote_id {vote_id}."
                    )

                continue

            duplicate_voter = connection.execute(
                f"""
                SELECT vote_id
                FROM {alias}.votes
                WHERE voter_identity = ?
                LIMIT 1
                """,
                (voter_identity,),
            ).fetchone()

            if duplicate_voter is not None:

                raise RuntimeError(
                    f"{level} database already contains a vote for "
                    f"voter {voter_identity}."
                )

        # -------------------------------------------------
        # INSERT THE VOTE INTO ALL FOUR LEVEL DATABASES
        # -------------------------------------------------

        for level, alias in aliases.items():

            connection.execute(
                f"""
                INSERT OR IGNORE INTO {alias}.votes (
                    vote_id,
                    voter_identity,
                    constituency,
                    candidate,
                    timestamp,
                    previous_hash,
                    vote_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                vote,
            )

        # -------------------------------------------------
        # BUILD POST-VOTE SIGNED SNAPSHOTS
        # -------------------------------------------------

        snapshots = {}

        for level, alias in aliases.items():

            rows = connection.execute(
                f"""
                SELECT
                    vote_id,
                    voter_identity,
                    constituency,
                    candidate,
                    timestamp,
                    previous_hash,
                    vote_hash
                FROM {alias}.votes
                ORDER BY vote_id ASC
                """
            ).fetchall()

            state = _state_from_votes(rows)
            checkpoint_timestamp = datetime.now().isoformat()

            checkpoint_hash = _build_checkpoint_hash(
                level,
                state["last_vote_id"],
                state["ledger_hash"],
                state["fingerprint"],
                checkpoint_timestamp,
            )

            snapshots[level] = {
                "level": level,
                "last_vote_id": state["last_vote_id"],
                "ledger_hash": state["ledger_hash"],
                "fingerprint": state["fingerprint"],
                "vote_count": state["vote_count"],
                "checkpoint_hash": checkpoint_hash,
                "signature": _sign(
                    level,
                    checkpoint_hash,
                ),
                "timestamp": checkpoint_timestamp,
            }

        # -------------------------------------------------
        # UPDATE LOCAL CHECKPOINTS
        # -------------------------------------------------

        for level, alias in aliases.items():

            snapshot = snapshots[level]

            connection.execute(
                f"""
                UPDATE {alias}.level_checkpoint
                SET
                    level = ?,
                    last_vote_id = ?,
                    ledger_hash = ?,
                    fingerprint = ?,
                    checkpoint_hash = ?,
                    signature = ?,
                    updated_at = ?
                WHERE id = 1
                """,
                (
                    level,
                    snapshot["last_vote_id"],
                    snapshot["ledger_hash"],
                    snapshot["fingerprint"],
                    snapshot["checkpoint_hash"],
                    snapshot["signature"],
                    snapshot["timestamp"],
                ),
            )

        # -------------------------------------------------
        # UPDATE PEER OBSERVATIONS
        # -------------------------------------------------

        for observer, observer_alias in aliases.items():

            for peer in LEVELS:

                snapshot = snapshots[peer]

                connection.execute(
                    f"""
                    INSERT INTO {observer_alias}.peer_checkpoints (
                        peer_level,
                        last_vote_id,
                        ledger_hash,
                        fingerprint,
                        checkpoint_hash,
                        signature,
                        observed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(peer_level) DO UPDATE SET
                        last_vote_id = excluded.last_vote_id,
                        ledger_hash = excluded.ledger_hash,
                        fingerprint = excluded.fingerprint,
                        checkpoint_hash = excluded.checkpoint_hash,
                        signature = excluded.signature,
                        observed_at = excluded.observed_at
                    """,
                    (
                        snapshot["level"],
                        snapshot["last_vote_id"],
                        snapshot["ledger_hash"],
                        snapshot["fingerprint"],
                        snapshot["checkpoint_hash"],
                        snapshot["signature"],
                        snapshot["timestamp"],
                    ),
                )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        # DETACH is only valid after the transaction has ended.
        for alias in reversed(attached_aliases):

            try:
                connection.execute(
                    f"DETACH DATABASE {alias}"
                )
            except sqlite3.Error:
                pass

        connection.close()

    final_check = verify_independent_databases()

    if not final_check["synchronized"]:

        raise RuntimeError(
            "Vote replication committed, but the post-replication "
            "integrity verification reported an alert. Investigate "
            "the four independent databases."
        )

    return snapshots


# =========================================================
# SAFE RESYNCHRONIZATION
# =========================================================

def synchronize_independent_databases():

    verification = verify_independent_databases()

    if not verification["synchronized"]:

        raise RuntimeError(
            "Synchronization blocked because a mismatch or "
            "tampering alert exists. Investigate the affected "
            "database before overwriting its evidence."
        )

    snapshots = {
        level: build_snapshot(level)
        for level in LEVELS
    }

    for level, snapshot in snapshots.items():

        _save_local_checkpoint(
            level,
            snapshot
        )

    for observer in LEVELS:

        for peer in LEVELS:

            _save_peer_snapshot(
                observer,
                snapshots[peer]
            )

    return snapshots

# =========================================================
# ADMIN DASHBOARD COMPATIBILITY SUMMARY
# =========================================================

def get_four_level_security_summary():

    result = verify_independent_databases()

    levels = {}

    for level in LEVELS:

        own_alerts = result["alerts_by_observer"].get(
            level,
            []
        )

        status = "SYNCED"

        if own_alerts:

            has_local_tamper = any(
                alert["source_level"] == level
                and alert["type"] in (
                    "LOCAL_LEDGER_MISMATCH",
                    "INVALID_LOCAL_SIGNATURE",
                    "MISSING_LOCAL_CHECKPOINT",
                )
                for alert in own_alerts
            )

            status = (
                "TAMPERED"
                if has_local_tamper
                else "MISMATCH"
            )

        levels[level] = {
            "status": status,
            "last_vote_id": result["states"][level]["last_vote_id"],
            "ledger_hash": result["states"][level]["ledger_hash"],
        }

    return {
        "overall": (
            "SECURE"
            if result["synchronized"]
            else "ALERT"
        ),
        "levels": levels,
        "alerts": result["alerts_by_observer"],
    }
