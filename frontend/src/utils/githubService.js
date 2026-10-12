/**
 * GitHub integration (live repository inspection). Not wired into the UI yet: today each candidate carries
 * a bundled `github` summary. Plug-in points, all served by the backend so tokens never reach the browser:
 *
 *   GET /integrations/github/oauth/start        -> redirects to GitHub (client id: VITE_GITHUB_CLIENT_ID)
 *   GET /integrations/github/inspect?user=<h>   -> { score, risk, repos, languages, flags }
 */
import { config, isApiMode } from "../config/env";
import { api } from "./apiClient";

export const githubService = {
  isConfigured: () => isApiMode("api") && Boolean(config.githubClientId),

  oauthStartUrl: () => `${config.apiBaseUrl}/integrations/github/oauth/start`,

  async inspectProfile(handle) {
    if (!isApiMode("api")) throw new Error("GitHub inspection needs the backend (set VITE_API_BASE_URL).");
    return api.get(`/integrations/github/inspect?user=${encodeURIComponent(handle)}`);
  },
};
