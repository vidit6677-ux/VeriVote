"""
VeriVote FastAPI backend.

The API exposes the existing VeriVote service layer.
Business logic is not duplicated inside the API.
"""

import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database import get_admin_audit_logs, get_connection, get_voter, initialize_database
from data.demo_voters import load_demo_voters
from services.admin_security import seed_demo_admin_accounts
from services.admin_2fa import verify_totp
from services.replication_service import retry_pending_replication
from services.privacy_service import issue_one_time_ballot, submit_tokenized_ballot
from services.voting_service import cast_vote
from services.four_level_sync import get_four_level_security_summary
from api.replay import vote_replay_guard
from api.rate_limit import sensitive_rate_limiter
from api.security import DEMO_MODE, authenticate, require_roles


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create required SQLite tables before serving requests."""
    initialize_database()
    if DEMO_MODE:
        seed_demo_admin_accounts()
        load_demo_voters()
    yield


app = FastAPI(
    title="VeriVote API",
    description="Backend API for the VeriVote security prototype.",
    version="1.0.0",
    lifespan=lifespan,
)

logger = logging.getLogger("verivote.api")


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    sensitive_path = (
        request.url.path.startswith("/auth/")
        or request.url.path.startswith("/votes")
        or request.url.path.startswith("/ballots/")
    )
    if sensitive_path:
        client_host = request.client.host if request.client else "unknown"
        if not sensitive_rate_limiter.allow(f"{client_host}:{request.url.path}"):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Try again later."},
                headers={"Retry-After": "60", "X-Request-ID": request_id},
            )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(json.dumps({
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
    }))
    return response


class VoteRequest(BaseModel):
    voter_identity: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    constituency: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    candidate: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)
    role: str = Field(..., min_length=1, max_length=16)
    otp: str | None = Field(default=None, min_length=6, max_length=6)


class BallotIssueRequest(BaseModel):
    voter_identity: str = Field(..., min_length=1, max_length=100)
    constituency: str = Field(..., min_length=1, max_length=100)


class PrivateBallotRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=256)
    candidate: str = Field(..., min_length=1, max_length=100)


IDEMPOTENCY_KEY_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$"


def reject_replayed_request(claim_status: str) -> None:
    if claim_status == "duplicate":
        raise HTTPException(
            status_code=409,
            detail="This idempotency key has already been used for the same request.",
        )
    if claim_status == "conflict":
        raise HTTPException(
            status_code=409,
            detail="An idempotency key cannot be reused for a different request.",
        )


@app.get("/")
def root():
    return {
        "application": "VeriVote",
        "status": "running",
        "api": "fastapi",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "verivote-api",
    }


@app.post("/auth/login")
def login(request: LoginRequest):
    result = authenticate(request.username, request.password, request.role)

    # Production Central API access requires the same second factor as the
    # GUI. Demo mode remains compatible with the classroom credentials.
    if (
        request.role.upper() == "CENTRAL"
        and not DEMO_MODE
    ):
        if request.otp is None:
            raise HTTPException(status_code=401, detail="Central API OTP required.")
        valid, message = verify_totp(request.username, request.otp)
        if not valid:
            raise HTTPException(status_code=401, detail=message)

    return result


@app.post("/ballots/issue")
def issue_ballot(
    request: BallotIssueRequest,
    principal: dict = Depends(require_roles("BOOTH", "ZONAL", "DEPUTY", "CENTRAL")),
):
    token, message = issue_one_time_ballot(
        request.voter_identity,
        request.constituency,
    )
    if token is None:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message, "ballot_token": token}


@app.post("/ballots/cast")
def cast_tokenized_ballot(
    request: PrivateBallotRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=8,
        max_length=128,
        pattern=IDEMPOTENCY_KEY_PATTERN,
    ),
):
    reject_replayed_request(
        vote_replay_guard.claim(idempotency_key, request.model_dump_json(), "private-ballot")
    )
    result = submit_tokenized_ballot(request.token, request.candidate)
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.get("/ready")
def readiness():
    """Return whether the API can reach its operational database."""
    connection = get_connection()
    try:
        connection.execute("SELECT 1")
    finally:
        connection.close()

    return {
        "status": "ready",
        "database": "healthy",
    }


@app.get("/integrity/status")
def integrity_status(principal: dict = Depends(require_roles("CENTRAL"))):
    """Expose the existing four-level integrity summary read-only."""
    return get_four_level_security_summary()


@app.get("/admin/audit")
def admin_audit(
    role: str | None = None,
    action: str | None = None,
    status: str | None = None,
    limit: int = 100,
    principal: dict = Depends(require_roles("CENTRAL")),
):
    """Return filtered Central audit records for monitoring tools."""
    bounded_limit = max(1, min(limit, 1000))
    rows = get_admin_audit_logs(
        limit=bounded_limit,
        role=role,
        action=action,
        status=status,
    )
    return {
        "count": len(rows),
        "records": [
            {
                "audit_id": row[0],
                "username": row[1],
                "role": row[2],
                "action": row[3],
                "details": row[4],
                "status": row[5],
                "timestamp": row[6],
            }
            for row in rows
        ],
    }


@app.post("/integrity/replication/retry")
def retry_replication(principal: dict = Depends(require_roles("CENTRAL"))):
    return {"results": retry_pending_replication()}


@app.get("/voters/{identity}")
def read_voter(
    identity: str,
    principal: dict = Depends(require_roles("BOOTH", "ZONAL", "DEPUTY", "CENTRAL")),
):
    voter = get_voter(identity)

    if voter is None:
        raise HTTPException(
            status_code=404,
            detail="Voter not found.",
        )

    return voter


@app.post("/votes")
def create_vote(
    request: VoteRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=8,
        max_length=128,
        pattern=IDEMPOTENCY_KEY_PATTERN,
    ),
    principal: dict = Depends(require_roles("BOOTH", "ZONAL", "DEPUTY", "CENTRAL")),
):
    reject_replayed_request(
        vote_replay_guard.claim(idempotency_key, request.model_dump_json(), "vote")
    )
    result = cast_vote(
        request.voter_identity,
        request.constituency,
        request.candidate,
    )

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Vote could not be recorded.",
            ),
        )

    return result


# Versioned aliases keep existing demo URLs working while giving clients a
# stable namespace for future API evolution.
app.add_api_route("/api/v1/health", health, methods=["GET"], include_in_schema=False)
app.add_api_route("/api/v1/ready", readiness, methods=["GET"], include_in_schema=False)
app.add_api_route("/api/v1/auth/login", login, methods=["POST"])
app.add_api_route("/api/v1/voters/{identity}", read_voter, methods=["GET"])
app.add_api_route("/api/v1/votes", create_vote, methods=["POST"])
app.add_api_route("/api/v1/integrity/status", integrity_status, methods=["GET"])
