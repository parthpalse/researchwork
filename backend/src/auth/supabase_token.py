"""
Verifies Supabase Auth access tokens (JWTs) offline with the project's public keys.

Supabase signs tokens with an asymmetric key (ES256/RS256) and publishes the public
keys at <SUPABASE_URL>/auth/v1/.well-known/jwks.json — no shared secret is needed.
"""
import os
import asyncio
from typing import Dict, Any, Optional

import jwt
from jwt import PyJWKClient

ALGORITHMS = ["ES256", "RS256"]
AUDIENCE = "authenticated"

_jwks_client: Optional[PyJWKClient] = None
_jwks_url: Optional[str] = None


class TokenError(Exception):
    """The token is missing, expired, forged or for another project."""


def supabase_url() -> Optional[str]:
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    # Accept the REST URL people often copy (…supabase.co/rest/v1/)
    return url.removesuffix("/rest/v1") or None


def _client(base_url: str) -> PyJWKClient:
    global _jwks_client, _jwks_url
    url = f"{base_url}/auth/v1/.well-known/jwks.json"
    if _jwks_client is None or _jwks_url != url:
        _jwks_client = PyJWKClient(url, cache_keys=True, lifespan=3600, timeout=10)
        _jwks_url = url
    return _jwks_client


async def verify_access_token(token: str) -> Dict[str, Any]:
    """Return the token's claims, or raise TokenError."""
    base_url = supabase_url()
    if not base_url:
        raise TokenError("Login is not configured on the server (SUPABASE_URL missing).")
    try:
        # Key fetch is blocking network I/O on a cache miss: keep it off the event loop
        signing_key = await asyncio.to_thread(_client(base_url).get_signing_key_from_jwt, token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=ALGORITHMS,
            audience=AUDIENCE,
            issuer=f"{base_url}/auth/v1",
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except jwt.PyJWTError as e:
        raise TokenError(f"Invalid or expired login ({type(e).__name__}).") from e
