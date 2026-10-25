import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authService } from "../utils/authService";
import { warmUpApi } from "../utils/apiClient";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading"); // "loading" | "ready"

  // Restore an existing session (if any) once on load. The warm-up ping wakes the API while the user is
  // still typing or verifying with Google, so that signing in does not wait for a cold start.
  useEffect(() => {
    let cancelled = false;
    warmUpApi();
    authService
      .getSession()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setStatus("ready");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (credentials) => {
    const u = await authService.signIn(credentials);
    setUser(u);
    return u;
  }, []);

  const signInWithGoogle = useCallback(async (credential) => {
    const u = await authService.signInWithGoogle(credential);
    setUser(u);
    return u;
  }, []);

  const resetPassword = useCallback((args) => authService.resetPassword(args), []);
  const requestPasswordReset = useCallback((email) => authService.requestPasswordReset(email), []);
  const resetPasswordWithCode = useCallback((args) => authService.resetPasswordWithCode(args), []);

  // Creating an account deliberately does NOT sign the user in.
  const signUp = useCallback((form) => authService.signUp(form), []);

  const signOut = useCallback(async () => {
    await authService.signOut();
    // Stop Google from auto-selecting the previous account on the next visit.
    try {
      window.google?.accounts?.id?.disableAutoSelect?.();
    } catch {
      /* Google script not loaded: nothing to reset */
    }
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, isAuthenticated: Boolean(user), status, signIn, signInWithGoogle, resetPassword, requestPasswordReset, resetPasswordWithCode, signUp, signOut }),
    [user, status, signIn, signInWithGoogle, resetPassword, requestPasswordReset, resetPasswordWithCode, signUp, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
