"""
Who is calling, and what they may see.

- get_current_user: verifies the Supabase login token and loads/creates the profile.
- Role 'clinician' is granted only when the account was created with the secret
  CLINICIAN_INVITE_CODE (sent as Supabase user metadata); everyone else is 'parent'.
- check_child_access: parents reach only children they own; clinicians reach all.
"""
import os
import hmac
from dataclasses import dataclass
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.auth.supabase_token import verify_access_token, TokenError
from src.db.connection import get_db

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    email: Optional[str]
    role: str

    @property
    def is_clinician(self) -> bool:
        return self.role == "clinician"


def has_valid_clinician_invite(user_metadata: Dict[str, Any]) -> bool:
    expected = os.getenv("CLINICIAN_INVITE_CODE", "")
    given = str(user_metadata.get("clinician_invite_code", ""))
    return bool(expected) and hmac.compare_digest(given.encode(), expected.encode())


async def _load_or_create_profile(user_id: str, email: Optional[str], user_metadata: Dict[str, Any]) -> str:
    async with get_db() as db:
        async with db.execute("SELECT role FROM profiles WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        current = row["role"] if row else None
        role = "clinician" if current == "clinician" or has_valid_clinician_invite(user_metadata) else "parent"
        if role != current:
            await db.execute("""
                INSERT INTO profiles (user_id, email, role) VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET role = excluded.role, email = excluded.email
            """, (user_id, email, role))
            await db.commit()
    return role


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Please sign in.")
    try:
        claims = await verify_access_token(credentials.credentials)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = claims["sub"]
    email = claims.get("email")
    role = await _load_or_create_profile(user_id, email, claims.get("user_metadata") or {})
    return CurrentUser(user_id=user_id, email=email, role=role)


async def require_clinician(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_clinician:
        raise HTTPException(status_code=403, detail="Only clinicians can do this.")
    return user


async def check_child_access(db, child_id: str, user: CurrentUser, allow_new: bool = False) -> bool:
    """Return True if the child exists and the user may use it, False if it does not exist
    and allow_new is set. Otherwise raise 404 (also for other families' children, so IDs
    cannot be probed) or 409 when trying to create an ID that is already taken."""
    async with db.execute("SELECT owner_id FROM children WHERE child_id = ?", (child_id,)) as cursor:
        row = await cursor.fetchone()

    if row is None:
        if allow_new:
            return False
        raise HTTPException(status_code=404, detail=f"No child found with ID {child_id}.")

    if user.is_clinician or row["owner_id"] == user.user_id:
        return True

    if allow_new:
        raise HTTPException(status_code=409, detail="This Child ID is already in use. Please choose another ID.")
    raise HTTPException(status_code=404, detail=f"No child found with ID {child_id}.")
