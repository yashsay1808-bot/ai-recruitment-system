/**
 * Pure functions behind the Recruiter Analytics page: every number and chart is computed from the candidates that are
 * loaded, so loading another pool (12, 50 or 100) or uploading resumes changes the whole page.
 */

export const VERDICTS = ["STRONG_HIRE", "LEAN_HIRE", "REJECT"];

export const VERDICT_META = {
  STRONG_HIRE: { label: "Strong Hire", color: "#059669", soft: "#d1fae5" },
  LEAN_HIRE: { label: "Lean Hire", color: "#d97706", soft: "#fef3c7" },
  REJECT: { label: "Reject", color: "#e11d48", soft: "#ffe4e6" },
};

export const verdictOf = (c) => (VERDICTS.includes(c?.verdict) ? c.verdict : c?.verdict === "HIRE" ? "LEAN_HIRE" : "REJECT");

const num = (v, fallback = 0) => (Number.isFinite(Number(v)) ? Number(v) : fallback);
export const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);
export const median = (xs) => {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
export const round1 = (n) => Math.round(n * 10) / 10;

export const filterCohort = (pool, cohort) => (cohort === "ALL" ? pool : pool.filter((c) => verdictOf(c) === cohort));

/** Headline numbers of a set of candidates. */
export function cohortStats(pool) {
  const n = pool.length;
  const counts = { STRONG_HIRE: 0, LEAN_HIRE: 0, REJECT: 0 };
  pool.forEach((c) => {
    counts[verdictOf(c)] += 1;
  });
  const flagged = pool.filter((c) => (c.redFlags || []).length > 0).length;
  const cleanFormat = pool.filter((c) => num(c.atsScore) >= 60 && !(c.redFlags || []).includes("FORMAT_CORRUPT")).length;
  const pct = (a) => (n ? round1((a / n) * 100) : 0);
  return {
    n,
    counts,
    shortlist: counts.STRONG_HIRE + counts.LEAN_HIRE,
    shortlistRate: pct(counts.STRONG_HIRE + counts.LEAN_HIRE),
    strongRate: pct(counts.STRONG_HIRE),
    medianMatch: round1(median(pool.map((c) => num(c.matchScore)))),
    meanMatch: round1(mean(pool.map((c) => num(c.matchScore)))),
    avgCouncil: round1(mean(pool.map((c) => num(c.councilScore)))),
    flagged,
    flagRate: pct(flagged),
    cleanFormat,
    cleanFormatRate: pct(cleanFormat),
  };
}

/** The six axes of the spider web. Each is a 0-100 score already stored on the candidate. */
export const RADAR_AXES = [
  { key: "match", label: "Skill match", get: (c) => num(c.matchScore) },
  { key: "ats", label: "Resume quality", get: (c) => num(c.atsScore) },
  { key: "council", label: "Council score", get: (c) => num(c.councilScore) },
  { key: "github", label: "Code authenticity", get: (c) => num(c.github?.score) },
  { key: "culture", label: "Culture fit", get: (c) => num(c.council?.culture?.score) },
  { key: "seniority", label: "Seniority fit", get: (c) => num(c.council?.seniorityComp?.score) },
];

/** Average of every axis for a list of candidates (zeros when the list is empty). */
export const radarValues = (list) => RADAR_AXES.map((a) => round1(mean(list.map(a.get))));

/** Score histogram: bins of 10 points, with the number of candidates of each verdict and their names. */
export function histogram(pool, step = 10) {
  const bins = [];
  for (let from = 0; from < 100; from += step) {
    bins.push({ from, to: from + step, counts: { STRONG_HIRE: 0, LEAN_HIRE: 0, REJECT: 0 }, total: 0, names: [] });
  }
  pool.forEach((c) => {
    const s = Math.min(99.999, Math.max(0, num(c.matchScore)));
    const b = bins[Math.floor(s / step)];
    b.counts[verdictOf(c)] += 1;
    b.total += 1;
    b.names.push(c.name);
  });
  return bins;
}

/** Share of the pool that shows each skill the role asks for, sorted from most to least common. */
export function skillCoverage(pool, role) {
  const skills = role?.skills || [];
  const n = pool.length;
  return skills
    .map((skill) => {
      const count = pool.filter((c) => (c.matchedSkills || []).includes(skill)).length;
      return { skill, count, pct: n ? Math.round((count / n) * 100) : 0 };
    })
    .sort((a, b) => b.count - a.count || a.skill.localeCompare(b.skill));
}

export const FLAG_LABELS = {
  EXPERIENCE_DEFICIT: "Experience deficit",
  REQUIRED_SKILLS_MISSING: "Required skills missing",
  UNVERIFIED_SKILL_CLAIMS: "Unverified skill claims",
  SKILL_STUFFING: "Skill stuffing",
  NO_QUANTIFIED_IMPACT: "No quantified impact",
  DATE_INCONSISTENCY: "Date inconsistency",
  CONCURRENT_EMPLOYMENT_CONFLICT: "Concurrent jobs",
  FORMAT_CORRUPT: "Corrupt format",
  MISSING_EDUCATION: "Missing education",
};
const prettyFlag = (code) => FLAG_LABELS[code] || code.replace(/_/g, " ").toLowerCase().replace(/^./, (m) => m.toUpperCase());

/** How often each red flag occurs, most frequent first. */
export function flagFrequency(pool) {
  const counts = new Map();
  pool.forEach((c) => (c.redFlags || []).forEach((f) => counts.set(f, (counts.get(f) || 0) + 1)));
  return [...counts.entries()]
    .map(([code, count]) => ({ code, label: prettyFlag(code), count, pct: pool.length ? Math.round((count / pool.length) * 100) : 0 }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

/** One point per candidate for the experience versus match scatter plot. */
export const scatterPoints = (pool) =>
  pool.map((c) => ({ id: c.id, name: c.name, x: num(c.experienceYears), y: num(c.matchScore), verdict: verdictOf(c), flags: c.redFlags || [] }));
