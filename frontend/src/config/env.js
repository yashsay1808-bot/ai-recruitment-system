// Single place where build-time configuration is read. Everything is optional: with no .env the
// app runs fully self-contained (local providers, bundled sample candidates).
//
// Copy `.env.example` to `.env` and set these to switch providers without touching components.
const env = import.meta.env;

export const config = {
  // Base URL of the backend (FastAPI / Node) that fronts MongoDB Atlas, GitHub and Gmail/SMTP.
  apiBaseUrl: (env.VITE_API_BASE_URL || "").replace(/\/$/, ""),

  // "local" -> accounts live in this browser only (demo). "api" -> POST /auth/* on apiBaseUrl.
  authProvider: env.VITE_AUTH_PROVIDER || "local",

  // "local" -> bundled sample candidates. "api" -> GET /candidates on apiBaseUrl (MongoDB Atlas).
  candidatesProvider: env.VITE_CANDIDATES_PROVIDER || "local",

  // Google Sign-In (Google Identity Services). When set, Google is the ONLY way to sign in.
  googleClientId: env.VITE_GOOGLE_CLIENT_ID || "",

  // GitHub OAuth: the client id is public; the secret and token exchange stay on the backend.
  githubClientId: env.VITE_GITHUB_CLIENT_ID || "",

  // Seeds recruiter@techcorp.com / password123 into the browser-local auth store (never used in "api" mode).
  seedDemoAccount: env.VITE_SEED_DEMO_ACCOUNT !== "off",

  // "off" -> invites are drafted and copied. "api" -> POST /integrations/mail/invite sends via Gmail/SMTP.
  mailProvider: env.VITE_MAIL_PROVIDER || "off",
};

// A provider set to "api" only takes effect when a base URL is configured, so a half-filled .env
// never leaves the app pointing at nothing.
export const isApiMode = (provider) => provider === "api" && Boolean(config.apiBaseUrl);
