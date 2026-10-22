import pytest
import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.db.session import Base, get_db
from app.main import app
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture
def auth_client(tmp_path):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    with session_factory() as db:
        db.add_all([
            User(username='active-admin', password_hash=hash_password('active-test-password-2026')),
            User(username='inactive-admin', password_hash=hash_password('inactive-test-password-2026'), is_active=False),
        ])
        db.commit()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_unauthenticated_access_is_rejected_and_health_stays_public(auth_client):
    assert auth_client.get('/api/products').status_code == 401
    assert auth_client.post('/api/products', json={'name': 'Blocked'}).status_code == 401
    assert auth_client.get('/api/export.xlsx').status_code == 401
    assert auth_client.get('/api/health').status_code == 200


def test_passwords_are_stored_as_argon2id_hashes():
    hashed = hash_password('test-password-long-enough')
    assert hashed.startswith('$argon2id$')


def test_login_rejects_missing_invalid_and_inactive_accounts_generically(auth_client):
    assert auth_client.post('/api/auth/login', json={}).status_code == 422
    assert auth_client.post('/api/auth/login', json={
        'username': 'active-admin', 'password': '1234',
    }).status_code == 422
    wrong = auth_client.post('/api/auth/login', json={'username': 'absent-admin', 'password': 'wrong-password'})
    inactive = auth_client.post('/api/auth/login', json={
        'username': 'inactive-admin', 'password': 'inactive-test-password-2026',
    })
    assert wrong.status_code == inactive.status_code == 401
    assert wrong.json()['detail'] == inactive.json()['detail'] == 'Invalid username or password'


def test_authenticated_session_csrf_protection_and_logout(auth_client):
    response = auth_client.post('/api/auth/login', json={
        'username': 'active-admin', 'password': 'active-test-password-2026',
    })
    assert response.status_code == 200
    assert 'password_hash' not in response.json()['user']
    assert 'httponly' in response.headers['set-cookie'].lower()
    csrf = response.json()['csrf_token']

    assert auth_client.get('/api/auth/me').json()['user']['username'] == 'active-admin'
    assert auth_client.get('/api/auth/me').json()['user']['id'] == response.json()['user']['id']
    assert auth_client.get('/api/products').status_code == 200
    assert auth_client.post('/api/products', json={'name': 'No CSRF'}).status_code == 403
    created = auth_client.post('/api/products', json={'name': 'Authenticated item'}, headers={'X-CSRF-Token': csrf})
    assert created.status_code == 201

    logged_out = auth_client.post('/api/auth/logout', headers={'X-CSRF-Token': csrf})
    assert logged_out.status_code == 200
    assert auth_client.get('/api/products').status_code == 401


def test_login_rate_limit(auth_client):
    for _ in range(5):
        response = auth_client.post('/api/auth/login', json={'username': 'rate-test-user', 'password': 'wrong-password'})
        assert response.status_code == 401
    limited = auth_client.post('/api/auth/login', json={'username': 'rate-test-user', 'password': 'wrong-password'})
    assert limited.status_code == 429


def test_auth_migration_adds_users_without_changing_products():
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.exec_driver_sql('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
        connection.exec_driver_sql("INSERT INTO products (id, name) VALUES (1, 'Existing RAKKI record')")
        migration_path = Path(__file__).parents[1] / 'alembic' / 'versions' / '0007_auth_users.py'
        spec = importlib.util.spec_from_file_location('auth_users_migration', migration_path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        user_tables = set(sa.inspect(connection).get_table_names())
        product = connection.exec_driver_sql('SELECT id, name FROM products').one()
    assert 'users' in user_tables
    assert product == (1, 'Existing RAKKI record')
    engine.dispose()
