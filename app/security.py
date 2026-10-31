import os
import secrets

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic = HTTPBasic(auto_error=False)


def same(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())


def require_admin(credentials: HTTPBasicCredentials | None = Depends(basic)) -> str:
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        raise HTTPException(status_code=503, detail="Review is disabled: set ADMIN_PASSWORD")
    user = os.environ.get("ADMIN_USER", "admin")
    if (
        credentials is None
        or not same(credentials.username, user)
        or not same(credentials.password, password)
    ):
        raise HTTPException(status_code=401, detail="Login required", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def require_api_token(x_api_key: str | None = Header(default=None)) -> None:
    token = os.environ.get("API_TOKEN", "")
    if token and (x_api_key is None or not same(x_api_key, token)):
        raise HTTPException(status_code=401, detail="Missing or wrong X-API-Key header")
