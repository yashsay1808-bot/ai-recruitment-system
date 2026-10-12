/**
 * Mail integration (interview invites and recruiter notifications via Gmail / SMTP). Not wired into the UI
 * yet; the Copilot only drafts text. With VITE_MAIL_PROVIDER=api the backend does the sending:
 *
 *   POST /integrations/mail/invite  { to, subject, body, candidateId }  -> { id, status }
 */
import { config, isApiMode } from "../config/env";
import { api } from "./apiClient";

export const mailService = {
  canSend: () => config.mailProvider === "api" && isApiMode("api"),

  async sendInvite({ to, subject, body, candidateId }) {
    if (!mailService.canSend()) {
      throw new Error("Email sending is not configured (set VITE_MAIL_PROVIDER=api and VITE_API_BASE_URL).");
    }
    return api.post("/integrations/mail/invite", { to, subject, body, candidateId });
  },
};
