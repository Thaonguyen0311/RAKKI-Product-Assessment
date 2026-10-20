# RAKKI

RAKKI is a product evidence and assessment workspace. The existing React/Vite/TypeScript application uses FastAPI, SQLAlchemy 2, Alembic, and MySQL. Gemini image observations are assistive and remain unverified until a person reviews and saves them.

## Start with Docker

Docker Desktop with Docker Compose is the only host dependency for this workflow. From the repository root, create your local environment file and replace its password and secret placeholders:

```powershell
Copy-Item .env.example .env
```

Set `DB_PASSWORD`, `MYSQL_ROOT_PASSWORD`, and `APP_SECRET_KEY` in `.env`. Set `GEMINI_API_KEY` to enable image analysis; it may be left blank for the rest of the application. Do not commit `.env`.

Build and start all services:

```powershell
docker compose up --build
```

Open the frontend at <http://localhost:5173>. The API is at <http://localhost:8000>, with interactive docs at <http://localhost:8000/docs> and health status at <http://localhost:8000/api/health>. The frontend calls the same-origin `/api` path, and Vite proxies it to the backend container. MySQL is available to the Docker network only; it is not published to the host.

Stop the services while retaining MySQL and images:

```powershell
docker compose down
```

Rebuild after changing dependencies or Docker configuration:

```powershell
docker compose up --build
```

Migrations run automatically before the backend starts and are safe to repeat. To run them manually after the services are up:

```powershell
docker compose exec backend alembic upgrade head
```

The database and image uploads persist in named volumes `mysql_data` and `uploaded_images`. To permanently erase all local database data and uploads, run `docker compose down --volumes`.

## Local development without Docker

The backend needs Python 3.11+ and a dedicated MySQL database. In one terminal, from `backend/`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal, from `frontend/`, with Node.js 20+:

```powershell
npm ci
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000` by default. Set `VITE_PROXY_TARGET` if the local API uses another address.

## Product workflow

- The Catalog create form allows an empty product name. Location, category, condition, intact/clean status, quantity, additional notes, and several JPEG, PNG, or WebP images can be supplied. Quantity defaults to `1`. The product is created before any image analysis, so Gemini is optional and cannot prevent creation.
- After a successful image upload, analysis starts automatically. Gemini can suggest a concise product name, one supported category, observable additional notes, and up to five ranked material candidates with confidence. The backend selects the candidate with the highest Gemini confidence, maps it to the closest canonical material, and resolves its ID and full category path. Approximate or low-confidence results remain visibly unverified until the user reviews and saves them. Images and user entries remain intact if Gemini is unavailable; the detail panel has a retry action and lets you choose the image to analyze.
- The Inventory tab shows database records in a paginated table with ID, completion date, location, category, material, material ID, material category, product name, condition, intact/clean status, quantity, notes, and edit/delete actions. The table supports inline create, edit, save, and cancel. IDs and categories are resolved from the canonical material table. Category options are `Movable Furniture and Fixed Furnishings`, `Electrical`, `HVAC and Plumbing`, `Building Components and Materials`, and `Other`.
- Condition choices are `1 - Very Poor`, `2 - Poor`, `3 - Fair`, `4 - Good`, `5 - Excellent`, and `Not Assessed`. The condition scale is an application convention, not an original dataset rating. Intact and clean default to `Not Assessed`; Gemini does not make those judgments.
- Product details allow edits to product name, category, subtype, brand, SKU, color, description, condition, and canonical material. Material IDs and full category paths are recalculated on the backend and are read-only in the UI. Saves use `PATCH /api/products/{product_id}`, create a revision snapshot, and persist field provenance and human verification separately from the AI extraction.
- The detail panel shows every image. Users can add images, choose the primary thumbnail, or remove an image. The catalog preserves search and assessment-status filtering and links each card to its detail panel.
- Product deletion requires confirmation and removes dependent materials, images, AI extraction records, assessments, evidence sources, revisions, and stored image files.
- Excel export remains available from the catalog. Sustainability assessments do not invent a carbon method or RAPU score; their current status explains which method or evidence is missing.

Each image is validated from its decoded contents and limited to `MAX_UPLOAD_SIZE_MB` (5 MB by default). Up to 10 images may be submitted per request, with per-image failures reported while successful uploads are kept. The primary image defaults to the earliest uploaded image; deleting it selects the earliest remaining image.

## Configuration

Docker settings are read from the root `.env`. `backend/.env.example` documents the equivalent local backend settings. Gemini keys belong only in the backend environment and are never sent to the browser. CORS defaults are limited to the local frontend origins. Change `APP_SECRET_KEY` and database passwords before using a shared environment.

## Migrations and compatibility

The existing `0001_initial` migration uses the model metadata to create tables. `0002_primary_product_image` adds the primary-image flag only when needed and marks the earliest existing image for each product as primary. `0003_product_field_provenance` stores AI/user provenance and verification status for product fields and marks legacy data unverified. `0004_inventory_fields` adds inventory details, derives legacy completion dates from record creation dates, and defaults legacy quantities to one. `0005_canonical_material` adds nullable material, numeric material ID, full category path, and confirmation fields without changing existing product rows. The 304-record source of truth is `backend/app/data/material_mapping.json`; `GET /api/materials` supplies the searchable frontend list, while Gemini returns a name suggestion that the API resolves through this mapping. Existing products and image records are retained. An empty product name is valid in the existing non-null name column, so it requires no separate migration. For local runs, apply migrations using `alembic upgrade head`; Docker runs the same command on backend startup. Back up MySQL and the image volume before production upgrades.

## Tests and build

Run backend tests from `backend/` after installing requirements:

```powershell
pytest
```

Build the frontend from `frontend/`:

```powershell
npm run build
```

Docker image/compose validation can be run with `docker compose config` and `docker compose up --build`.

## Manual editing issue found

The FastAPI `PATCH /api/products/{product_id}` route already used `ProductUpdate` and `exclude_unset=True`, so it supported partial edits for its declared fields. Users could not edit those fields because the React product sheet only displayed read-only text and exposed no controlled edit inputs or save action. The earlier browser workflow only submitted a product name during creation. This update adds the form and connects it to the existing PATCH route. The route now also accepts a full material list when supplied.

The Gemini service validates structured inventory and material candidate outputs, category options, and confidence. Material IDs and categories always come from the canonical backend mapping, and the model does not infer condition, cleanliness, intact status, or unsupported specifications.

## Security note

This application still has no authentication or authorization and is intended for local or trusted internal development. Do not expose it publicly until access control and production rate limiting are added. Do not commit `.env` or publish the local development ports to an untrusted network.
