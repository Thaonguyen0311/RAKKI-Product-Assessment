import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginIn
from app.services.auth import (
    clear_login_failures,
    login_is_limited,
    record_login_failure,
    require_authenticated_user,
    verify_password,
)

router = APIRouter(prefix='/api/auth', tags=['authentication'])
GENERIC_LOGIN_ERROR = 'Invalid username or password'


def _user_payload(user: User) -> dict:
    return {
        'id': user.id,
        'username': user.username,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat(),
    }


@router.post('/login')
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    origin = request.headers.get('origin')
    if origin and origin not in settings.cors_list:
        raise HTTPException(status_code=403, detail='Request origin is not allowed')

    remote_addr = request.client.host if request.client else 'unknown'
    if login_is_limited(remote_addr, data.username):
        raise HTTPException(status_code=429, detail='Too many login attempts. Try again later.')

    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash if user and user.is_active else None) or not user.is_active:
        record_login_failure(remote_addr, data.username)
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)

    clear_login_failures(remote_addr, data.username)
    csrf_token = secrets.token_urlsafe(32)
    request.session.clear()
    request.session['user_id'] = user.id
    request.session['session_version'] = user.session_version
    request.session['csrf_token'] = csrf_token
    return {'user': _user_payload(user), 'csrf_token': csrf_token}


@router.get('/me')
def me(request: Request, user: User = Depends(require_authenticated_user)):
    csrf_token = request.session.get('csrf_token')
    if not csrf_token:
        csrf_token = secrets.token_urlsafe(32)
        request.session['csrf_token'] = csrf_token
    return {'user': _user_payload(user), 'csrf_token': csrf_token}


@router.post('/logout')
def logout(request: Request, _user: User = Depends(require_authenticated_user), db: Session = Depends(get_db)):
    _user.session_version += 1
    request.session.clear()
    db.commit()
    return {'status': 'ok'}
