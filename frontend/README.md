# Nexus ATS: React frontend

The only frontend for this project (React 19 + Vite + Tailwind 4).

```bash
npm install
npm run dev      # http://localhost:5173
npm run build
```

## Auth

Signed-out users see only the Sign In / Sign Up card (`src/components/AuthCard.jsx`); the app in `src/App.jsx`
is not rendered until sign-in succeeds (`src/main.jsx`). Creating an account returns to Sign In with a
confirmation; it does not sign the user in.

By default accounts live in this browser (PBKDF2-hashed, `localStorage`) and the session in `sessionStorage`.
That is a self-contained demo store, not a replacement for a server.

A demo login (`recruiter@techcorp.com` / `password123`) is created automatically in local mode, and the Sign In
card has a "Fill demo credentials" link. It is never created when `VITE_AUTH_PROVIDER=api`; set
`VITE_SEED_DEMO_ACCOUNT=off` to disable it everywhere (e.g. for a shared deployment).

## Plugging in a backend (MongoDB Atlas, GitHub, Gmail)

Copy `.env.example` to `.env`. Each integration has a service module under `src/utils/` and is switched by
environment variable, so components never change:

| Concern | Module | Switch | Backend contract |
|---|---|---|---|
| Auth / users | `authService.js` | `VITE_AUTH_PROVIDER=api` | `POST /auth/signup`, `POST /auth/signin`, `GET /auth/me`, `POST /auth/signout` |
| Candidates | `candidatesService.js` | `VITE_CANDIDATES_PROVIDER=api` | `GET /candidates?pool=core12\|benchmark50\|benchmark100` |
| GitHub | `githubService.js` | `VITE_GITHUB_CLIENT_ID` | `GET /integrations/github/oauth/start`, `GET /integrations/github/inspect?user=` |
| Email | `mailService.js` | `VITE_MAIL_PROVIDER=api` | `POST /integrations/mail/invite` |

All requests go through `src/utils/apiClient.js` (base URL from `VITE_API_BASE_URL`, bearer token, normalised errors).
Secrets (GitHub client secret, SMTP credentials, Mongo URI) belong on the backend only.
