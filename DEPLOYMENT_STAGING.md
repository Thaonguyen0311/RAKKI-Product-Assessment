# RAKKI staging deployment (Cloudflare Pages + Azure)

This guide deploys a **separate staging copy**. It does not import, reset, or delete local Docker volumes or local MySQL data.

## Branch

Use `deploy/cloudflare-azure-staging` for the first staging deployment. Do not change the production/default branch just to test hosting.

## Cloudflare Pages frontend

Create a Pages project from the GitHub repository and select branch `deploy/cloudflare-azure-staging`.

- Root directory: `frontend`
- Build command: `npm run build`
- Build output directory: `dist`
- Environment variable: `BACKEND_URL` = the Azure backend HTTPS origin only, e.g. `https://<app-name>.<region>.azurecontainerapps.io` (no trailing path such as `/api`)

The Pages Function in `frontend/functions/api/[[path]].ts` forwards same-origin `/api/*` requests to Azure. This keeps browser requests on the Pages hostname, which is important for the existing cookie-based login and CSRF flow. Do not set `VITE_API_URL` to a separate backend hostname for this deployment.

## Azure backend configuration

Deploy the repository's root Dockerfile to Azure Container Apps. Use a **new staging database** and a new storage location; do not point staging at any existing or local database.

Required application settings/secrets:
- `APP_ENV=production`
- `APP_SECRET_KEY`: a newly generated random secret of at least 32 characters
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: staging-only Azure database credentials
- `GEMINI_API_KEY`: secret set in Azure, never committed to Git
- `GEMINI_MODEL`: use a model name verified against the Gemini API account
- `CORS_ORIGINS`: leave as a comma-separated HTTPS origin list if required by the app; the same-origin Pages proxy means browser API requests normally originate from Pages, so include the exact Pages origin if CORS checks are needed

The container runs `alembic upgrade head` on startup. It should run only against the new staging database during this first deployment.

## Important image-storage gate

The current backend saves uploaded images under `STORAGE_DIR` on the local filesystem. A normal Container Apps container filesystem is not a safe durable image store across replacement/revision/scale events. **Before testing image upload as a reliable feature**, configure Azure Blob Storage or an appropriately mounted persistent Azure Files share and update the backend storage service. Do not claim image persistence is production-ready until this change has been tested.

## Safe test sequence

1. Keep the current local app running and leave its Docker volumes alone.
2. Create a separate staging database and credentials.
3. Deploy backend and verify `/api/health` reports database connected.
4. Set `BACKEND_URL` in Cloudflare Pages and deploy the frontend.
5. Verify login, logout, CSRF-protected edits, and product CRUD using test-only data.
6. Verify Gemini analysis only after the model/key are confirmed.
7. Test image upload and retrieval only after durable image storage is configured.
8. Export/backup staging data before any later migration. Do not import local data until explicitly planned and backed up.

## Cost and security

Check the Azure pricing estimate and set a budget/alert where supported before creating billable resources. Never paste passwords, API keys, subscription IDs, or other secrets into GitHub commits or chat. Use Azure secret/environment settings. Student credits have eligibility and usage terms; verify these in the Azure portal.
