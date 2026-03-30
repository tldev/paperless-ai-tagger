import base64
import json
import logging
import time

import httpx

logger = logging.getLogger(__name__)

OAUTH_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
OAUTH_SCOPE = "user:profile user:inference user:sessions:claude_code user:mcp_servers user:file_upload"

# Refresh 5 minutes before expiry
EXPIRY_BUFFER_SECONDS = 300

# Module-level cache for the refreshed token
_cached_token: str | None = None
_cached_expiry: float = 0.0


def _decode_jwt_expiry(token: str) -> float | None:
    """Try to decode the expiry time from a JWT access token.

    Returns the 'exp' claim as a Unix timestamp, or None if the token
    is not a valid JWT or has no exp claim.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # JWT payload is the second part, base64url-encoded
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        exp = payload.get("exp")
        if exp is not None:
            return float(exp)
    except Exception:
        pass
    return None


def _refresh_token(refresh_token: str) -> tuple[str, float]:
    """Call the OAuth token refresh endpoint.

    Returns (new_access_token, expiry_unix_timestamp).
    """
    response = httpx.post(
        OAUTH_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": OAUTH_CLIENT_ID,
            "scope": OAUTH_SCOPE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15.0,
    )
    response.raise_for_status()
    data = response.json()

    new_access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    expiry = time.time() + expires_in

    logger.info("OAuth token refreshed, expires in %d seconds", expires_in)
    return new_access_token, expiry


def ensure_fresh_token(access_token: str, refresh_token: str | None) -> str:
    """Return a valid access token, refreshing if necessary.

    If no refresh_token is provided, returns access_token unchanged (backward
    compatible). Otherwise, checks expiry and refreshes proactively when the
    token is expired or within EXPIRY_BUFFER_SECONDS of expiry.
    """
    global _cached_token, _cached_expiry

    if not refresh_token:
        return access_token

    # If we have a cached token that's still valid, use it
    if _cached_token and time.time() < (_cached_expiry - EXPIRY_BUFFER_SECONDS):
        return _cached_token

    # Check if the current access token is still valid
    if not _cached_token:
        expiry = _decode_jwt_expiry(access_token)
        if expiry is not None and time.time() < (expiry - EXPIRY_BUFFER_SECONDS):
            _cached_token = access_token
            _cached_expiry = expiry
            return access_token

    # Token is expired or we can't determine expiry -- refresh it
    try:
        new_token, new_expiry = _refresh_token(refresh_token)
        _cached_token = new_token
        _cached_expiry = new_expiry
        return new_token
    except httpx.HTTPStatusError as e:
        logger.error("OAuth token refresh failed (HTTP %d): %s", e.response.status_code, e)
        # Fall back to the original token -- it might still work
        return _cached_token or access_token
    except Exception as e:
        logger.error("OAuth token refresh failed: %s", e)
        return _cached_token or access_token


def reset_cache():
    """Reset the module-level token cache. Useful for testing."""
    global _cached_token, _cached_expiry
    _cached_token = None
    _cached_expiry = 0.0
