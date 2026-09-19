from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from .config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AUTHORIZED_ADMINS,
    SUPER_USER_EMAIL,
    INACTIVITY_AUTO_DISABLE_ENABLED,
    INACTIVITY_DISABLE_DAYS,
)
from sqlalchemy.orm import Session
from .database import SessionLocal


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a token and record a successful login timestamp.

    This is intentionally the point at which last_login is updated so normal
    authenticated API traffic does not reset the inactivity timer.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    email = str(data.get("sub", "")).strip().lower()
    if email:
        try:
            from .models import User
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.email == email).first()
                if user and user.is_active:
                    user.last_login = datetime.utcnow()
                    user.disabled_at = None
                    user.disabled_reason = None
                    db.commit()
            finally:
                db.close()
        except Exception:
            # Token creation should not fail solely because login telemetry
            # could not be written.
            pass

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(authorization: str = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")

    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        email = email.strip().lower()

        db = SessionLocal()
        try:
            from .models import User
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized email")
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
        finally:
            db.close()

        return email
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
