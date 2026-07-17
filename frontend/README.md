# LinkedIn Growth Agent — Frontend

Next.js (App Router) + TypeScript + Tailwind dashboard for the FastAPI backend.

## Run locally

1. Make sure the **backend** is running first (see `../backend`) on http://localhost:8000.
2. Install dependencies (first time only):
   ```
   npm install
   ```
3. Copy the env template and adjust if needed:
   ```
   copy .env.local.example .env.local
   ```
   `NEXT_PUBLIC_API_BASE` should point at your backend (default `http://localhost:8000`).
4. Start the dev server:
   ```
   npm run dev
   ```
5. Open http://localhost:3000

## Pages

- `/` — projects list
- `/new` — create a project
- `/projects/[id]` — dashboard (stats, cadence decision, audience)
- `/projects/[id]/upload` — drag-and-drop the LinkedIn `.xlsx` export
- `/projects/[id]/weeks/[weekId]` — the weekly plan (diagnosis, trends, posts)
- `/projects/[id]/history` — past weeks + what the agent has learned

Nothing secret lives here — the only env var is the public backend URL. All API
keys stay in the backend.
