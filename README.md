# LinkedIn Growth Agent

A strategic growth brain for LinkedIn. Every 7 days you upload LinkedIn's own analytics
export (`.xlsx`); a team of nine AI specialists diagnoses what happened, checks live industry
news, recalls what it has learned about your audience, and independently decides your strategy
for the week — including how often to post (which can be "post nothing this week; fix X first").

It never connects to LinkedIn, never automates posting, and never generates images. It reads
your manually-downloaded export and hands you a plan you post by hand. Image ideas are prompts only.

- **Backend:** Python + FastAPI + LangGraph (the agent) → deploys to **Render**
- **Frontend:** Next.js + TypeScript + Tailwind (the dashboard) → deploys to **Vercel**
- **Database:** Supabase (Postgres + pgvector) — already set up
- **LLM:** Groq (primary) with Google Gemini (fallback); **Search:** Tavily. All free tiers.

---

## 1. What you need (free accounts + tools)

Accounts (all have free tiers): **Supabase**, **Groq** (console.groq.com), **Google AI Studio**
(aistudio.google.com/apikey, for Gemini), **Tavily** (tavily.com). For deploying: **GitHub**,
**Render** (render.com), **Vercel** (vercel.com).

Tools on your machine: **Python 3.11+** and **Node.js LTS** (nodejs.org).

Your API keys go in local `.env` files (already git-ignored) or into the hosting dashboards —
**never** into the code or GitHub.

---

## 2. Run it locally

### Backend (terminal 1)
```powershell
cd "backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then open backend\.env and paste your real keys
uvicorn app.main:app --reload --port 8000
```
Check it: open http://localhost:8000/health → `{"status":"ok"}`.

### Frontend (terminal 2)
```powershell
cd "frontend"
npm install
copy .env.local.example .env.local   # default points at http://localhost:8000
npm run dev
```
Open **http://localhost:3000**.

### Run the tests (optional)
```powershell
cd "backend"
.\.venv\Scripts\Activate.ps1
pytest -q
```

---

## 3. Deploy to the internet

You'll do three things: the database is already live (Supabase), deploy the **backend to Render**,
then the **frontend to Vercel**, and finally tell them about each other.

### Step A — Push to GitHub
Create a new **private** GitHub repo and push this project to it. (Secrets are safe: `.env` files
are git-ignored — Section 5 shows how to verify.)

### Step B — Backend → Render
1. In Render: **New + → Blueprint**, and select your GitHub repo. Render reads `render.yaml`
   automatically and creates the API service.
2. It will **prompt you to paste each secret** (they are marked `sync: false`, so they never live
   in the repo): `GROQ_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `SUPABASE_URL`,
   `SUPABASE_SERVICE_ROLE_KEY`, and `ALLOWED_ORIGINS`.
3. For `ALLOWED_ORIGINS`, leave a placeholder for now (e.g. `http://localhost:3000`); you'll set the
   real value in Step D once Vercel gives you a URL.
4. Deploy. When it's live, note the URL, e.g. `https://linkedin-growth-agent-api.onrender.com`.
   Visit `/health` on it to confirm.

### Step C — Frontend → Vercel
1. In Vercel: **Add New → Project**, select the same GitHub repo.
2. Set **Root Directory** to `frontend` (important — the Next.js app lives in a subfolder).
3. Add one environment variable: `NEXT_PUBLIC_API_BASE` = your Render backend URL from Step B.
4. Deploy. Vercel gives you a URL, e.g. `https://your-app.vercel.app`.

### Step D — Introduce them (CORS)
Back in Render → your service → **Environment**, set `ALLOWED_ORIGINS` to your Vercel URL
(e.g. `https://your-app.vercel.app`) and save. Render redeploys. The backend now accepts the
frontend, and you're live.

> Tip: Vercel also creates preview URLs per branch. If you want previews to work, add those origins
> to `ALLOWED_ORIGINS` too (comma-separated).

---

## 4. Things to know (free-tier realities)

- **Render free tier sleeps after ~15 min idle.** The first request after it wakes takes ~50s while
  it cold-starts. Later requests are normal speed. The dashboard streams progress, so a weekly run
  still works — it just starts slowly after a nap.
- **Groq free tier has a per-minute token limit.** A full 9-specialist run can bump into it; the app
  automatically falls back to Gemini for that call, so runs still complete. If both are exhausted,
  you'll see the real error from each (never a vague "it failed").
- **Model names are environment variables.** Providers retire models often. If Groq or Gemini drops a
  model, change `GROQ_MODEL` / `GEMINI_MODEL` in the Render dashboard — a 10-second fix, no code change.
- **Embeddings are pinned to 768 dimensions** on purpose (pgvector can't index the 3072-dim default).
  Don't change `EMBEDDING_DIMENSIONS` unless you also rebuild the database index.

---

## 5. Security — verify no secrets are in git

Before (and after) pushing, from the repo root:
```powershell
git ls-files | Select-String "\.env"      # should list ONLY the two .example files
git grep -n "gsk_"                          # should find nothing (your Groq key)
```
`.gitignore` already excludes `.env`, `.env.local`, `__pycache__`, `.next`, `node_modules`, the
Python venv, the research cache, and generated plans. If you ever see a real `.env` listed by the
first command, stop and remove it from tracking before pushing.

---

## 6. Project layout
```
backend/    FastAPI + the LangGraph agent (9 specialists), parser, embeddings, memory
frontend/   Next.js dashboard (projects, upload, weekly plan, history)
render.yaml  Backend deploy blueprint for Render
```
Backend and frontend each have their own README with more detail.
