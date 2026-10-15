# RAKKI

RAKKI is a product evidence and assessment workspace. This implementation uses React/Vite/TypeScript in `frontend/` and FastAPI, SQLAlchemy 2, Alembic, MySQL, and the official Google Gen AI SDK in `backend/`.

## Core workflow

Create a product, upload one JPEG/PNG/WebP image (maximum configured size), and run Gemini analysis. Extracted image observations are retained as an AI extraction and only fill blank product fields; existing user-reviewed fields are not overwritten. Product edits create a revision snapshot. Excel export includes product, materials, sustainability, and evidence sheets. Carbon is reported as insufficient until a documented method and inputs exist; RAPU remains pending an authoritative formula.

## Local setup

Requirements: Python 3.12 (3.11+ should work), Node 20+, and a running MySQL 8 compatible server. The app does not create, reset, or drop databases. Create a dedicated `rakki` database and least-privilege `rakki_app` user yourself, then copy `backend/.env.example` to `backend/.env` and set credentials. Set `GEMINI_API_KEY` to enable image analysis. Never put keys in frontend environment variables. Configure `APP_SECRET_KEY` with a random secret before deployment.

Backend (PowerShell):

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs. Health check: http://localhost:8000/api/health. Images are stored in `backend/storage` by default, outside the frontend's public directory. Back up both MySQL and that storage directory.

Frontend (second terminal):

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` at frontend build time if the API is hosted somewhere other than `http://localhost:8000/api`.

## Data operations

Back up with `mysqldump --single-transaction -u rakki_app -p rakki > rakki-backup.sql`; restore to the intended database with `mysql -u rakki_app -p rakki < rakki-backup.sql`. Back up uploaded image files at the same time. Alembic migration downgrade is intentionally non-destructive and does not drop production tables.

## Tests and migrations

Install backend requirements and run `pytest` from `backend`. Migrations are in `backend/alembic`; run `alembic upgrade head` against a dedicated empty test database for migration validation, never against a valuable database without a verified backup. Frontend production build: `npm run build` from `frontend`.
