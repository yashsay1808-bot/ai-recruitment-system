import { useId, useState } from "react";
import { Eye, EyeOff, CheckCircle2, Wand2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ROLES, MIN_PASSWORD_LENGTH, DEMO_ACCOUNT, isDemoAccountEnabled } from "../utils/authService";

const SUCCESS_NOTICE = "Account created successfully. Please sign in with your credentials.";

const inputClass =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 " +
  "shadow-sm outline-none transition duration-150 hover:border-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100";

// Soft indigo glow top-centre, faint slate glow bottom-right, and a dotted grid that fades out from the middle.
const BACKDROP = {
  backgroundImage:
    "radial-gradient(60rem 36rem at 50% -8%, rgb(238 242 255) 0%, transparent 62%)," +
    "radial-gradient(42rem 30rem at 100% 100%, rgb(241 245 249) 0%, transparent 60%)",
};
const DOT_GRID = {
  backgroundImage: "radial-gradient(rgb(203 213 225) 1px, transparent 1px)",
  backgroundSize: "24px 24px",
  WebkitMaskImage: "radial-gradient(ellipse 55% 60% at 50% 40%, black 10%, transparent 75%)",
  maskImage: "radial-gradient(ellipse 55% 60% at 50% 40%, black 10%, transparent 75%)",
  opacity: 0.55,
};

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

function PasswordInput({ id, value, onChange, autoComplete, placeholder }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input
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

const EMPTY_SIGN_UP = { name: "", email: "", company: "", role: ROLES[0], password: "" };

export default function AuthCard() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
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

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError("");
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

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-50 px-4 py-10" style={BACKDROP}>
      <div aria-hidden="true" className="pointer-events-none absolute inset-0" style={DOT_GRID} />

      <div className="relative w-full max-w-[420px]">
        <div className="mb-7 flex flex-col items-center text-center">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-sm font-bold text-white shadow-lg shadow-indigo-600/25 ring-1 ring-inset ring-white/20">
            NX
          </div>
          <span className="mt-3 text-sm font-semibold tracking-tight text-slate-900">Nexus ATS</span>
          <span className="mt-0.5 text-xs text-slate-500">Explainable AI recruitment</span>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white/90 p-8 shadow-xl shadow-slate-200/50 backdrop-blur-sm">
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            {isSignIn ? "Sign in" : "Create your account"}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {isSignIn ? "Welcome back. Sign in to continue to your workspace." : "It only takes a minute."}
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

          {isSignIn ? (
            <form key="signin" onSubmit={handleSignIn} className="mt-5 space-y-4">
              <Field label="Corporate email">
                {(id) => (
                  <input
                    id={id}
                    type="email"
                    value={credentials.email}
                    onChange={(e) => setCredentials((c) => ({ ...c, email: e.target.value }))}
                    autoComplete="username"
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
              <Field label="Work email">
                {(id) => (
                  <input
                    id={id}
                    type="email"
                    value={form.email}
                    onChange={setField("email")}
                    autoComplete="email"
                    placeholder="you@company.com"
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
              <Field label="Role">
                {(id) => (
                  <select id={id} value={form.role} onChange={setField("role")} className={inputClass}>
                    {ROLES.map((r) => (
                      <option key={r}>{r}</option>
                    ))}
                  </select>
                )}
              </Field>
              <Field label="Password" hint={`At least ${MIN_PASSWORD_LENGTH} characters.`}>
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
        </div>

        <p className="mt-5 text-center text-sm text-slate-500">
          {isSignIn ? "Don't have an account?" : "Already have an account?"}{" "}
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
