# Deployment: Docker Hub + Azure Container Apps

An alternative to `docs/deployment.md` (IBM Code Engine), chosen to avoid
the IBM Cloud Databases account-upgrade requirement. watsonx Orchestrate
does not care who hosts the API it calls — only that it's a public HTTPS
endpoint with a valid OpenAPI document. Nothing in the application code
differs between the two deployment targets; only where the containers and
database run changes.

## Architecture

```
watsonx Orchestrate (calls your API as a tool, imported from openapi.json)
           │ HTTPS
           ▼
Azure Container Apps
  ├── finassist-frontend  (nginx, port 80)   → https://....azurecontainerapps.io
  └── finassist-backend   (FastAPI, port 8000) → https://....azurecontainerapps.io
           │
           ▼
Azure Database for PostgreSQL — Flexible Server
```

## Why this avoids the IBM account-upgrade problem

- **Registry**: Docker Hub, not IBM Container Registry. A **public** Docker
  Hub repo needs zero registry credentials on the Azure side — simpler
  than IBM's registry-secret step.
- **Database**: Azure's free account includes **750 hours/month of
  Burstable (B1ms) compute + 32GB storage for Azure Database for
  PostgreSQL Flexible Server, free for 12 months** — no paid-tier upgrade
  required, unlike IBM Cloud Databases for PostgreSQL (which dropped its
  free Lite tier).

## 1. Push images to Docker Hub

```bash
docker login

cd backend
docker build -t <your-dockerhub-username>/finassist-backend:v1 .
docker push <your-dockerhub-username>/finassist-backend:v1
```

If the repo is **public** (default for a free Docker Hub account), Azure
needs no credentials to pull it — skip straight to Step 3 for the
backend. If you make it **private**, add `--registry-server docker.io
--registry-username <user> --registry-password <token>` to the
`az containerapp create` calls below (use a Docker Hub access token, not
your account password).

## 2. Create the Azure Database for PostgreSQL instance

```bash
az login
az group create --name finassist-rg --location eastus

az postgres flexible-server create \
  --resource-group finassist-rg \
  --name finassist-pg \
  --location eastus \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --version 16 \
  --admin-user finassist \
  --admin-password "$(openssl rand -base64 24)" \
  --public-access 0.0.0.0-255.255.255.255   # tighten later, see note below

az postgres flexible-server db create \
  --resource-group finassist-rg \
  --server-name finassist-pg \
  --database-name finassist
```

The generated password is printed once by `openssl rand` into your shell
history, not written to any file here — copy it immediately into a
password manager, then build `DATABASE_URL`:

```text
postgresql+psycopg://finassist:<password>@finassist-pg.postgres.database.azure.com:5432/finassist?sslmode=require
```

`--public-access 0.0.0.0-255.255.255.255` opens the firewall to any IP,
which is fine for a short-lived course-project demo but is not something
to leave open indefinitely — narrow it to Azure Container Apps' outbound
IP range (`az postgres flexible-server firewall-rule create` with a
specific range) once you know it, per `docs/security.md`'s posture on not
leaving things open by default.

## 3. Create the Container Apps environment and deploy the backend

```bash
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App

az containerapp env create \
  --name finassist-env \
  --resource-group finassist-rg \
  --location eastus

az containerapp create \
  --name finassist-backend \
  --resource-group finassist-rg \
  --environment finassist-env \
  --image docker.io/<your-dockerhub-username>/finassist-backend:v1 \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 --max-replicas 2 \
  --cpu 0.5 --memory 1Gi \
  --env-vars \
    DATABASE_URL="secretref:database-url" \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    CORS_ORIGINS="http://localhost:5173" \
    API_PUBLIC_URL="secretref:api-public-url" \
    WATSONX_API_KEY="" WATSONX_PROJECT_ID="" WATSONX_URL="" \
    ORCHESTRATE_URL="" ORCHESTRATE_API_KEY="" \
  --secrets \
    database-url="postgresql+psycopg://finassist:<password>@finassist-pg.postgres.database.azure.com:5432/finassist?sslmode=require" \
    api-public-url="PLACEHOLDER_UNTIL_STEP_4"
```

`CORS_ORIGINS` and `api-public-url` are placeholders — both get fixed up
once real URLs exist, same two-step pattern as the IBM guide (Step 5
below closes this loop).

## 4. Get the backend's URL, then fix `API_PUBLIC_URL`

```bash
BACKEND_URL=$(az containerapp show --name finassist-backend --resource-group finassist-rg \
  --query properties.configuration.ingress.fqdn --output tsv)
echo "https://$BACKEND_URL"

az containerapp secret set --name finassist-backend --resource-group finassist-rg \
  --secrets api-public-url="https://$BACKEND_URL"

az containerapp update --name finassist-backend --resource-group finassist-rg \
  --set-env-vars API_PUBLIC_URL="secretref:api-public-url"
```

This is what makes `/openapi.json` self-describing — see `app/main.py`'s
`servers` field, added specifically for this (`API_PUBLIC_URL` in
`app/config.py`).

## 5. Run migrations and seed data

Container Apps has no direct shell-exec-and-done equivalent to a Code
Engine job for one-off commands as cleanly, but `az containerapp exec`
works against a running replica:

```bash
az containerapp exec --name finassist-backend --resource-group finassist-rg \
  --command "alembic upgrade head"

az containerapp exec --name finassist-backend --resource-group finassist-rg \
  --command "python -m scripts.seed_demo_data"
```

## 6. Build and deploy the frontend — after the backend URL exists

Same build-time constraint as the IBM guide: `VITE_API_BASE_URL` is baked
into the JS bundle by Vite at build time (see `frontend/Dockerfile`'s own
comment), so the backend must exist first.

```bash
cd ../frontend
docker build \
  --build-arg VITE_API_BASE_URL="https://$BACKEND_URL" \
  -t <your-dockerhub-username>/finassist-frontend:v1 .
docker push <your-dockerhub-username>/finassist-frontend:v1

az containerapp create \
  --name finassist-frontend \
  --resource-group finassist-rg \
  --environment finassist-env \
  --image docker.io/<your-dockerhub-username>/finassist-frontend:v1 \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 --max-replicas 2 \
  --cpu 0.25 --memory 0.5Gi

FRONTEND_URL=$(az containerapp show --name finassist-frontend --resource-group finassist-rg \
  --query properties.configuration.ingress.fqdn --output tsv)
echo "https://$FRONTEND_URL"
```

## 7. Close the loop: give the backend the frontend's real CORS origin

```bash
az containerapp update --name finassist-backend --resource-group finassist-rg \
  --set-env-vars CORS_ORIGINS="https://$FRONTEND_URL"
```

## 8. Verify

```bash
curl "https://$BACKEND_URL/health"
# {"status":"ok"}

curl "https://$BACKEND_URL/openapi.json" | python3 -c "import sys,json; print(json.load(sys.stdin)['servers'])"
# [{'url': 'https://finassist-backend...azurecontainerapps.io', 'description': 'production'}]
```

Open `https://$FRONTEND_URL` in a browser and run through the flows
verified locally (`frontend/README.md`'s change log).

## 9. Connect watsonx Orchestrate

This is the part that's identical regardless of which cloud hosts the
API — Orchestrate only cares that the URL is public and the document is
valid OpenAPI.

### Fetch the live spec

```bash
curl "https://$BACKEND_URL/openapi.json" > openapi.json
```

This works right now, with zero backend changes — `/openapi.json` is
generated automatically by FastAPI from your existing routes and Pydantic
schemas (`app/schemas/`). The `curl` in the earlier conversation was
exactly this command; it needed the real deployed URL in place of the
placeholder, which you now have from Step 4.

### Import it — UI path (no CLI needed)

1. In watsonx Orchestrate, open **Agent Builder** → the tool/skill
   building area (currently labelled "Build tools" / "Add tools" — exact
   wording has moved around across Orchestrate releases, look for an
   **OpenAPI** import option).
2. Choose **import from a file** and upload the `openapi.json` you just
   downloaded (some versions also accept pasting a live URL directly
   instead of uploading a file).
3. Orchestrate parses the spec and lists every operation it found. **Only
   select the ones that map to a `WorkflowPort` action**
   (`docs/orchestration.md`): `GET /api/v1/transactions/{reference}`,
   `POST /api/v1/disputes`, `POST /api/v1/support/cases`,
   `GET /api/v1/support/cases/{reference}` — not every route, and
   certainly not `/health`.
4. Because `servers` is now set (Step 4 above), Orchestrate should
   pre-fill the correct host. If it still prompts you to confirm or type
   a base URL, enter the same `https://$BACKEND_URL`.
5. Configure the connection/authentication for the tool. **Do this before
   relying on it for anything beyond a demo** — right now the backend has
   no auth (`docs/security.md`), so a public tool URL with no credential
   check means anyone who obtains it can call your API, not only your
   agent. At minimum, add an API-key header check on the backend and
   register that same key as the tool's credential here.
6. Save, then attach the tool to an agent and test it from Orchestrate's
   chat preview.

### Import it — CLI/ADK path (if you have `orchestrate` CLI access)

```bash
pip install --upgrade ibm-watsonx-orchestrate
orchestrate env add -n finassist-tz --url <your-orchestrate-instance-url>
orchestrate env activate finassist-tz --api-key <your-api-key>
orchestrate tools import -k openapi -f openapi.json
```

Same selection/auth caveats as the UI path apply — the CLI just automates
the click-through.

## Redeploying after a code change

```bash
# backend
docker build -t <user>/finassist-backend:v2 backend/
docker push <user>/finassist-backend:v2
az containerapp update --name finassist-backend --resource-group finassist-rg \
  --image docker.io/<user>/finassist-backend:v2

# frontend (rebuild needed even for a backend-only change, since the URL
# is baked into the bundle at build time)
docker build --build-arg VITE_API_BASE_URL="https://$BACKEND_URL" \
  -t <user>/finassist-frontend:v2 frontend/
docker push <user>/finassist-frontend:v2
az containerapp update --name finassist-frontend --resource-group finassist-rg \
  --image docker.io/<user>/finassist-frontend:v2
```

## Cost note

`--min-replicas 1` on both apps keeps them always warm, avoiding
cold-start delay when Orchestrate calls the tool — but it also means
continuous billing past whatever free-tier/trial-credit window your Azure
account has. Drop to `--min-replicas 0` between demo sessions if that
matters; the trade-off is a cold start on the next request.
