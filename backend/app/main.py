from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth_routes import router as auth_router
from app.api.routes import router
from app.core.config import settings
from app.db.session import get_db

if settings.app_env.lower() == 'production' and (
    'app_secret_key' not in settings.model_fields_set
    or len(settings.app_secret_key) < 32
    or settings.app_secret_key.startswith('replace_with_')
):
    raise RuntimeError('Production requires a generated APP_SECRET_KEY with at least 32 characters')
if settings.app_env.lower() == 'production' and any(origin.startswith('http://') for origin in settings.cors_list):
    raise RuntimeError('Production CORS_ORIGINS must use HTTPS')

app = FastAPI(title='RAKKI API', version='1.0.0', description='Product assessment and evidence tracking API')
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
    session_cookie='rakki_session',
    max_age=8 * 60 * 60,
    same_site='lax',
    https_only=settings.app_env.lower() == 'production',
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
                   allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
                   allow_headers=['Content-Type', 'X-CSRF-Token'])


@app.get('/api/health')
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {'status': 'ok', 'database': 'connected'}
    except Exception as exc:
        raise HTTPException(503, 'Database unavailable') from exc


app.include_router(auth_router)
app.include_router(router)
