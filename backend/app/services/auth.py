import hmac
import secrets
import threading
import time

from fastapi import Depends, Header, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

password_hasher = PasswordHash.recommended()
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))
_attempts: dict[tuple[str, str], list[float]] = {}
_attempt_lock = threading.Lock()
_ATTEMPT_WINDOW_SECONDS = 15 * 60
_MAX_FAILED_ATTEMPTS = 5


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    return password_hasher.verify(password, password_hash or _dummy_hash)


def login_is_limited(remote_addr: str, username: str) -> bool:
    now = time.monotonic()
    key = (remote_addr, username.casefold())
    with _attempt_lock:
        for attempt_key in list(_attempts):
            recent = [stamp for stamp in _attempts[attempt_key] if now - stamp < _ATTEMPT_WINDOW_SECONDS]
            if recent:
                _attempts[attempt_key] = recent
            else:
                del _attempts[attempt_key]
        return len(_attempts.get(key, [])) >= _MAX_FAILED_ATTEMPTS


def record_login_failure(remote_addr: str, username: str) -> None:
    key = (remote_addr, username.casefold())
    with _attempt_lock:
        _attempts.setdefault(key, []).append(time.monotonic())


def clear_login_failures(remote_addr: str, username: str) -> None:
    with _attempt_lock:
        _attempts.pop((remote_addr, username.casefold()), None)


def require_authenticated_user(
    request: Request,
    db: Session = Depends(get_db),
    csrf_token: str | None = Header(default=None, alias='X-CSRF-Token'),
) -> User:
    user_id = request.session.get('user_id')
    user = db.get(User, user_id) if isinstance(user_id, int) else None
    if (user is None or not user.is_active or
            request.session.get('session_version') != user.session_version):
        request.session.clear()
        raise HTTPException(status_code=401, detail='Authentication required')

    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        expected = request.session.get('csrf_token', '')
        if not csrf_token or not hmac.compare_digest(csrf_token, expected):
            raise HTTPException(status_code=403, detail='Invalid CSRF token')
    return user
