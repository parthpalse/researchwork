import os

from fastapi import APIRouter, Depends
from src.auth.supabase_token import supabase_url
from src.auth.users import CurrentUser, get_current_user

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/config")
async def public_config():
    """Public settings the website needs to show the login screen.
    The publishable key is meant to be public; data access is enforced by this API."""
    return {
        "supabase_url": supabase_url(),
        "supabase_publishable_key": os.getenv("SUPABASE_PUBLISHABLE_KEY", "") or None,
    }


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return {"user_id": user.user_id, "email": user.email, "role": user.role}
