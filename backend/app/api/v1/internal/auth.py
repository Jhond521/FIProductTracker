from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts import security
from app.accounts.dependencies import get_current_user
from app.accounts.models import User
from app.accounts.schemas import GoogleAuthRequest, UserRead
from app.core.config import settings
from app.core.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=settings.environment != "dev",
        path="/",
    )


@router.post("/google", response_model=UserRead)
async def google_sign_in(
    payload: GoogleAuthRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        profile = security.verify_google_id_token(payload.credential)
    except security.InvalidGoogleTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token"
        ) from exc

    result = await db.execute(select(User).where(User.google_sub == profile.sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_sub=profile.sub,
            email=profile.email,
            name=profile.name,
            picture_url=profile.picture,
        )
        db.add(user)
    else:
        user.email = profile.email
        user.name = profile.name
        user.picture_url = profile.picture

    await db.commit()
    await db.refresh(user)

    token = security.create_session_token(user.id)
    _set_session_cookie(response, token)
    return user


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key=settings.session_cookie_name, path="/")
