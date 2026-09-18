from fastapi import Header, HTTPException

from .models import User
from .repository import get_users


def current_user(x_user_id: str = Header(default="bryan")) -> User:
    user = next((item for item in get_users() if item.id == x_user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown simulated user")
    return user


def require_edit(user: User, developer_id: str) -> None:
    if user.role != "pm" and user.id != developer_id:
        raise HTTPException(status_code=403, detail="Developers may only edit their own update")
