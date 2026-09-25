from fastapi.testclient import TestClient

import api.main as api_main
from api.main import app
from database import add_demo_voter, get_connection, initialize_database
from data.demo_voters import load_demo_voters
from services.admin_security import seed_demo_admin_accounts


client = TestClient(app)
initialize_database()
seed_demo_admin_accounts()
load_demo_voters()


def token(username="booth01", password="Booth@2026", role="BOOTH"):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password, "role": role},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness():
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "healthy",
    }


def test_existing_voter():
    response = client.get(
        "/voters/647162579350",
        headers={"Authorization": f"Bearer {token()}"},
    )

    assert response.status_code == 200
    assert response.json()["identity"] == "647162579350"


def test_missing_voter():
    response = client.get(
        "/voters/DOES-NOT-EXIST",
        headers={"Authorization": f"Bearer {token()}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Voter not found."


def test_invalid_constituency():
    response = client.post(
        "/votes",
        headers={
            "Authorization": f"Bearer {token()}",
            "Idempotency-Key": "invalid-constituency-1",
        },
        json={
            "voter_identity": "647162579350",
            "constituency": "INVALID-CONSTITUENCY",
            "candidate": "DemoCandidate",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Constituency mismatch."


def test_sensitive_endpoint_requires_authentication():
    response = client.get("/voters/647162579350")

    assert response.status_code == 401


def test_integrity_requires_central_role():
    response = client.get(
        "/integrity/status",
        headers={"Authorization": f"Bearer {token()}"},
    )

    assert response.status_code == 403


def test_replication_retry_requires_central_role():
    response = client.post(
        "/integrity/replication/retry",
        headers={"Authorization": f"Bearer {token()}"},
    )

    assert response.status_code == 403


def test_central_can_retry_replication():
    response = client.post(
        "/integrity/replication/retry",
        headers={
            "Authorization": f"Bearer {token('central01', 'Central@2026!Secure', 'CENTRAL')}"
        },
    )

    assert response.status_code == 200
    assert "results" in response.json()


def test_integrity_endpoint_uses_four_level_sync_summary():
    assert api_main.get_four_level_security_summary.__module__ == "services.four_level_sync"

    response = client.get(
        "/integrity/status",
        headers={
            "Authorization": f"Bearer {token('central01', 'Central@2026!Secure', 'CENTRAL')}"
        },
    )

    assert response.status_code == 200
    assert {"overall", "levels", "alerts"} <= response.json().keys()


def test_private_ballot_issue_returns_one_time_token():
    identity = "PRIVACY-TEST-VOTER"
    add_demo_voter(identity, "Privacy Test Voter", "Privacy City", "")
    try:
        response = client.post(
            "/ballots/issue",
            headers={"Authorization": f"Bearer {token()}"},
            json={"voter_identity": identity, "constituency": "Privacy City"},
        )

        assert response.status_code == 200
        assert len(response.json()["ballot_token"]) >= 20
    finally:
        connection = get_connection()
        try:
            connection.execute("DELETE FROM ballot_issuances WHERE voter_identity = ?", (identity,))
            connection.execute("DELETE FROM voters WHERE identity = ?", (identity,))
            connection.commit()
        finally:
            connection.close()


def test_private_ballot_rejects_invalid_token():
    response = client.post(
        "/ballots/cast",
        headers={"Idempotency-Key": "private-invalid-token-1"},
        json={"token": "invalid-token-value-that-is-long-enough", "candidate": "DemoCandidate"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid ballot token."


def test_vote_replay_is_rejected():
    headers = {
        "Authorization": f"Bearer {token()}",
        "Idempotency-Key": "replay-test-key-1",
    }
    payload = {
        "voter_identity": "647162579350",
        "constituency": "INVALID-CONSTITUENCY",
        "candidate": "DemoCandidate",
    }

    first = client.post("/votes", json=payload, headers=headers)
    second = client.post("/votes", json=payload, headers=headers)

    assert first.status_code == 400
    assert second.status_code == 409
    assert "same request" in second.json()["detail"]


def test_idempotency_key_cannot_be_reused_for_a_different_payload():
    headers = {
        "Authorization": f"Bearer {token()}",
        "Idempotency-Key": "payload-conflict-key-1",
    }
    first = client.post(
        "/votes",
        json={
            "voter_identity": "647162579350",
            "constituency": "INVALID-CONSTITUENCY",
            "candidate": "Candidate-A",
        },
        headers=headers,
    )
    second = client.post(
        "/votes",
        json={
            "voter_identity": "647162579350",
            "constituency": "INVALID-CONSTITUENCY",
            "candidate": "Candidate-B",
        },
        headers=headers,
    )

    assert first.status_code == 400
    assert second.status_code == 409
    assert "different request" in second.json()["detail"]
