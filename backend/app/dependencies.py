from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User
from app.services.auth import decode_access_token


def get_request_id(x_request_id: str | None = Header(default=None)) -> str:
    return x_request_id or str(uuid4())


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Authentication required"})

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail={"code": "TOKEN_INVALID", "message": "Invalid or expired token"})

    user = (
        db.query(User)
        .options(joinedload(User.patient), joinedload(User.doctor))
        .filter(User.id == payload["sub"])
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "User not found"})
    return user
