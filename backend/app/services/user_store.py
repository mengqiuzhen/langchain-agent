from __future__ import annotations

import time

from sqlalchemy.orm import Session

from backend.app.models import User


class UserStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_user(self, email: str) -> dict | None:
        target = email.strip().lower()
        row = self.db.query(User).filter(User.email == target).first()
        if not row:
            return None
        return {
            "email": row.email,
            "password_hash": row.password_hash,
            "role": row.role,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def upsert_user(self, *, email: str, password_hash: str, role: str, is_active: bool = True) -> dict:
        target = email.strip().lower()
        now = int(time.time())
        row = self.db.query(User).filter(User.email == target).first()

        if row:
            row.password_hash = password_hash
            row.role = role
            row.is_active = is_active
            row.updated_at = now
            self.db.commit()
            self.db.refresh(row)
        else:
            row = User(
                email=target,
                password_hash=password_hash,
                role=role,
                is_active=is_active,
                created_at=now,
                updated_at=now,
            )
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)

        return {
            "email": row.email,
            "password_hash": row.password_hash,
            "role": row.role,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def list_users(self) -> list[dict]:
        rows = self.db.query(User).order_by(User.created_at.desc()).all()
        return [
            {
                "email": row.email,
                "role": row.role,
                "is_active": row.is_active,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def ensure_admin(self, *, email: str, password_hash: str) -> None:
        existing = self.find_user(email)
        if existing:
            return
        self.upsert_user(email=email, password_hash=password_hash, role="admin", is_active=True)
