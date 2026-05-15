from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import admin, auth, chat, knowledge, metrics
from backend.app.core.auth_security import hash_password
from backend.app.db import SessionLocal, init_db
from backend.app.services.app_state import get_vector_store
from backend.app.services.user_store import UserStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_vector_store()
    init_db()

    bootstrap_admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com").strip().lower()
    bootstrap_admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123456").strip()

    db = SessionLocal()
    try:
        user_store = UserStore(db)
        user_store.ensure_admin(
            email=bootstrap_admin_email,
            password_hash=hash_password(bootstrap_admin_password),
        )

        demo_users = [
            ("teacher1@example.com", "teacher123", "teacher"),
            ("teacher2@example.com", "teacher123", "teacher"),
            ("student1@example.com", "student123", "student"),
            ("student2@example.com", "student123", "student"),
            ("student3@example.com", "student123", "student"),
        ]
        for email, password, role in demo_users:
            if not user_store.find_user(email):
                user_store.upsert_user(
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=True,
                )
    finally:
        db.close()

    yield


app = FastAPI(
    title="AI Teaching Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
