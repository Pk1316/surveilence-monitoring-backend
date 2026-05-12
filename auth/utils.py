from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import hashlib
import secrets
import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..users import models
from .models import RefreshToken, RevokedAccessToken

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY","")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be configured")

bearer_scheme = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, stored_password: str) -> bool:
    if not stored_password:
        return False

    if stored_password.startswith("$2"):
        try:
            password_bytes = plain_password.encode("utf-8")[:72]
            return bcrypt.checkpw(password_bytes, stored_password.encode("utf-8"))
        except ValueError:
            return False

    return plain_password == stored_password


def get_user_by_identifier(db: Session, identifier: str):
    return db.query(models.User).filter(
        or_(models.User.username == identifier, models.User.email == identifier),
    ).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_from_token_payload(db: Session, payload: dict):
    subject = payload.get("sub")
    user_id = payload.get("user_id")
    email = payload.get("email")

    if user_id is not None:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            return user

    if subject is not None:
        user = get_user_by_username(db, str(subject))
        if user:
            return user

        try:
            user = db.query(models.User).filter(models.User.id == int(subject)).first()
            if user:
                return user
        except (TypeError, ValueError):
            pass

    if email:
        return db.query(models.User).filter(models.User.email == email).first()

    return None


def authenticate_user(db: Session, identifier: str, password: str):
    user = get_user_by_identifier(db, identifier)
    if not user:
        return None
    stored_password = user.password
    if isinstance(stored_password, (bytes, bytearray)):
        stored_password = stored_password.decode("utf-8", errors="ignore")
    if not verify_password(password, str(stored_password)):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": secrets.token_urlsafe(32)})
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": secrets.token_urlsafe(32)})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, expire


def get_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def store_refresh_token(db: Session, token: str, user_id: int, expires_at: datetime):
    token_hash = get_token_hash(token)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    refresh_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def is_refresh_token_valid(db: Session, token: str) -> bool:
    token_hash = get_token_hash(token)
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if bool(not refresh_token or refresh_token.is_revoked):
        return False
   
    expires_at = refresh_token.expires_at #type: ignore
    if expires_at.tzinfo is None:
        
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    if(bool(expires_at <current_time)):
        return False
    return True


def revoke_refresh_token(db: Session, token: str):
    token_hash = get_token_hash(token)
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if (refresh_token and not refresh_token.is_revoked): #type:ignore
        refresh_token.is_revoked = True #type: ignore
        db.commit()
    return refresh_token


def is_access_token_revoked(db: Session, token: str) -> bool:
    token_hash = get_token_hash(token)
    return db.query(RevokedAccessToken).filter(
        RevokedAccessToken.token_hash == token_hash,
    ).first() is not None


def revoke_access_token(db: Session, token: str, user_id: int | None = None):
    payload = safe_decode_token(token)
    if not payload:
        return None

    resolved_user_id = user_id or payload.get("user_id")
    if resolved_user_id is None:
        return None

    token_hash = get_token_hash(token)
    if db.query(RevokedAccessToken).filter(RevokedAccessToken.token_hash == token_hash).first():
        return None

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    revoked_token = RevokedAccessToken(
        token_hash=token_hash,
        user_id=resolved_user_id,
        expires_at=expires_at,
    )
    db.add(revoked_token)
    db.commit()
    db.refresh(revoked_token)
    return revoked_token


def safe_decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None or payload.get("exp") is None:
            return None
        return payload
    except JWTError:
        return None


def safe_verify_token(token: str) -> dict | None:
    payload = safe_decode_token(token)
    if payload is None:
        return None
    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    access_token = credentials.credentials if credentials else None

    if not access_token or is_access_token_revoked(db, access_token):
        raise credentials_exception

    token_data = safe_verify_token(access_token)
    if token_data is None:
        raise credentials_exception

    user = get_user_from_token_payload(db, token_data)

    if user is None:
        raise credentials_exception

    return user
