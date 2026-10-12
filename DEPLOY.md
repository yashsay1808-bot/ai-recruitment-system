# Deployment (all free tiers)

| Piece | Host | Root / entry |
|---|---|---|
| Streamlit app | Streamlit Community Cloud | `app.py` (uses `requirements.txt`, `packages.txt`) |
| FastAPI backend + Postgres | Render (Blueprint) | `render.yaml` (uses `requirements-api.txt`) |
| React frontend | Vercel | Root directory `frontend` |

## 0. Push to GitHub
All three hosts deploy from a GitHub repo. `.env`, `node_modules` and `dist` are already git-ignored.
The two `.db` files are local SQLite data — delete them or add `*.db` to `.gitignore` before pushing if you don't want them public.

## 1. Backend (Render)
1. Render → New → Blueprint → select the repo. It creates the API service and a free Postgres.
2. When prompted, set `CORS_ORIGINS` to a JSON list, e.g. `["https://YOUR-APP.vercel.app"]` (update after step 3).
3. Check `https://<service>.onrender.com/health` and `/docs`.
Free tier notes: service sleeps after 15 min idle (slow first request); free Postgres expires after 30 days.

## 2. Streamlit app
1. share.streamlit.io → New app → repo, branch, main file `app.py`.
2. Optional secrets (Settings → Secrets): `GEMINI_API_KEY`, `LLM_PROVIDER = "gemini"`.
Note: the SQLite DB on Streamlit Cloud is ephemeral (resets on restart).

## 3. Frontend (Vercel)
1. Vercel → Add New Project → repo → Root Directory `frontend`. Framework preset Vite is auto-detected.
2. No env vars are required (runs in self-contained local mode). To use the backend later, set `VITE_API_BASE_URL` to the Render URL.
