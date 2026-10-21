from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_current_user(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    session_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = x_session_token or session_token
    if not token:
        raise HTTPException(status_code=401, detail="Sign in required")
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    return user


def optional_user(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    session_token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    token = x_session_token or session_token
    if not token:
        return None
    return db.query(User).filter(User.token == token).first()
