import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List

import bcrypt as _bcrypt_lib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import User, UserRole
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserSchema, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

# ── Password hashing (bcrypt direct — avoids passlib/bcrypt4 compat issue) ───
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "clm-jwt-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

logger.info("AUTH_SECRET_KEY loaded (first 8 chars): %s", SECRET_KEY[:8])


def _hash_password(plain: str) -> str:
    return _bcrypt_lib.hashpw(plain.encode("utf-8"), _bcrypt_lib.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt_lib.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_access_token(user_id: int, email: str, role: str) -> str:
    from jose import jwt
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),   # JWT spec: sub must be a string
        "email": email,
        "role": str(role),     # explicit str — avoid enum serialisation quirks
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _get_current_user_from_token(token: str, db: Session) -> User:
    """Decode JWT and return the User row. Raises 401 on failure."""
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = int(user_id_str)
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except (ValueError, TypeError) as exc:
        logger.warning("JWT sub parsing failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def _require_admin(token: str, db: Session) -> User:
    user = _get_current_user_from_token(token, db)
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def _get_token_from_header(authorization: str = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    return authorization[7:]


# ── Dependency helpers ────────────────────────────────────────────────────────

from fastapi import Header


def get_token(authorization: str = Header(default=None)) -> str:
    return _get_token_from_header(authorization)


def current_user(authorization: str = Header(default=None), db: Session = Depends(get_db)) -> User:
    token = _get_token_from_header(authorization)
    return _get_current_user_from_token(token, db)


def admin_user(authorization: str = Header(default=None), db: Session = Depends(get_db)) -> User:
    token = _get_token_from_header(authorization)
    return _require_admin(token, db)


# ── Seed first admin on startup ───────────────────────────────────────────────

def seed_default_admin(db: Session) -> None:
    """Create a default admin account if no users exist."""
    if db.query(User).count() == 0:
        admin = User(
            email="admin@clm.local",
            full_name="System Admin",
            hashed_password=_hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not _verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = _create_access_token(user.id, user.email, str(user.role))
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        premium_access=bool(getattr(user, "premium_access", True)),
    )


@router.get("/me", response_model=UserSchema)
def me(user: User = Depends(current_user)):
    return user


# ── User management (admin only) ──────────────────────────────────────────────

@router.get("/users", response_model=List[UserSchema])
def list_users(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=_hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: int, payload: UserUpdate, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.premium_access is not None:
        user.premium_access = payload.premium_access
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    db.delete(user)
    db.commit()
