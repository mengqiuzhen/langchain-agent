from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


ADMIN_TOKEN_ENV = "ADMIN_TOKEN"


def verify_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    configured_token = os.getenv(ADMIN_TOKEN_ENV, "").strip()
    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"服务端未配置管理员口令，请设置环境变量 {ADMIN_TOKEN_ENV}",
        )

    if not x_admin_token or x_admin_token.strip() != configured_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员鉴权失败")
