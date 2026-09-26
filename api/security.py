"""JWT authentication and role-based authorization for the API."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services.admin_security import authenticate_admin

ALGORITHM = "HS256"
ISSUER = "verivote-api"
TOKEN_TTL_MINUTES = 15
DEMO_MODE = os.getenv("VERIVOTE_DEMO_MODE", "true").lower() == "true"
configured_secret = os.getenv("VERIVOTE_JWT_SECRET")
if not configured_secret and not DEMO_MODE:
    raise RuntimeError(
        "VERIVOTE_JWT_SECRET must be configured when VERIVOTE_DEMO_MODE is false."
    )
_RUNTIME_SECRET = configured_secret or secrets.token_urlsafe(32)
bearer = HTTPBearer(auto_error=False)


def issue_token(username: str, role: str) -> dict:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=TOKEN_TTL_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "iss": ISSUER,
        "iat": now,
        "exp": expires,
        "jti": secrets.token_urlsafe(16),
    }
    return {
        "access_token": jwt.encode(payload, _RUNTIME_SECRET, algorithm=ALGORITHM),
        "token_type": "bearer",  # nosec B105 -- OAuth token_type field, not a credential
        "expires_in": int((expires - now).total_seconds()),
        "role": role,
    }


def authenticate(username: str, password: str, role: str) -> dict:
    success, account, message = authenticate_admin(username, password, role)
    if not success or account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return issue_token(account["username"], account["role"])


def current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            _RUNTIME_SECRET,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
        )
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    if not payload.get("sub") or not payload.get("role"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_roles(*roles: str) -> Callable:
    allowed = {role.upper() for role in roles}

    def dependency(principal: dict = Depends(current_principal)) -> dict:
        if principal["role"].upper() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient administrative permissions.",
            )
        return principal

    return dependency
