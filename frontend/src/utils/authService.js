/**
 * Authentication service. Components talk only to `authService`; the provider behind it is chosen by
 * VITE_AUTH_PROVIDER:
 *
 *   local (default)  Accounts are stored in this browser (localStorage) with PBKDF2-hashed passwords and
 *                    the session lives in sessionStorage. This is a self-contained demo store, not a
 *                    substitute for a server: anyone with access to the browser profile can read it.
 *   api              Delegates to the backend (MongoDB Atlas behind it):
 *                      POST /auth/signup  {name,email,company,role,password}  -> 201 {user}
 *                      POST /auth/signin  {email,password}                    -> {token,user}
 *                      GET  /auth/me                                          -> {user}
 *                      POST /auth/signout
 *
 * Public user shape: { id, name, email, company, role }.
 */
import { config, isApiMode } from "../config/env";
import { api, tokenStore, ApiError } from "./apiClient";

export const ROLES = [
  "Lead Technical Recruiter",
  "Talent Acquisition Partner",
  "Engineering Hiring Manager",
  "HR Business Partner",
  "Technical Interviewer",
];

export const MIN_PASSWORD_LENGTH = 8;
export const PASSWORD_RULE = `At least ${MIN_PASSWORD_LENGTH} characters with an uppercase letter, a lowercase letter, a number and a special character.`;

/** null when the password is strong enough, otherwise the message to show. */
export function passwordProblem(password) {
  const p = password || "";
  const ok = p.length >= MIN_PASSWORD_LENGTH && /[a-z]/.test(p) && /[A-Z]/.test(p) && /\d/.test(p) && /[^A-Za-z0-9]/.test(p);
  return ok ? null : `Password must have ${PASSWORD_RULE.charAt(0).toLowerCase()}${PASSWORD_RULE.slice(1)}`;
}
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const isGmail = (email) => /@gmail\.com$/i.test((email || "").trim());

export class AuthError extends Error {}

// Demo account for reviewers/testers. Only exists in the browser-local provider, never against a real backend,
// and can be switched off with VITE_SEED_DEMO_ACCOUNT=off.
export const DEMO_ACCOUNT = {
  name: "Yashashwini",
  email: "recruiter@techcorp.com",
  password: "password123",
  role: "Lead Technical Recruiter",
  company: "TechCorp Global",
};
export const isDemoAccountEnabled = config.seedDemoAccount && !isApiMode(config.authProvider);

/** "" or a plausible mobile number: 10 digits (read as Indian) or +country code and 10 to 14 digits. */
export const phoneProblem = (phone) => {
  const p = (phone || "").replace(/[\s().-]/g, "");
  return !p || /^\d{10}$/.test(p) || /^\+\d{10,14}$/.test(p) ? null : "Enter a valid mobile number, or leave it empty.";
};

export function validateSignUp({ name, email, company, role, password, phone }) {
  if (!name?.trim()) return "Enter your full name.";
  if (!EMAIL_RE.test(email?.trim() || "")) return "Enter a valid email address.";
  if (!isGmail(email)) return "Only Gmail addresses (name@gmail.com) can sign up.";
  if (!company?.trim()) return "Enter your company.";
  if (!ROLES.includes(role)) return "Choose your role.";
  return phoneProblem(phone) || passwordProblem(password);
}

/* -------------------------------------------------------------------------------------------- */
/* Local provider                                                                                */
/* -------------------------------------------------------------------------------------------- */
const USERS_KEY = "ats.users.v1";
const SESSION_KEY = "ats.session.v1";
const PBKDF2_ITERATIONS = 200_000;

const readJson = (storage, key, fallback) => {
  try {
    const raw = storage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
};
const writeJson = (storage, key, value) => {
  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
};

const toHex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
const fromHex = (hex) => new Uint8Array(hex.match(/.{2}/g).map((h) => parseInt(h, 16)));

async function derive(password, saltBytes, iterations) {
  if (!globalThis.crypto?.subtle) {
    throw new AuthError("Secure password hashing needs HTTPS or localhost.");
  }
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, [
    "deriveBits",
  ]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt: saltBytes, iterations, hash: "SHA-256" },
    key,
    256,
  );
  return toHex(bits);
}

const publicUser = ({ id, name, email, company, role }) => ({ id, name, email, company, role });
const normEmail = (e) => e.trim().toLowerCase();

async function createLocalUser(form) {
  const users = readJson(localStorage, USERS_KEY, []);
  const email = normEmail(form.email);
  if (users.some((u) => u.email === email)) throw new AuthError("An account with this email already exists.");

  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await derive(form.password, salt, PBKDF2_ITERATIONS);
  const user = {
    id: crypto.randomUUID(),
    name: form.name.trim(),
    email,
    company: form.company.trim(),
    role: form.role,
    phone: (form.phone || "").trim(),
    salt: toHex(salt),
    hash,
    iterations: PBKDF2_ITERATIONS,
    createdAt: new Date().toISOString(),
  };
  if (!writeJson(localStorage, USERS_KEY, [...users, user])) {
    throw new AuthError("Could not save your account (browser storage is unavailable).");
  }
  return publicUser(user);
}

// Idempotent: creates the demo account only when it is missing.
async function ensureDemoAccount() {
  if (!isDemoAccountEnabled) return;
  const exists = readJson(localStorage, USERS_KEY, []).some((u) => u.email === DEMO_ACCOUNT.email);
  if (!exists) {
    try {
      await createLocalUser(DEMO_ACCOUNT);
    } catch {
      /* storage unavailable: sign-in will simply fail with the normal message */
    }
  }
}

const localProvider = {
  async signUp(form) {
    const problem = validateSignUp(form);
    if (problem) throw new AuthError(problem);
    await ensureDemoAccount();
    return createLocalUser(form);
  },

  async signIn({ email, password }) {
    await ensureDemoAccount();
    const user = readJson(localStorage, USERS_KEY, []).find((u) => u.email === normEmail(email || ""));
    // One message for unknown email and wrong password, so accounts can't be enumerated.
    const fail = () => new AuthError("Incorrect email or password.");
    if (!user) throw fail();
    const hash = await derive(password || "", fromHex(user.salt), user.iterations);
    if (hash !== user.hash) throw fail();

    const session = { token: toHex(crypto.getRandomValues(new Uint8Array(16))), user: publicUser(user) };
    writeJson(sessionStorage, SESSION_KEY, session);
    return session.user;
  },

  async getSession() {
    return readJson(sessionStorage, SESSION_KEY, null)?.user || null;
  },

  async signOut() {
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch {
      /* ignore */
    }
  },
};

/* -------------------------------------------------------------------------------------------- */
/* API provider (MongoDB Atlas behind the backend)                                               */
/* -------------------------------------------------------------------------------------------- */
const asAuthError = (err) => (err instanceof ApiError ? new AuthError(err.message) : err);

const apiProvider = {
  async signUp(form) {
    const problem = validateSignUp(form);
    if (problem) throw new AuthError(problem);
    try {
      const res = await api.post("/auth/signup", { ...form, email: normEmail(form.email) });
      return res.user;
    } catch (err) {
      throw asAuthError(err);
    }
  },

  async signIn({ email, password }) {
    try {
      const res = await api.post("/auth/signin", { email: normEmail(email || ""), password });
      tokenStore.set(res.token);
      return res.user;
    } catch (err) {
      throw asAuthError(err);
    }
  },

  async getSession() {
    if (!tokenStore.get()) return null;
    try {
      return (await api.get("/auth/me")).user;
    } catch {
      tokenStore.clear();
      return null;
    }
  },

  async signOut() {
    try {
      await api.post("/auth/signout");
    } catch {
      /* the token is dropped regardless */
    }
    tokenStore.clear();
  },
};

/* -------------------------------------------------------------------------------------------- */
/* Google Sign-In (Google Identity Services)                                                     */
/* -------------------------------------------------------------------------------------------- */
// With VITE_GOOGLE_CLIENT_ID set, the Google button is shown. In "api" auth mode the ID token is sent to
// POST /auth/google, which verifies it with Google, stores the user in MongoDB and returns a session
// token. In "local" mode there is no server, so the token is only checked in the browser (audience,
// issuer, expiry): treat that as a UI gate, not server-side authorization.
export const isGoogleAuthEnabled = Boolean(config.googleClientId);

function decodeJwtPayload(token) {
  try {
    const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    return null;
  }
}

async function signInWithGoogle(credential) {
  if (isApiMode(config.authProvider)) {
    try {
      const res = await api.post("/auth/google", { credential });
      tokenStore.set(res.token);
      return res.user;
    } catch (err) {
      throw asAuthError(err);
    }
  }

  const claims = decodeJwtPayload(credential || "");
  const issuerOk = claims && ["accounts.google.com", "https://accounts.google.com"].includes(claims.iss);
  if (!claims || !issuerOk || claims.aud !== config.googleClientId || claims.exp * 1000 < Date.now()) {
    throw new AuthError("Google sign-in could not be verified. Please try again.");
  }
  if (!claims.email || claims.email_verified === false) {
    throw new AuthError("Your Google account email is not verified.");
  }
  if (!isGmail(claims.email)) throw new AuthError("Only @gmail.com Google accounts are accepted.");
  const user = {
    id: claims.sub,
    name: claims.name || claims.email,
    email: claims.email.toLowerCase(),
    company: claims.hd || "Google account",
    role: ROLES[0],
    picture: claims.picture,
  };
  writeJson(sessionStorage, SESSION_KEY, { token: credential, user });
  return user;
}

const needsServer = () => new AuthError("Reset by e-mail needs the online server. Use \"Reset with Google instead\".");

/** Forgot password, step 1: the server e-mails a 6-digit code (and texts it when the account has a number). */
async function requestPasswordReset(email) {
  if (!isApiMode(config.authProvider)) throw needsServer();
  try {
    return await api.post("/auth/forgot-password", { email: normEmail(email || "") });
  } catch (err) {
    throw asAuthError(err);
  }
}

/** Forgot password, step 2: the code from the e-mail plus the new password. */
async function resetPasswordWithCode({ email, code, password }) {
  const problem = passwordProblem(password);
  if (problem) throw new AuthError(problem);
  if (!isApiMode(config.authProvider)) throw needsServer();
  try {
    await api.post("/auth/reset-with-code", { email: normEmail(email || ""), code: (code || "").trim(), password });
  } catch (err) {
    throw asAuthError(err);
  }
}

/** Forgot password with Google: a Google sign-in proves the Gmail address, then the new password is saved. */
async function resetPassword({ credential, password }) {
  const problem = passwordProblem(password);
  if (problem) throw new AuthError(problem);
  if (isApiMode(config.authProvider)) {
    try {
      await api.post("/auth/reset-password", { credential, password });
      return;
    } catch (err) {
      throw asAuthError(err);
    }
  }
  const claims = decodeJwtPayload(credential || "");
  const issuerOk = claims && ["accounts.google.com", "https://accounts.google.com"].includes(claims.iss);
  if (!claims || !issuerOk || claims.aud !== config.googleClientId || claims.exp * 1000 < Date.now()) {
    throw new AuthError("Google sign-in could not be verified. Please try again.");
  }
  const users = readJson(localStorage, USERS_KEY, []);
  const user = users.find((u) => u.email === normEmail(claims.email || ""));
  if (!user) throw new AuthError("No account was found for this Gmail address. Create an account first.");
  const salt = crypto.getRandomValues(new Uint8Array(16));
  user.salt = toHex(salt);
  user.iterations = PBKDF2_ITERATIONS;
  user.hash = await derive(password, salt, PBKDF2_ITERATIONS);
  if (!writeJson(localStorage, USERS_KEY, users)) throw new AuthError("Could not save the new password (browser storage is unavailable).");
}

const baseProvider = isApiMode(config.authProvider) ? apiProvider : localProvider;
export const authService = { ...baseProvider, signInWithGoogle, resetPassword, requestPasswordReset, resetPasswordWithCode };
