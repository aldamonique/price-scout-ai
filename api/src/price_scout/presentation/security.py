import secrets
from collections.abc import Callable

from fastapi import Header, HTTPException, status


def admin_only(token: str | None) -> Callable[[str | None], None]:
    def check(authorization: str | None = Header(default=None)) -> None:
        if token is None:
            return
        expected = f"Bearer {token}"
        if authorization is None or not secrets.compare_digest(authorization, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This action needs the admin token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return check
