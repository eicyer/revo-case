import secrets
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.config import settings
from app.auth import create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Constant-time comparison to dodge timing attacks
    user_ok = secrets.compare_digest(form_data.username, settings.ADMIN_USERNAME)
    pass_ok = secrets.compare_digest(form_data.password, settings.ADMIN_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=form_data.username)
    return TokenResponse(access_token=token)