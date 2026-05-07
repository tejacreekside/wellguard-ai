# Deploy WellGuard AI Live

Recommended live stack:

- Database: Neon Postgres
- Backend: Render Web Service
- Frontend: Vercel Vite app

This keeps the backend, database, and frontend separately scalable while preserving the current monorepo.

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

## 2. Deploy Backend On Render

1. Go to https://render.com.
2. New → Blueprint.
3. Connect GitHub repo: `tejacreekside/wellguard-ai`.
4. Select the repo and let Render read `render.yaml`.
5. Add this environment variable when prompted:

```text
WELLGUARD_DATABASE_URL=<your Neon connection string>
```

6. Deploy.

Expected backend URL:

```text
https://wellguard-ai-api.onrender.com
```

Check:

```text
https://wellguard-ai-api.onrender.com/health
https://wellguard-ai-api.onrender.com/docs
```

## 3. Deploy Frontend On Vercel

1. Go to https://vercel.com.
2. New Project.
3. Import GitHub repo: `tejacreekside/wellguard-ai`.
4. Set **Root Directory** to:

```text
frontend
```

5. Set environment variable:

```text
VITE_API_BASE_URL=https://wellguard-ai-api.onrender.com
```

Use your actual Render backend URL.

6. Deploy.

Expected frontend URL:

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
https://your-render-url.onrender.com/health
https://your-render-url.onrender.com/portfolio/summary
https://your-render-url.onrender.com/copilot/query?q=Which%20wells%20are%20highest%20risk%3F
```

## Notes

- Render uses `/health` as the health check path.
- Vercel requires `VITE_` prefix for Vite environment variables.
- OCC/OTC upload remains available at `/ingestion/upload-occ-data`.
- The app still falls back to generated Oklahoma-style production data if no uploaded public dataset exists.
