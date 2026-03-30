import base64
import json
import time

import httpx
import pytest
import respx

from paperless_ai_tagger.oauth import (
    OAUTH_CLIENT_ID,
    OAUTH_SCOPE,
    OAUTH_TOKEN_URL,
    _decode_jwt_expiry,
    ensure_fresh_token,
    reset_cache,
)


def _make_jwt(exp: float) -> str:
    """Create a minimal JWT with a given exp claim."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b"=").decode()
    payload = (
        base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=").decode()
    )
    return f"{header}.{payload}.signature"


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset module-level token cache before each test."""
    reset_cache()
    yield
    reset_cache()


class TestDecodeJwtExpiry:
    def test_valid_jwt(self):
        exp = time.time() + 3600
        token = _make_jwt(exp)
        assert _decode_jwt_expiry(token) == exp

    def test_opaque_token(self):
        assert _decode_jwt_expiry("sk-ant-not-a-jwt-token") is None

    def test_jwt_without_exp(self):
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b"=")
        payload = base64.urlsafe_b64encode(json.dumps({"sub": "user"}).encode()).rstrip(b"=")
        token = f"{header.decode()}.{payload.decode()}.sig"
        assert _decode_jwt_expiry(token) is None

    def test_malformed_base64(self):
        assert _decode_jwt_expiry("a.!!!invalid!!!.c") is None


class TestEnsureFreshToken:
    def test_no_refresh_token_returns_access_token(self):
        """When no refresh token is configured, access token is returned as-is."""
        result = ensure_fresh_token("my-access-token", None)
        assert result == "my-access-token"

    def test_valid_jwt_not_expired_no_refresh(self):
        """A JWT access token that is still valid should be returned without refreshing."""
        exp = time.time() + 3600  # expires in 1 hour
        token = _make_jwt(exp)
        result = ensure_fresh_token(token, "my-refresh-token")
        assert result == token

    @respx.mock
    def test_expired_jwt_triggers_refresh(self):
        """An expired JWT should trigger a token refresh."""
        expired_token = _make_jwt(time.time() - 60)  # expired 1 minute ago

        respx.post(OAUTH_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "fresh-access-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
            )
        )

        result = ensure_fresh_token(expired_token, "my-refresh-token")
        assert result == "fresh-access-token"

    @respx.mock
    def test_near_expiry_triggers_refresh(self):
        """A token expiring within 5 minutes should trigger a refresh."""
        near_expiry_token = _make_jwt(time.time() + 120)  # expires in 2 minutes

        respx.post(OAUTH_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "fresh-token-2",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
            )
        )

        result = ensure_fresh_token(near_expiry_token, "my-refresh-token")
        assert result == "fresh-token-2"

    @respx.mock
    def test_cached_token_reused(self):
        """After a refresh, the cached token should be returned on subsequent calls."""
        expired_token = _make_jwt(time.time() - 60)

        route = respx.post(OAUTH_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "cached-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
            )
        )

        # First call refreshes
        result1 = ensure_fresh_token(expired_token, "my-refresh-token")
        assert result1 == "cached-token"
        assert route.call_count == 1

        # Second call uses cache
        result2 = ensure_fresh_token(expired_token, "my-refresh-token")
        assert result2 == "cached-token"
        assert route.call_count == 1  # No additional HTTP call

    @respx.mock
    def test_http_error_falls_back(self):
        """If the refresh endpoint returns an error, fall back to the original token."""
        expired_token = _make_jwt(time.time() - 60)

        respx.post(OAUTH_TOKEN_URL).mock(
            return_value=httpx.Response(401, json={"error": "invalid_grant"})
        )

        result = ensure_fresh_token(expired_token, "bad-refresh-token")
        # Should fall back to the original token
        assert result == expired_token

    @respx.mock
    def test_opaque_token_triggers_refresh(self):
        """An opaque (non-JWT) token with no cached state should trigger a refresh."""
        respx.post(OAUTH_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "refreshed-opaque",
                    "expires_in": 1800,
                    "token_type": "Bearer",
                },
            )
        )

        result = ensure_fresh_token("opaque-token-no-jwt", "my-refresh-token")
        assert result == "refreshed-opaque"

    @respx.mock
    def test_refresh_sends_correct_parameters(self):
        """Verify the refresh request sends the expected form parameters."""
        expired_token = _make_jwt(time.time() - 60)

        route = respx.post(OAUTH_TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={"access_token": "new", "expires_in": 3600},
            )
        )

        ensure_fresh_token(expired_token, "test-refresh-token")

        assert route.called
        request = route.calls.last.request
        body = request.content.decode()
        assert "grant_type=refresh_token" in body
        assert "refresh_token=test-refresh-token" in body
        assert f"client_id={OAUTH_CLIENT_ID}" in body
