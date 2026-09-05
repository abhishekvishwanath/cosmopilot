from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def read_current_user(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Proves the Supabase Auth JWT verification path works end to end.
    Returns a minimal, non-sensitive subset of the token claims — full
    clinic-scoped user/staff records are added in Phase 2.
    """
    return {
        "sub": user.get("sub"),
        "email": user.get("email"),
        "role": user.get("role"),
        "aud": user.get("aud"),
    }
