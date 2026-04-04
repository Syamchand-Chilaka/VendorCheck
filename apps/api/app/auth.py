"""Cognito JWT verification.

Fetches JWKS from Cognito on first request, caches keys in memory.
Verifies token signature (RS256), audience, and issuer.
"""

from __future__ import annotations

import httpx
from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwk, jwt

from app.config import Settings, get_settings

_jwks_cache: dict | None = None


def _get_jwks(settings: Settings) -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    resp = httpx.get(settings.cognito_jwks_url, timeout=10)
    resp.raise_for_status()
    _jwks_cache = resp.json()
    return _jwks_cache


def clear_jwks_cache() -> None:
    """Clear JWKS cache. Used in tests."""
    global _jwks_cache
    _jwks_cache = None


def _find_key(kid: str, jwks: dict) -> dict | None:
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            return key
    return None


def verify_token(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Verify Cognito JWT and return decoded token payload.

    Returns dict with at least: sub, email, token_use.
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.removeprefix("Bearer ")

    try:
        # Decode header to find kid
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")
        if not kid:
            raise HTTPException(
                status_code=401, detail="Invalid token: missing kid")

        jwks = _get_jwks(settings)
        key_data = _find_key(kid, jwks)
        if key_data is None:
            # Refresh JWKS in case keys rotated
            clear_jwks_cache()
            jwks = _get_jwks(settings)
            key_data = _find_key(kid, jwks)
            if key_data is None:
                raise HTTPException(
                    status_code=401, detail="Invalid token: unknown signing key")

        payload = jwt.decode(
            token,
            key_data,
            algorithms=["RS256"],
            audience=settings.cognito_user_pool_client_id,
            issuer=settings.cognito_issuer,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=401, detail="Invalid token: missing sub claim")

    return payload
