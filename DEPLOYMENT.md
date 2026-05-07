# Deploy WellGuard AI Live

Recommended free live stack:

- Database: Neon Postgres
- Frontend and Backend: Vercel

This deploys the React dashboard and FastAPI API from the same monorepo. Vercel hosts the Vite frontend and routes `/api/*` to the FastAPI Python function.

## 1. Create Neon Postgres

1. Go to https://neon.tech and create a project.
2. Open the project dashboard and click **Connect**.
3. Copy the Postgres connection string.
4. Prefer the pooled connection string for web apps unless you specifically need a direct connection.

Neon connection strings look like:

```text
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

For WellGuard, either of these forms works:

```text
postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
postgresql+psycopg2://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

## 2. Deploy Full App On Vercel

1. Go to https://vercel.com.
2. New Project.
3. Import GitHub repo: `tejacreekside/wellguard-ai`.
4. Keep the root directory as the repository root.
5. Add this environment variable:

```text
WELLGUARD_DATABASE_URL=<your Neon connection string>
```

6. Add this environment variable so the frontend calls the Vercel-hosted API:

```text
VITE_API_BASE_URL=/api
```

7. Deploy.

Expected live URL:

```text
https://wellguard-ai.vercel.app
```

## 4. Verify Live App

Open:

```text
https://your-vercel-url.vercel.app
```

Then verify API endpoints:

```text
https://your-vercel-url.vercel.app/api/health
https://your-vercel-url.vercel.app/api/portfolio/summary
https://your-vercel-url.vercel.app/api/copilot/query?q=Which%20wells%20are%20highest%20risk%3F
```

## Notes

- Vercel requires `VITE_` prefix for Vite environment variables.
- OCC/OTC upload remains available at `/api/ingestion/upload-occ-data`.
- The app still falls back to generated Oklahoma-style production data if no uploaded public dataset exists.
- Vercel Functions are serverless, so uploaded data is persisted to Neon Postgres rather than process memory.
