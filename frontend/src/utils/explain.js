/**
 * Explainable AI: turns the stored scores of a candidate into plain-language reasons, so every verdict can be
 * traced to evidence (skills, experience, red flags, the council and the GitHub check). No new scoring is done here.
 */
import { FLAG_LABELS, verdictOf } from "./analytics";

const FLAG_MEANING = {
  EXPERIENCE_DEFICIT: "has less experience than the role asks for",
  REQUIRED_SKILLS_MISSING: "is missing several required skills",
  UNVERIFIED_SKILL_CLAIMS: "lists skills that no project or job shows",
  SKILL_STUFFING: "lists far more skills than the experience can support",
  NO_QUANTIFIED_IMPACT: "gives no measurable results",
  DATE_INCONSISTENCY: "has dates that do not add up",
  CONCURRENT_EMPLOYMENT_CONFLICT: "shows overlapping full-time jobs",
  FORMAT_CORRUPT: "has a damaged or unreadable layout",
  MISSING_EDUCATION: "shows no education",
};

const minYears = (role) => {
  const n = parseFloat(String(role?.minExperience || "").match(/[\d.]+/)?.[0]);
  return Number.isFinite(n) ? n : 0;
};

const VERDICT_TEXT = {
  STRONG_HIRE: "Strong Hire: the council consensus is high enough (80 or more) with no blocking red flag.",
  LEAN_HIRE: "Lean Hire: promising but with gaps to probe in an interview (council consensus 55 to 79).",
  REJECT: "Reject: the evidence does not support moving forward (council consensus below 55, or a blocking red flag).",
};

/** { verdictText, reasons: [{ tone: "good" | "warn" | "bad", text }], factors: [{ label, value, note }] } */
export function explainCandidate(c, role) {
  const reasons = [];
  const need = role?.skills?.length || 0;
  const got = (c.matchedSkills || []).length;
  const missing = c.missingSkills || [];
  const skillPct = need ? Math.round((got / need) * 100) : 0;
  if (need) {
    reasons.push({
      tone: skillPct >= 60 ? "good" : skillPct >= 35 ? "warn" : "bad",
      text: `Matches ${got} of ${need} required skills (${skillPct}%)${missing.length ? `; missing ${missing.slice(0, 3).join(", ")}` : ""}.`,
    });
  }
  const years = Number(c.experienceYears) || 0;
  const askYears = minYears(role);
  if (askYears) {
    reasons.push({
      tone: years >= askYears ? "good" : "bad",
      text: years >= askYears ? `Has ${years} years of experience; the role asks for ${askYears}+.` : `Has ${years} years of experience; the role asks for ${askYears}+.`,
    });
  }
  (c.redFlags || []).slice(0, 3).forEach((f) =>
    reasons.push({ tone: "bad", text: `${FLAG_LABELS[f] || f}: the resume ${FLAG_MEANING[f] || "raised this flag"}.` }),
  );
  if (!(c.redFlags || []).length) reasons.push({ tone: "good", text: "No red flags: the claims are consistent and backed by evidence." });
  if (c.evidenceSnippet) reasons.push({ tone: "good", text: `Evidence on file: "${c.evidenceSnippet}"` });
  const risk = c.github?.risk;
  if (risk) {
    reasons.push({
      tone: risk === "LOW" ? "good" : risk === "MEDIUM" ? "warn" : "bad",
      text: `GitHub check: ${risk.toLowerCase()} risk, authenticity score ${c.github.score ?? "n/a"}/100.`,
    });
  }
  const factors = [
    { label: "Required skills matched", value: skillPct, note: need ? `${got} of ${need}` : "no role skills" },
    { label: "Experience fit", value: askYears ? Math.min(100, Math.round((years / askYears) * 100)) : 100, note: `${years} of ${askYears || "any"} years` },
    { label: "Resume quality (ATS)", value: Math.round(Number(c.atsScore) || 0), note: `${c.atsScore ?? "n/a"} / 100` },
    { label: "Code authenticity", value: Math.round(Number(c.github?.score) || 0), note: `${c.github?.score ?? "n/a"} / 100` },
    { label: "Council consensus", value: Math.round(Number(c.councilScore) || 0), note: `${c.councilScore ?? "n/a"} / 100` },
  ];
  return { verdictText: VERDICT_TEXT[verdictOf(c)], reasons, factors };
}
