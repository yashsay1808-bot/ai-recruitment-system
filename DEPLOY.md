# Deployment (all free tiers)

| Piece | Host | Root / entry |
|---|---|---|
| Streamlit app | Streamlit Community Cloud | `app.py` (uses `requirements.txt`, `packages.txt`) |
| FastAPI backend | Render (Blueprint) | `render.yaml` (uses `requirements-api.txt`) |
| Accounts, sessions, candidates | MongoDB Atlas (free M0) | `MONGODB_URI` env var on the backend |
| React frontend | Vercel | Root directory `frontend` |

## 0. Push to GitHub
All three hosts deploy from a GitHub repo. `.env`, `node_modules` and `dist` are already git-ignored.
The two `.db` files are local SQLite data — delete them or add `*.db` to `.gitignore` before pushing if you don't want them public.

## 1. Backend (Render)
1. Render → New → Blueprint → select the repo. It creates the API service and a free Postgres.
2. When prompted, set `CORS_ORIGINS` to a JSON list, e.g. `["https://YOUR-APP.vercel.app"]` (update after step 3).
3. Check `https://<service>.onrender.com/health` and `/docs`.
Free tier notes: service sleeps after 15 min idle (slow first request). The legacy SQL routes use an ephemeral SQLite file; accounts and candidates are in Atlas.

## 2. Streamlit app
1. share.streamlit.io → New app → repo, branch, main file `app.py`.
2. Optional secrets (Settings → Secrets): `GEMINI_API_KEY`, `LLM_PROVIDER = "gemini"`.
Note: the SQLite DB on Streamlit Cloud is ephemeral (resets on restart).

## 3. Frontend (Vercel)
1. Vercel → Add New Project → repo → Root Directory `frontend`. Framework preset Vite is auto-detected.
2. No env vars are required (runs in self-contained local mode). To use the backend, set `VITE_API_BASE_URL` to the Render URL, `VITE_AUTH_PROVIDER=api` and `VITE_CANDIDATES_PROVIDER=api`. Add `VITE_GOOGLE_CLIENT_ID` for Google sign-in.


## Forgot-password e-mails

The "Forgot password?" flow e-mails a 6-digit code (valid 10 minutes, 5 tries, 3 codes per hour per address). Render's free plan blocks SMTP,
so the server uses the **Brevo** HTTPS API (free: 300 e-mails a day).

1. Create a free account at brevo.com and verify a sender address (Senders, Domains and Dedicated IPs -> Senders).
2. Create an API key (SMTP and API -> API keys).
3. In Render, open the service -> Environment and add `BREVO_API_KEY` (the key) and `MAIL_FROM` (the verified sender). Save; Render redeploys.
4. Optional SMS: add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_FROM`. Users who entered a mobile number at sign-up then also get the code by SMS.

Without these variables the sign-in page shows "Password reset by e-mail is not set up on this server yet", and "Reset with Google instead" still works.
