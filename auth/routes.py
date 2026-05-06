from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.auth.schema import LoginRequest, Token, UserOut, RegisterRequest
from backend.auth.utils import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    bearer_scheme,
    get_current_user,
    get_user_from_token_payload,
    revoke_access_token,
    safe_verify_token,
    store_refresh_token,
    revoke_refresh_token,
    is_refresh_token_valid,
)
from backend.database import get_db
from backend.users.models import User

class LoginResponse(Token):
    user: UserOut


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, credentials.identifier, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {"sub": user.username, "user_id": user.id, "role": user.role}
    access_token = create_access_token(token_payload)
    refresh_token, refresh_expires_at = create_refresh_token(token_payload)
    store_refresh_token(db, refresh_token, int(user.id), refresh_expires_at) #type: ignore

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, #type: ignore
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserOut.from_orm(user),
    }


@router.post("/register", response_model=UserOut)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    from backend.auth.utils import get_password_hash
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=get_password_hash(user_data.password),
        role=user_data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserOut.from_orm(new_user)


@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise credentials_exception

    token_data = safe_verify_token(refresh_token)
    if token_data is None:
        raise credentials_exception

    if not is_refresh_token_valid(db, refresh_token):
        raise credentials_exception

    user = get_user_from_token_payload(db, token_data)
    if not user:
        raise credentials_exception

    revoke_refresh_token(db, refresh_token)
    access_token = create_access_token(
        {"sub": user.username, "user_id": user.id, "role": user.role}
    )
    new_refresh_token, refresh_expires_at = create_refresh_token(
        {"sub": user.username, "user_id": user.id, "role": user.role}
    )
    store_refresh_token(db, new_refresh_token, user.id, refresh_expires_at) #type: ignore

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, #type: ignore
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        revoke_refresh_token(db, refresh_token)

    access_token = credentials.credentials if credentials else None
    if access_token:
        token_data = safe_verify_token(access_token)
        user = get_user_from_token_payload(db, token_data) if token_data else None
        revoke_access_token(db, access_token, user.id if user else None)

    response.delete_cookie("refresh_token", path="/")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
