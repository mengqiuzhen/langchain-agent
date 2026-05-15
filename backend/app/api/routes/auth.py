from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth_security import create_access_token, get_current_user, hash_password, require_roles, verify_password
from backend.app.deps import get_db
from backend.app.schemas.auth import (
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    AuthResponse,
    LoginRequest,
    MeResponse,
    UserItem,
)
from backend.app.services.user_store import UserStore

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = request.email.strip().lower()
    user_store = UserStore(db)
    user = user_store.find_user(email)
    if not user or not verify_password(request.password, str(user.get("password_hash", ""))):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not bool(user.get("is_active", True)):
        raise HTTPException(status_code=403, detail="账号已禁用，请联系管理员")

    token = create_access_token({"email": user["email"], "role": user["role"]})
    return AuthResponse(access_token=token, role=user["role"], email=user["email"])


@router.get("/me", response_model=MeResponse)
def me(user: dict = Depends(get_current_user)) -> MeResponse:
    return MeResponse(email=user["email"], role=user["role"])


@router.get("/users", response_model=list[UserItem])
def list_users(_: dict = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[UserItem]:
    user_store = UserStore(db)
    return [UserItem(**item) for item in user_store.list_users()]


@router.post("/users", response_model=UserItem)
def admin_create_user(
    request: AdminCreateUserRequest,
    _: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> UserItem:
    email = request.email.strip().lower()
    user_store = UserStore(db)
    if user_store.find_user(email):
        raise HTTPException(status_code=400, detail="该邮箱已存在")

    created = user_store.upsert_user(
        email=email,
        password_hash=hash_password(request.password),
        role=request.role,
        is_active=True,
    )

    return UserItem(
        email=created["email"],
        role=created["role"],
        is_active=bool(created.get("is_active", True)),
        created_at=int(created.get("created_at", 0)),
    )


@router.post("/users/reset-password")
def admin_reset_user_password(
    request: AdminResetPasswordRequest,
    _: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    email = request.email.strip().lower()
    user_store = UserStore(db)
    user = user_store.find_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_store.upsert_user(
        email=email,
        password_hash=hash_password(request.new_password),
        role=str(user.get("role", "student")),
        is_active=bool(user.get("is_active", True)),
    )
    return {"ok": True}
