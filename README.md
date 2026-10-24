# RAKKI

RAKKI is a product evidence and assessment workspace built with React, Vite, TypeScript, FastAPI, SQLAlchemy 2, Alembic, and MySQL. Gemini image observations are assistive and remain unverified until a person reviews and saves them.

## Local development

Use Docker Desktop and Compose:

```powershell
Copy-Item .env.example .env
```

Set local-only database passwords and `APP_SECRET_KEY`; set `GEMINI_API_KEY` only if you want image analysis. Then run:

```powershell
docker compose up --build
```

The Vite development frontend is at <http://localhost:5173>; the API is at <http://localhost:8200>. Vite proxies `/api/*` to the backend. Compose uses local image storage and a local MySQL volume. `docker compose down` retains the volumes. Avoid `docker compose down --volumes` if you need local data or uploads.

For backend development, install `backend/requirements.txt` in a virtual environment, copy `backend/.env.example` to `backend/.env`, and run Alembic and Uvicorn from `backend/`. For frontend development, run `npm ci` and `npm run dev` from `frontend/`.

## Product workflow

- Catalog creation supports locations, categories, condition, intact/clean state, quantity, notes, and multiple JPEG, PNG, or WebP uploads. Images are validated by decoded content and limited to 5 MB each by default.
- Gemini can suggest a product name, category, process, and materials. Suggestions remain unverified until reviewed; Gemini does not assess cleanliness, intactness, or condition. Uploads and user data remain available when Gemini is not configured or fails.
- Inventory is paginated and supports inline create/edit. Product details support manual edits, material verification, image selection/removal, revisions, and Excel export.
- Product and image deletion are authenticated operations. Image records preserve primary-image selection and are stored locally in development or in the private Blob container in production.
- The app uses a shared workspace for authenticated users. Passwords use Argon2id; sessions use signed HTTP-only cookies and CSRF tokens. There is no public account registration; create the initial user with `python -m app.cli create-user` after deployment.

## Production architecture

- **Frontend:** Cloudflare Pages, built from `frontend/` with `npm ci` then `npm run build`, output directory `dist`.
- **API:** Azure Container Apps Consumption in Sweden Central. Use a small initial allocation (0.25 vCPU / 0.5 GiB), minimum replicas `0`, and a modest maximum (for example `1` for a demo). Scale-to-zero saves compute but adds cold-start delay.
- **Database:** Continue using the existing Azure Database for MySQL Flexible Server `mysql-rakki-prod`, database `rakki`, and least-privilege application login `rakki_app`. This project does not change its SKU, network, backup policy, or data. Set `DB_SSL_CA` to the included PEM bundle; certificate and hostname verification are enabled.
- **Images:** Azure Blob Storage Standard, Hot, LRS in Sweden Central, private container. The API accesses it with the Container App's managed identity and `Storage Blob Data Contributor` scoped to the container/storage account. Images remain behind authenticated `/api/images/{id}` routes; the container is not public.
- **Secrets:** Put `APP_SECRET_KEY`, `DB_PASSWORD`, and `GEMINI_API_KEY` in Container Apps secrets. Do not commit populated environment files. Key Vault is not needed for this demo and would add setup and potential cost.

The root `Dockerfile` is the production API image. It runs as a non-root user and does not run migrations when the web container starts. Compose remains a local development setup.

## Cloudflare Pages `/api/*` proxy

`frontend/functions/api/[[path]].ts` forwards all `/api/*` requests to the `BACKEND_ORIGIN` Pages environment variable. Set that variable to the public HTTPS origin of the Container App (for example `https://<app-name>.<region>.azurecontainerapps.io`, without a path). Do not set `VITE_API_URL` for this same-origin setup; the React app defaults to `/api`. Set `CORS_ORIGINS` to the exact Pages origin(s), including the custom domain if used. The proxy preserves cookies, CSRF headers, HTTP methods, and query strings.

Configure Pages with repository root `frontend`, build command `npm ci && npm run build`, output directory `dist`, and `BACKEND_ORIGIN` as a runtime environment variable for the Pages Function. Vite's `VITE_PROXY_TARGET` remains for local development only.

## Azure MySQL TLS

The backend uses PyMySQL with certificate-chain and server-identity verification whenever `DB_SSL_CA` is set. Production startup requires this setting. The image includes `backend/certs/azure-mysql-ca-bundle.pem`, containing DigiCert Global Root CA (G1), DigiCert Global Root G2, and Microsoft RSA Root Certificate Authority 2017 for the documented transition. The bundle contains public CA certificates, not secrets. Keep it current with Microsoft's Azure MySQL root rotation guidance.

Never disable TLS verification to make a failed connection work. Confirm `DB_HOST` is the full Azure hostname and `DB_SSL_CA` points to the bundled PEM.

## Safe migration procedure

The migration chain is `0001_initial` through `0007_auth_users`. The user confirmed that the legacy product columns removed by `0006_process_fields` do not need to be retained. Other downgrade operations also drop columns or the `users` table, so do not use downgrade as a production rollback.

Before an Azure migration:

1. Confirm the target server/database, current Alembic revision, and actual schema using a read-only connection. If `alembic_version` is absent or the schema differs from the expected predecessor, stop and reconcile the baseline; do not blindly stamp the database.
2. Take and verify a MySQL backup/restore point. Preserve Blob and any existing local image files separately; the migration does not migrate or delete image bytes.
3. Review the exact migration SQL against the schema and run the migration against a restored/staging copy first. In particular, confirm the `0006` legacy-column drops and that the target is at the expected prior revision.
4. Run `alembic upgrade head` once as a controlled release step, using a migration-only database credential where possible. Do not run it automatically on every API replica.
5. Deploy the API image and verify `/api/health` and an authenticated product/image read. Keep the backup until verification is complete.

Example one-off invocation from the backend image, using a protected environment file that is not committed:

```powershell
docker run --rm --env-file .\migration.env --entrypoint alembic rakki-api:<tag> upgrade head
```

Before switching existing image records to Blob Storage, inventory `product_images` rows and locate their current bytes. If image bytes currently live on a local disk/volume, copy them to blobs under the same `filename` keys and verify every object before setting `STORAGE_PROVIDER=azure_blob`. Keep the source files until the counts and checksums match; no database migration is needed for the Blob adapter.

## Azure resource setup (manual; not performed)

1. Reuse the existing MySQL server and its current region/SKU. Do not resize, stop, or alter its firewall/backups without a separate review.
2. Create one Standard general-purpose storage account in Sweden Central using LRS and Hot block blob storage; create a private `product-images` container. Assign the Container App managed identity `Storage Blob Data Contributor`. Do not enable public blob access, geo-replication, private endpoints, or lifecycle deletion until the actual need and cost are reviewed.
3. Build and push the API image to a registry, then create a Consumption Container Apps environment and app in Sweden Central. Configure scale-to-zero, a low resource allocation, HTTPS ingress, health probes (`/api/health/live` for liveness and `/api/health` for readiness), and only the needed maximum replicas.
4. Add production environment variables from `deploy/azure-container-apps.env.example` as secrets/settings. Set Pages `BACKEND_ORIGIN`, and set `CORS_ORIGINS` to the exact Pages site origin.
5. Confirm the Container App's outbound IPs and configure the existing MySQL firewall narrowly enough for the app. Preserve TLS verification. Do not enable broad “allow Azure services” access without reviewing its wider scope.
6. Create the initial login with `python -m app.cli create-user` after migrations and deploy; use an interactive secure session and a unique password.

No Azure resources are created or changed by this repository work. Review actual portal prices and access settings before provisioning.


Price and operations references: [Container Apps billing and free grants](https://learn.microsoft.com/azure/container-apps/billing), [Azure Container Registry pricing](https://azure.microsoft.com/pricing/details/container-registry/), [Azure Blob Storage pricing](https://azure.microsoft.com/pricing/details/storage/blobs/), [Azure MySQL root certificate rotation](https://learn.microsoft.com/azure/mysql/security/security-tls-root-certificate-rotation), and [Azure Monitor cost and usage](https://learn.microsoft.com/azure/azure-monitor/usage-estimated-costs), and [Azure bandwidth pricing](https://azure.microsoft.com/pricing/details/bandwidth/), and [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Cost plan (monthly estimate, euros)

Assumptions: the existing MySQL bill remains about **€14/month** as reported; Sweden Central; one small demo API; no minimum replicas; no more than 5 GB image storage; light image traffic; no custom domains or paid Cloudflare add-ons; and no sustained log ingestion above free allowances. Azure quotes vary by subscription, currency, region, and tax, so validate in the Azure Pricing Calculator and Cost Management before provisioning.

| Component | Estimate | Cost behavior and notes |
| --- | ---: | --- |
| Existing Azure MySQL Flexible Server | ~€14 | User-reported current fixed baseline. Preserve its SKU and availability settings. |
| Container Apps Consumption API | €0 in low-use scenario; variable above allowance | First 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests per subscription/month are free; scale-to-zero has no replica compute charge. At 0.25 vCPU/0.5 GiB, CPU allowance covers about 50 active hours/month for one replica. Cold starts are the trade-off. |
| Blob Storage Standard Hot LRS | ~€0.10 for 5 GB, plus small operation/transfer charges | Usage-based. LRS avoids the higher replication cost; keep the container private. Estimate is a planning approximation, not a quote. |
| Azure internet egress | €0 assumed below the shared 100 GB/month allowance; about €0.08/GB beyond it | Usage-based. Light demo image delivery should remain low; the allowance is shared with other subscription traffic. |
| Managed Identity | €0 | No separate charge; recommended for backend access to Blob Storage. |
| Azure Monitor / Log Analytics | €0 at or below shared 5 GB/month free ingestion; usage-based above | Keep logs concise, avoid request/body/image logging, set a daily cap/alert, and monitor ingestion. Existing subscription usage shares the allowance. |
| ACR Basic, if selected for private image pulls | about €4.5–€5/month | Fixed daily registry charge, includes 10 GB storage. Not needed for local development; use only when you need private Azure-native image storage and Managed Identity pulls. |
| Cloudflare Pages | €0 assumed | Assumes the existing/free Pages plan and usage within its current limits; verify Cloudflare account plan. |
| Gemini API (`gemini-3.8-flash`) | Separate from Azure; no fixed Azure cost | Google lists paid Standard rates of $0.75/1M input tokens and $3.75/1M output tokens through Dec. 31, 2026, then $1.50/$7.50 from Jan. 1, 2027. Image and prompt token counts determine per-call cost; the app makes one automatic analysis call and no automatic retries. Manual retries may incur additional charges. |

**Expected Azure total:** about **€14.10/month without ACR** in the low-use assumption; about **€18.60–€19.10/month with ACR Basic**, before any Container Apps usage above its free grant, log overage, image growth, data transfer, taxes, or subscription-specific rates. Sustained API activity, ACR, or excess logs can push the total above **€20/month**. The first practical cost-saving option is to defer ACR during development; for a private production image registry, Basic ACR is the simplest Azure-native tier and its cost should be approved before creation. A free external registry may avoid the ACR charge but introduces external registry credentials or public image visibility.

### Cost controls and review

- Keep Container Apps `minReplicas=0`; use a low initial allocation and `maxReplicas=1` for demos. Raise limits only after measuring latency and memory.
- Keep MySQL running and backed up. Do not pause, resize, delete, or weaken its security to save cost.
- Use Blob Hot LRS for small, regularly viewed product images. Set upload limits, avoid duplicate uploads, and periodically review storage usage; do not automatically delete user images.
- Keep Gemini timeouts bounded (30 seconds), avoid automatic retries, and trigger reanalysis only when needed. Gemini charges are separate from Azure.
- In Azure Portal, check **Cost Management + Billing → Cost analysis**; filter by subscription/resource group/service and month, and add a budget with alerts near €18 and €20. Review Container Apps replica/usage metrics, Blob capacity/transactions, ACR tier/storage, and Log Analytics ingestion. Pricing calculator amounts and credits/allowances should be verified for the actual subscription before creating resources.

## Authentication and operational behavior

The shared workspace requires a user account. Passwords are hashed with Argon2id; browser sessions use a signed, HTTP-only, HTTPS-only production cookie and unsafe API requests require a CSRF token. Login throttling is process-local, so it is a modest demo control rather than a distributed rate limiter. Do not expose backend ingress outside the Pages proxy unless required.

The `/api/health/live` endpoint checks process liveness without touching MySQL; `/api/health` checks database readiness. Logs go to stdout/stderr and should remain at INFO/WARNING in production. Gemini calls are capped at 30 seconds with no automatic retry, avoiding surprise duplicate charges.

## Tests and build

From `backend/`, run `pytest`. From `frontend/`, run `npm ci` and `npm run build`. The deployment Dockerfile can be validated with `docker build -t rakki-api:local -f Dockerfile .`. Tests/builds do not connect to the live database when using the included SQLite test fixtures.
