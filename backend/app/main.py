import logging

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

if settings.storage_provider not in {'local', 'azure_blob'}:
    raise RuntimeError('STORAGE_PROVIDER must be local or azure_blob')
if settings.is_production and settings.storage_provider != 'azure_blob':
    raise RuntimeError('Production requires STORAGE_PROVIDER=azure_blob to preserve uploaded images')
if settings.is_production and not settings.db_ssl_ca:
    raise RuntimeError('Production requires DB_SSL_CA with the Azure MySQL root CA bundle')
if settings.storage_provider == 'azure_blob' and (
    not settings.azure_storage_account_url or not settings.azure_storage_container
):
    raise RuntimeError('Azure Blob storage requires AZURE_STORAGE_ACCOUNT_URL and AZURE_STORAGE_CONTAINER')

if settings.app_env.lower() == 'production' and (
    'app_secret_key' not in settings.model_fields_set
    or len(settings.app_secret_key) < 32
    or settings.app_secret_key.startswith('replace_with_')
):
    raise RuntimeError('Production requires a generated APP_SECRET_KEY with at least 32 characters')
if settings.is_production and (not settings.cors_list or '*' in settings.cors_list):
    raise RuntimeError('Production CORS_ORIGINS must list exact HTTPS frontend origins')
if settings.is_production and any(not origin.startswith('https://') for origin in settings.cors_list):
    raise RuntimeError('Production CORS_ORIGINS must use HTTPS')

app = FastAPI(
    title='RAKKI API', version='1.0.0',
    description='Product assessment and evidence tracking API',
    docs_url=None if settings.is_production else '/docs',
    redoc_url=None if settings.is_production else '/redoc',
    openapi_url=None if settings.is_production else '/openapi.json',
)
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


@app.get('/api/health/live')
def liveness():
    return {'status': 'ok'}


@app.get('/api/health')
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
        return {'status': 'ok', 'database': 'connected'}
    except Exception as exc:
        raise HTTPException(503, 'Database unavailable') from exc


app.include_router(auth_router)
app.include_router(router)
