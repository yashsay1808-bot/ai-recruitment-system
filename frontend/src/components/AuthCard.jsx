import { useEffect, useId, useRef, useState } from "react";
import { Eye, EyeOff, CheckCircle2, Wand2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { config } from "../config/env";
import {
  ROLES,
  PASSWORD_RULE,
  passwordProblem,
  phoneProblem,
  DEMO_ACCOUNT,
  isDemoAccountEnabled,
  isGoogleAuthEnabled,
} from "../utils/authService";

const GSI_SRC = "https://accounts.google.com/gsi/client";

// Renders Google's official "Sign in with Google" button and hands the returned ID token to onCredential.
function GoogleSignIn({ onCredential, onError, label = "signin_with" }) {
  const holder = useRef(null);
  const handler = useRef(onCredential);

  useEffect(() => {
    handler.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    let cancelled = false;
    const init = () => {
      if (cancelled || !window.google?.accounts?.id || !holder.current) return;
      window.google.accounts.id.initialize({
        client_id: config.googleClientId,
        callback: (res) => handler.current(res.credential),
      });
      window.google.accounts.id.renderButton(holder.current, {
        theme: "outline",
        size: "large",
        text: label,
        shape: "rectangular",
        width: 320,
      });
    };
    if (window.google?.accounts?.id) {
      init();
    } else {
      let script = document.querySelector(`script[src="${GSI_SRC}"]`);
      if (!script) {
        script = document.createElement("script");
        script.src = GSI_SRC;
        script.async = true;
        document.head.appendChild(script);
      }
      script.addEventListener("load", init);
      script.addEventListener("error", () => onError("Could not load Google sign-in. Check your connection."));
    }
    return () => {
      cancelled = true;
    };
  }, [onError, label]);

  return <div ref={holder} className="flex min-h-[44px] justify-center" />;
}

const SUCCESS_NOTICE = "Account created successfully. Please sign in with your credentials.";

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 " +
  "shadow-sm outline-none transition duration-150 hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";

// Blocks copy, cut, paste and drag-and-drop on a field. Password managers and the browser's strong-password
// suggestion fill fields programmatically (no paste event), so those keep working.
const clipboardGuards = {
  onPaste: (e) => e.preventDefault(),
  onCopy: (e) => e.preventDefault(),
  onCut: (e) => e.preventDefault(),
  onDrop: (e) => e.preventDefault(),
};

// With `noAutofill` the field starts read-only and unlocks on focus. The browser then does not pre-fill saved
// credentials into a fresh sign-in form (for example right after logging out), but its saved-login dropdown
// still appears when the user clicks into the field.
function GuardedInput({ noAutofill = false, onFocus, ...props }) {
  const [locked, setLocked] = useState(noAutofill);
  return (
    <input
      {...props}
      {...clipboardGuards}
      readOnly={locked}
      onFocus={(e) => {
        setLocked(false);
        onFocus?.(e);
      }}
    />
  );
}

// Sky-blue gradient with soft clouds (the .sky-clouds rule in index.css).
const BACKDROP = { backgroundImage: "linear-gradient(180deg, #8dc3fb 0%, #bcdcff 45%, #eaf4ff 100%)" };

function Field({ label, children, hint }) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      {typeof children === "function" ? children(id) : children}
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

function PasswordInput({ id, value, onChange, autoComplete, placeholder, noAutofill }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <GuardedInput
        noAutofill={noAutofill}
        id={id}
        type={visible ? "text" : "password"}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        placeholder={placeholder}
        required
        className={`${inputClass} pr-10`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-slate-400 hover:text-slate-600"
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}

const EMPTY_SIGN_UP = { name: "", email: "", company: "", role: ROLES[0], phone: "", password: "" };

export default function AuthCard() {
  const { signIn, signUp, signInWithGoogle, resetPassword, requestPasswordReset, resetPasswordWithCode } = useAuth();
  const [mode, setMode] = useState("signin"); // "signin" | "signup" | "reset"
  const [newPassword, setNewPassword] = useState("");
  const [resetStep, setResetStep] = useState("email"); // "email" | "code" | "google"
  const [resetEmail, setResetEmail] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [googleBusy, setGoogleBusy] = useState(false);
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [form, setForm] = useState(EMPTY_SIGN_UP);

  const switchMode = (next) => {
    setMode(next);
    setError("");
    setNotice("");
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await signIn(credentials);
    } catch (err) {
      setError(err.message || "Could not sign in. Please try again.");
      setBusy(false);
    }
    // On success the gate swaps this card out, so there is nothing more to update here.
  };

  const handleGoogle = async (credential) => {
    setError("");
    setNotice("");
    setGoogleBusy(true);
    try {
      await signInWithGoogle(credential);
    } catch (err) {
      setError(err.message || "Could not sign in with Google. Please try again.");
      setGoogleBusy(false);
    }
    // On success the gate swaps this card out.
  };

  const openReset = () => {
    switchMode("reset");
    setResetStep("email");
    setResetEmail(credentials.email);
    setResetCode("");
    setNewPassword("");
  };

  // Forgot password, step 1: e-mail the code. The answer is the same for every address.
  const handleSendCode = async (e) => {
    e?.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const res = await requestPasswordReset(resetEmail);
      setNotice(res.message);
      setResetStep("code");
      setCooldown(30);
    } catch (err) {
      setError(err.message || "Could not send the code. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  // Forgot password, step 2: the code from the e-mail and the new password.
  const handleResetWithCode = async (e) => {
    e.preventDefault();
    setError("");
    setNotice("");
    const problem = passwordProblem(newPassword);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    try {
      await resetPasswordWithCode({ email: resetEmail, code: resetCode, password: newPassword });
      setNewPassword("");
      setResetCode("");
      setCredentials({ email: resetEmail.trim(), password: "" });
      setMode("signin");
      setNotice("Password updated. Sign in with your new password.");
    } catch (err) {
      setError(err.message || "Could not reset the password. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  // Forgot password with Google: the Google sign-in proves the Gmail address; the new password was typed before it.
  const handleReset = async (credential) => {
    setError("");
    const problem = passwordProblem(newPassword);
    if (problem) {
      setError(problem);
      return;
    }
    setGoogleBusy(true);
    try {
      await resetPassword({ credential, password: newPassword });
      setNewPassword("");
      setMode("signin");
      setNotice("Password updated. Sign in with your new password.");
    } catch (err) {
      setError(err.message || "Could not reset the password. Please try again.");
    } finally {
      setGoogleBusy(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError("");
    const phoneIssue = phoneProblem(form.phone);
    if (phoneIssue) {
      setError(phoneIssue);
      return;
    }
    setBusy(true);
    try {
      await signUp(form);
      // Account saved. Go back to Sign In (prefilled email, never the password) with a confirmation.
      setCredentials({ email: form.email.trim(), password: "" });
      setForm(EMPTY_SIGN_UP);
      setMode("signin");
      setNotice(SUCCESS_NOTICE);
    } catch (err) {
      setError(err.message || "Could not create your account. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = () => {
    setError("");
    setNotice("");
    setCredentials({ email: DEMO_ACCOUNT.email, password: DEMO_ACCOUNT.password });
  };

  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const isSignIn = mode === "signin";
  const isReset = mode === "reset";

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-50 px-4 py-10" style={BACKDROP}>
      <div aria-hidden="true" className="sky-clouds pointer-events-none absolute inset-0" />

      <div className="relative w-full max-w-[420px]">
        <div className="mb-7 flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-sky-400 text-sm font-extrabold text-white shadow-lg shadow-indigo-600/25">
            NX
          </div>
          <span className="mt-3 text-base font-extrabold tracking-tight text-slate-900">Nexus ATS</span>
          <span className="mt-0.5 text-xs font-medium text-slate-700">Explainable AI recruitment</span>
        </div>

        <div className="rounded-[28px] border border-white/70 bg-white p-8 shadow-2xl shadow-indigo-900/15">
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
            {isReset ? "Reset your password" : isSignIn ? "Sign in" : "Create your account"}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {isReset
              ? resetStep === "email"
                ? "Enter your Gmail address and we will send you a 6-digit code."
                : resetStep === "code"
                  ? "Enter the code from your e-mail (or SMS) and choose a new password."
                  : "Choose a new password, then confirm it is you with Google."
              : isSignIn
                ? "Welcome back. Sign in to continue to your workspace."
                : "It only takes a minute."}
          </p>

          {notice && (
            <div
              role="status"
              className="mt-5 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-sm text-emerald-800"
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{notice}</span>
            </div>
          )}

          {isReset && resetStep === "email" ? (
            <form key="reset-email" onSubmit={handleSendCode} className="mt-5 space-y-4">
              <Field label="Gmail address">
                {(id) => (
                  <input
                    id={id}
                    type="email"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    autoComplete="email"
                    spellCheck={false}
                    autoCapitalize="none"
                    placeholder="you@gmail.com"
                    required
                    className={inputClass}
                  />
                )}
              </Field>
              {error && (
                <p role="alert" className="text-sm text-rose-600">
                  {error}
                </p>
              )}
              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-600/20 transition duration-150 hover:bg-indigo-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Sending…" : "Send reset code"}
              </button>
              {isGoogleAuthEnabled && (
                <button type="button" onClick={() => setResetStep("google")} className="w-full text-center text-xs font-medium text-indigo-600 hover:underline">
                  Reset with Google instead
                </button>
              )}
            </form>
          ) : isReset && resetStep === "code" ? (
            <form key="reset-code" onSubmit={handleResetWithCode} className="mt-5 space-y-4">
              <Field label="6-digit code" hint={`Sent to ${resetEmail}. It is valid for 10 minutes.`}>
                {(id) => (
                  <input
                    id={id}
                    value={resetCode}
                    onChange={(e) => setResetCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    placeholder="123456"
                    required
                    minLength={6}
                    className={`${inputClass} tracking-[0.4em]`}
                  />
                )}
              </Field>
              <Field label="New password" hint={PASSWORD_RULE}>
                {(id) => (
                  <PasswordInput id={id} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" />
                )}
              </Field>
              {error && (
                <p role="alert" className="text-sm text-rose-600">
                  {error}
                </p>
              )}
              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-600/20 transition duration-150 hover:bg-indigo-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Resetting…" : "Reset password"}
              </button>
              <div className="flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={handleSendCode}
                  disabled={busy || cooldown > 0}
                  className="font-medium text-indigo-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-400 disabled:no-underline"
                >
                  {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
                </button>
                <button type="button" onClick={() => setResetStep("email")} className="font-medium text-slate-500 hover:underline">
                  Use a different e-mail
                </button>
              </div>
            </form>
          ) : isReset ? (
            <div key="reset" className="mt-5 space-y-4">
              <Field label="New password" hint={PASSWORD_RULE}>
                {(id) => (
                  <PasswordInput id={id} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} autoComplete="new-password" />
                )}
              </Field>
              {error && (
                <p role="alert" className="text-sm text-rose-600">
                  {error}
                </p>
              )}
              <p className="text-xs text-slate-500">Use the Google account that has the same Gmail address as your account.</p>
            </div>
          ) : isSignIn ? (
            <form key="signin" onSubmit={handleSignIn} className="mt-5 space-y-4">
              <Field label="Corporate email">
                {(id) => (
                  <GuardedInput
                    noAutofill
                    id={id}
                    type="email"
                    value={credentials.email}
                    onChange={(e) => setCredentials((c) => ({ ...c, email: e.target.value }))}
                    autoComplete="username"
                    spellCheck={false}
                    autoCapitalize="none"
                    placeholder="you@company.com"
                    required
                    className={inputClass}
                  />
                )}
              </Field>
              <Field label="Password">
                {(id) => (
                  <PasswordInput
                    id={id}
                    value={credentials.password}
                    onChange={(e) => setCredentials((c) => ({ ...c, password: e.target.value }))}
                    autoComplete="current-password"
                    noAutofill
                  />
                )}
              </Field>

              <button
                type="button"
                onClick={openReset}
                className="text-xs font-medium text-indigo-600 hover:text-indigo-700 hover:underline"
              >
                Forgot password?
              </button>

              {error && (
                <p role="alert" className="text-sm text-rose-600">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-600/20 transition duration-150 hover:bg-indigo-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Signing in…" : "Sign In"}
              </button>

              {isDemoAccountEnabled && (
                <button
                  type="button"
                  onClick={fillDemo}
                  className="flex w-full items-center justify-center gap-1.5 rounded-lg py-1.5 text-xs font-medium text-slate-500 transition hover:bg-slate-50 hover:text-indigo-600"
                >
                  <Wand2 className="h-3.5 w-3.5" />
                  Fill demo credentials
                </button>
              )}
            </form>
          ) : (
            <form key="signup" onSubmit={handleSignUp} className="mt-5 space-y-4">
              <Field label="Full name">
                {(id) => (
                  <input id={id} value={form.name} onChange={setField("name")} autoComplete="name" required className={inputClass} />
                )}
              </Field>
              <Field label="Gmail address">
                {(id) => (
                  <GuardedInput
                    id={id}
                    type="email"
                    value={form.email}
                    onChange={setField("email")}
                    autoComplete="email"
                    spellCheck={false}
                    autoCapitalize="none"
                    placeholder="you@gmail.com"
                    required
                    className={inputClass}
                  />
                )}
              </Field>
              <Field label="Company">
                {(id) => (
                  <input
                    id={id}
                    value={form.company}
                    onChange={setField("company")}
                    autoComplete="organization"
                    required
                    className={inputClass}
                  />
                )}
              </Field>
              <Field label="Mobile number (optional)" hint="Used to text you a password-reset code when SMS is switched on.">
                {(id) => (
                  <input id={id} type="tel" value={form.phone} onChange={setField("phone")} autoComplete="tel" placeholder="98765 43210" className={inputClass} />
                )}
              </Field>
              <Field label="Role">
                {(id) => (
                  <select id={id} value={form.role} onChange={setField("role")} className={inputClass}>
                    {ROLES.map((r) => (
                      <option key={r}>{r}</option>
                    ))}
                  </select>
                )}
              </Field>
              <Field label="Password" hint={PASSWORD_RULE}>
                {(id) => (
                  <PasswordInput id={id} value={form.password} onChange={setField("password")} autoComplete="new-password" />
                )}
              </Field>

              {error && (
                <p role="alert" className="text-sm text-rose-600">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-600/20 transition duration-150 hover:bg-indigo-700 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busy ? "Creating account…" : "Create Account"}
              </button>
            </form>
          )}

          {isGoogleAuthEnabled && (!isReset || resetStep === "google") && (
            <div className="mt-6">
              <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-slate-400">
                <span className="h-px flex-1 bg-slate-200" />
                {isReset ? "then confirm with Google" : "or"}
                <span className="h-px flex-1 bg-slate-200" />
              </div>
              <div className="mt-4">
                <GoogleSignIn key={mode} label={isReset ? "continue_with" : "signin_with"} onCredential={isReset ? handleReset : handleGoogle} onError={setError} />
              </div>
              {googleBusy && (
                <p role="status" className="mt-3 rounded-lg bg-indigo-50 px-3 py-2 text-center text-xs text-indigo-800">
                  {isReset ? "Updating your password…" : "Signing you in with Google…"} The server may need up to a minute to wake up. Please wait.
                </p>
              )}
              <p className="mt-2 text-center text-xs text-slate-500">Only @gmail.com accounts are accepted.</p>
            </div>
          )}
        </div>

        <p className="mt-5 text-center text-sm text-slate-500">
          {isReset ? "Remembered it?" : isSignIn ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => switchMode(isSignIn ? "signup" : "signin")}
            className="font-medium text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            {isSignIn ? "Sign up" : "Sign in"}
          </button>
        </p>
      </div>
    </main>
  );
}
