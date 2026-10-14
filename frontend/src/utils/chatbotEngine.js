/**
 * Talent Copilot conversation engine.
 *
 * Answers are built from the loaded candidate pool and the active role (no model calls, so nothing is
 * invented). It keeps conversational context from the chat history: follow-ups such as "why?", "tell me
 * more", "what about her GitHub?" or "show more" resolve against the previous answer, lists paginate, and
 * asking the same thing twice yields a different angle instead of the same text.
 *
 * generateChatbotReply() returns { text, meta, suggestions }. Store `meta` on the assistant message and pass
 * the messages back as `history`. generateChatbotResponse() returns the text only.
 */
import { buildInterviewKit } from "./interviewQuestions";

/* -------------------------------------------------------------------------------------------- */
/* Small helpers                                                                                    */
/* -------------------------------------------------------------------------------------------- */
const norm = (s) => String(s ?? "").toLowerCase();
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const first = (name) => String(name || "").split(/\s+/)[0] || "this candidate";
const PAGE = 5;

function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
const pick = (list, seed) => list[hash(String(seed)) % list.length];
const pct = (n, d) => (d ? `${((n / d) * 100).toFixed(1)}%` : "0%");
const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);
const fix1 = (n) => (Number.isFinite(n) ? n.toFixed(1) : "n/a");
// Candidates from uploaded resumes can lack fields: print "n/a" instead of "undefined".
const nz = (x, suffix = "") => (x == null || x === "" || (typeof x === "number" && !Number.isFinite(x)) ? "n/a" : `${x}${suffix}`);
const yrs = (c) => nz(c.experienceYears, " years");
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;

const VERDICT = { STRONG_HIRE: "Strong Hire", LEAN_HIRE: "Lean Hire", REJECT: "Reject" };
const vLabel = (v) => VERDICT[v] || v || "Unrated";

const FLAG_TEXT = [
  ["REQUIRED_SKILLS_MISSING", "skills the role requires are missing from the resume"],
  ["EXPERIENCE_DEFICIT", "less experience than the role asks for"],
  ["LEVEL_MISMATCH", "experience level does not match the seniority of the role"],
  ["UNVERIFIED_SKILL_CLAIMS", "skills are listed without supporting project evidence"],
  ["SKILL_STUFFING", "a keyword-heavy skills section with little supporting detail"],
  ["NO_QUANTIFIED_IMPACT", "work is described without measurable results"],
  ["DATE_INCONSISTENCY", "gaps or overlaps in the employment dates"],
];
function explainFlag(flag) {
  const up = String(flag).toUpperCase();
  const hits = FLAG_TEXT.filter(([code]) => up.includes(code)).map(([, text]) => text);
  return hits.length ? hits.join("; ") : String(flag).toLowerCase().replace(/_/g, " ");
}

const flagsOf = (c) => (Array.isArray(c.redFlags) ? c.redFlags : []);
const skillsOf = (c) => c.matchedSkills || [];
const missingOf = (c) => c.missingSkills || [];
const gh = (c) => c.github || {};
const risk = (c) => gh(c).risk || "LOW";
const line = (c) => `**${c.name}** (Rank #${c.rank ?? "?"} • ${nz(c.matchScore, "%")} • ${vLabel(c.verdict)})`;

/* -------------------------------------------------------------------------------------------- */
/* Indexes built once per pool                                                                      */
/* -------------------------------------------------------------------------------------------- */
const SKILL_ALIASES = {
  k8s: "Kubernetes",
  js: "JavaScript",
  ts: "TypeScript",
  nodejs: "Node.js",
  node: "Node.js",
  golang: "Golang",
  postgres: "PostgreSQL",
  tf: "Terraform",
  llms: "LLM",
  genai: "LLM",
  gpt: "OpenAI API",
  sklearn: "Scikit-Learn",
  "scikit learn": "Scikit-Learn",
  "hugging face": "Hugging Face",
  huggingface: "Hugging Face",
  spark: "Apache Spark",
  pyspark: "Apache Spark",
  airflow: "Apache Airflow",
  "power-bi": "Power BI",
  powerbi: "Power BI",
  ml: "Machine Learning",
  nlp: "Natural Language Processing",
  dl: "Deep Learning",
};
const EXTRA_SKILLS = [
  "python", "pytorch", "tensorflow", "docker", "kubernetes", "aws", "gcp", "azure", "fastapi", "flask",
  "sql", "spark", "hadoop", "nlp", "transformers", "hugging face", "scikit-learn", "ci/cd", "git", "redis",
  "microservices", "linux", "cuda", "rag", "llm", "tableau", "power bi", "react", "typescript", "golang",
  "django", "celery", "graphql", "grpc", "pandas", "numpy", "c++", "rest api", "terraform", "kafka",
  "snowflake", "postgresql", "mongodb", "java", "javascript", "node.js", "next.js", "langchain", "openai api",
];

const indexCache = new WeakMap();
function getIndex(pool, role) {
  const roleSkills = role?.skills || [];
  const cached = indexCache.get(pool);
  if (cached && cached.roleKey === roleSkills.join("|")) return cached;

  const byId = new Map(pool.map((c) => [c.id, c]));
  const nameIndex = new Map();
  for (const c of pool) {
    for (const part of new Set(norm(c.name).split(/\s+/).filter((p) => p.length >= 3))) {
      if (!nameIndex.has(part)) nameIndex.set(part, []);
      nameIndex.get(part).push(c);
    }
  }

  const vocab = new Map(); // lower -> canonical display name
  const addSkill = (s) => {
    const key = norm(s).trim();
    if (key.length < 3) return;
    const cur = vocab.get(key);
    // Prefer a properly cased display name (from the data) over the lower-case built-in one.
    if (!cur || (cur === key && s.trim() !== key)) vocab.set(key, s.trim());
  };
  EXTRA_SKILLS.forEach(addSkill);
  roleSkills.forEach(addSkill);
  for (const c of pool) {
    skillsOf(c).forEach(addSkill);
    (c.partiallyMatchedSkills || []).forEach(addSkill);
    missingOf(c).forEach(addSkill);
  }
  const skillRes = [...vocab.entries()].map(([key, display]) => ({
    display,
    key,
    re: new RegExp(`(^|[^a-z0-9+#.])${esc(key)}(?![a-z0-9+#])`),
  }));

  const built = { roleKey: roleSkills.join("|"), byId, nameIndex, skillRes };
  indexCache.set(pool, built);
  return built;
}

function detectSkills(lower, index) {
  const found = new Map();
  for (const { display, re } of index.skillRes) if (re.test(lower)) found.set(norm(display), display);
  for (const [alias, canonical] of Object.entries(SKILL_ALIASES)) {
    if (new RegExp(`(^|[^a-z0-9+#.])${esc(alias)}(?![a-z0-9+#])`).test(lower)) found.set(norm(canonical), canonical);
  }
  // Prefer the longest names: "machine learning" should not also report "learning" style fragments.
  const all = [...found.values()];
  return all.filter((s) => !all.some((o) => o !== s && norm(o).includes(norm(s)) && norm(o).length > norm(s).length));
}

function skillLevel(c, skill) {
  const s = norm(skill);
  if (skillsOf(c).some((x) => norm(x) === s || norm(x).includes(s))) return "verified";
  if ((c.partiallyMatchedSkills || []).some((x) => norm(x).includes(s))) return "partial";
  if (norm(c.evidenceSnippet).includes(s) || (gh(c).languages || []).some((l) => norm(l).includes(s))) return "mentioned";
  return null;
}

/* -------------------------------------------------------------------------------------------- */
/* Understanding the question                                                                       */
/* -------------------------------------------------------------------------------------------- */
const ORDINALS = { first: 1, "1st": 1, second: 2, "2nd": 2, third: 3, "3rd": 3, fourth: 4, "4th": 4, fifth: 5, "5th": 5 };

function resolveCandidates(lower, pool, index, ctx) {
  const found = new Map();
  const ambiguous = [];

  // Full-name hits, grouped: the data can hold two different people with the same name.
  const byName = new Map();
  for (const c of pool) {
    if (norm(c.name).length > 3 && lower.includes(norm(c.name))) {
      const k = norm(c.name);
      if (!byName.has(k)) byName.set(k, []);
      byName.get(k).push(c);
    }
  }
  for (const id of lower.match(/can-[a-z0-9-]+/g) || []) {
    const c = index.byId.get(pool.find((x) => norm(x.id) === id)?.id);
    if (c) found.set(c.id, c);
  }
  const rankRe = /(?:\brank|#|\bcandidate\s*#?|\bnumber|\bno\.?)\s*(\d{1,3})\b/g;
  for (const m of lower.matchAll(rankRe)) {
    const n = Number(m[1]);
    const c = pool.find((x) => x.rank === n) || pool[n - 1];
    if (c) found.set(c.id, c);
  }
  for (const group of byName.values()) {
    if (group.length === 1) found.set(group[0].id, group[0]);
    else if (!group.some((c) => found.has(c.id))) ambiguous.push({ token: group[0].name, options: group });
  }
  for (const t of new Set(lower.match(/[a-z][a-z'.-]{2,}/g) || [])) {
    const list = index.nameIndex.get(t);
    if (!list || list.some((c) => found.has(c.id))) continue;
    if (list.length === 1) found.set(list[0].id, list[0]);
    else if (list.length <= 6) ambiguous.push({ token: t, options: list });
  }

  // "the second one" / "number 3 from that list" resolve against the list shown last time
  if (!found.size && ctx.list?.shown?.length) {
    for (const [word, n] of Object.entries(ORDINALS)) {
      if (new RegExp(`\\b${word}( one| candidate| person)?\\b`).test(lower)) {
        const c = index.byId.get(ctx.list.shown[n - 1]);
        if (c) found.set(c.id, c);
        break;
      }
    }
  }
  return { list: [...found.values()], ambiguous };
}

function parseFilters(lower) {
  const f = { verdict: null, minYears: null, maxYears: null, flagged: null, flagType: null, category: null };
  if (/\bstrong[- ]hires?\b|\bstrong candidates?\b/.test(lower)) f.verdict = "STRONG_HIRE";
  else if (/\blean[- ]hires?\b|\blean candidates?\b/.test(lower)) f.verdict = "LEAN_HIRE";
  else if (/\brejects?\b|\brejected\b|\brejections?\b|\bnot recommended\b/.test(lower)) f.verdict = "REJECT";

  let m = lower.match(/(?:more than|over|above|at least|minimum of|min|>=?|atleast)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|y)\b/);
  if (m) f.minYears = Number(m[1]);
  else if ((m = lower.match(/(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)/)) || (m = lower.match(/(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:or more|and above|plus)/))) f.minYears = Number(m[1]);
  m = lower.match(/(?:less than|under|below|at most|maximum of|max|<=?)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?|y)\b/);
  if (m) f.maxYears = Number(m[1]);
  if (f.minYears == null && f.maxYears == null) {
    if (/\b(freshers?|entry[- ]level|juniors?|early[- ]career|new grads?)\b/.test(lower)) f.maxYears = 2;
    else if (/\bseniors?\b/.test(lower) && !/\bsenior (?:machine|ml|engineer|data|business)/.test(lower)) f.minYears = 5;
  }
  if (/\b(flagged|red flags?|has flags?|with flags?|suspicious)\b/.test(lower)) f.flagged = true;
  if (/\b(clean|no red flags?|unflagged|without flags?)\b/.test(lower)) f.flagged = false;
  const types = [
    ["SKILL_STUFFING", /stuff/],
    ["EXPERIENCE_DEFICIT", /experience (deficit|gap)|too junior|not enough experience/],
    ["UNVERIFIED_SKILL_CLAIMS", /unverified|unsupported|unproven/],
    ["NO_QUANTIFIED_IMPACT", /quantif|no metrics|no measurable|no numbers/],
    ["DATE_INCONSISTENCY", /date (inconsisten|gap|mismatch)|timeline|employment gap/],
    ["REQUIRED_SKILLS_MISSING", /missing (required )?skills|lack(s|ing)? (the )?(required )?skills/],
    ["LEVEL_MISMATCH", /level mismatch|seniority mismatch/],
  ];
  for (const [code, re] of types) if (re.test(lower)) f.flagType = code;
  const cats = ["gold standard", "lateral switcher", "keyword stuffing", "corrupt layout", "early career fresher"];
  for (const cat of cats) if (lower.includes(cat)) f.category = cat;
  return f;
}

const hasFilter = (f) =>
  f.verdict || f.minYears != null || f.maxYears != null || f.flagged != null || f.flagType || f.category;

function applyFilters(pool, f, skills) {
  return pool.filter((c) => {
    if (f.verdict && c.verdict !== f.verdict) return false;
    if (f.minYears != null && !(c.experienceYears >= f.minYears)) return false;
    if (f.maxYears != null && !(c.experienceYears <= f.maxYears)) return false;
    if (f.flagged === true && !flagsOf(c).length) return false;
    if (f.flagged === false && flagsOf(c).length) return false;
    if (f.flagType && !flagsOf(c).some((x) => String(x).toUpperCase().includes(f.flagType))) return false;
    if (f.category && norm(c.category) !== f.category) return false;
    if (skills.length && !skills.every((s) => skillLevel(c, s))) return false;
    return true;
  });
}

function describeFilters(f, skills) {
  const bits = [];
  if (f.verdict) bits.push(vLabel(f.verdict));
  if (f.minYears != null) bits.push(`${f.minYears}+ years`);
  if (f.maxYears != null) bits.push(`up to ${f.maxYears} years`);
  if (f.flagType) bits.push(explainFlag(f.flagType));
  else if (f.flagged === true) bits.push("with red flags");
  if (f.flagged === false) bits.push("with no red flags");
  if (f.category) bits.push(`${f.category} category`);
  if (skills.length) bits.push(`skills: ${skills.join(", ")}`);
  return bits.join(" • ") || "all candidates";
}

const METRICS = [
  ["experience", /\b(experience|experienced|tenure|years|senior(?:ity)?)\b/, (c) => c.experienceYears, "years of experience", "yrs"],
  ["ats", /\b(ats|readab|parse|parsing|format)\b/, (c) => c.atsScore, "ATS parse score", "/100"],
  ["council", /\b(council|consensus)\b/, (c) => c.councilScore, "council consensus", "%"],
  ["github", /\b(github|repos?|open.?source|authentic)\b/, (c) => gh(c).score, "GitHub authenticity", "/100"],
  ["match", /\b(match|score|fit|overall|rank(?:ed|ing)?)\b/, (c) => c.matchScore, "match score", "%"],
];

/* -------------------------------------------------------------------------------------------- */
/* Reply builders                                                                                   */
/* -------------------------------------------------------------------------------------------- */
function makeReply(text, meta = {}, suggestions = []) {
  return { text, meta, suggestions: suggestions.filter(Boolean).slice(0, 4) };
}

function lastContext(history) {
  for (let i = history.length - 1; i >= 0; i--) {
    const m = history[i];
    if (m?.sender === "assistant" && m.meta) return m.meta;
  }
  return {};
}

function listReply({ key, title, rows, offset, ctx, rowFn, intro, intent, suggestions, repeat }) {
  const total = rows.length;
  let start = offset ?? 0;
  if (repeat > 0 && ctx.list?.key === key && start === 0) start = ctx.list.offset || 0;
  let wrapped = false;
  if (start >= total) {
    start = 0;
    wrapped = repeat > 0;
  }
  const page = rows.slice(start, start + PAGE);
  const next = start + page.length;
  const range = total > PAGE ? ` (showing ${start + 1}–${next} of ${total})` : "";
  const more = next < total ? `\n\nSay **show more** to see the next ${Math.min(PAGE, total - next)}.` : total > PAGE ? "\n\nThat's the end of the list." : "";
  const body = page.map((c, i) => rowFn(c, start + i + 1)).join("\n\n");
  const lead = [wrapped ? "You have already been through this whole list, so here it is again from the top." : "", intro || ""].filter(Boolean).join("\n\n");
  const text = `${lead ? `${lead}\n\n` : ""}**${title}${range}**\n\n${body}${more}`;
  return makeReply(
    text,
    { intent, candidateIds: page.map((c) => c.id).slice(0, 1), list: { key, title, ids: rows.map((c) => c.id), offset: next, shown: page.map((c) => c.id) } },
    suggestions || [],
  );
}

const rowStd = (c, n) =>
  `${n}. ${line(c)}\n   • ${c.title || "n/a"} • ${yrs(c)} • ATS ${nz(c.atsScore, "/100")}\n   • Skills: ${skillsOf(c).slice(0, 5).join(", ") || "none verified"}` +
  (flagsOf(c).length ? `\n   • Flags: ${flagsOf(c).map(explainFlag).join("; ")}` : "");

/* ----------------------------------- candidate answers ----------------------------------- */
function verdictNarrative(c, pool) {
  const mean = avg(pool.map((x) => x.matchScore));
  const gap = c.matchScore - mean;
  const where = gap >= 0 ? `${fix1(gap)} points above` : `${fix1(Math.abs(gap))} points below`;
  const flags = flagsOf(c);
  if (c.verdict === "STRONG_HIRE")
    return `Overall this is a strong fit: ${where} the pool average of ${fix1(mean)}%${flags.length ? `, with ${plural(flags.length, "flag")} to clear in the interview` : " and a clean audit"}.`;
  if (c.verdict === "LEAN_HIRE")
    return `A reasonable but not certain fit: ${where} the pool average of ${fix1(mean)}%. ${missingOf(c).length ? `The main gap is ${missingOf(c).slice(0, 3).join(", ")}.` : "A screening call should settle the open questions."}`;
  return `Not recommended on the current evidence: ${where} the pool average of ${fix1(mean)}%${flags.length ? `, and the audit raised ${plural(flags.length, "flag")}` : ""}.`;
}

function profileReply(c, ctx, { pool, seed }) {
  const opener = pick(
    [`Here is the snapshot for **${c.name}**.`, `**${c.name}** at a glance:`, `Pulling up **${c.name}** (${c.id}):`],
    seed + c.id,
  );
  const flags = flagsOf(c);
  const text =
    `${opener}\n\n` +
    `• **Role & level:** ${c.title || "n/a"}${c.level ? ` (${c.level})` : ""}, ${yrs(c)}\n` +
    `• **Scores:** ${nz(c.matchScore, "%")} match, ATS ${nz(c.atsScore, "/100")}, council ${nz(c.councilScore, "%")} → **${vLabel(c.verdict)}**\n` +
    `• **Audit:** ${flags.length ? `${plural(flags.length, "flag")} — ${flags.map(explainFlag).join("; ")}` : "clean, no red flags"}\n` +
    `• **Verified skills:** ${skillsOf(c).join(", ") || "none verified"}\n` +
    `• **Gaps:** ${missingOf(c).join(", ") || "none against this role"}\n` +
    `• **Evidence:** "${c.evidenceSnippet || "no project evidence captured"}"\n` +
    `• **GitHub:** ${gh(c).score ?? "n/a"}/100, ${risk(c)} risk\n` +
    `• **Compensation target:** ${c.salaryRange || "n/a"}${c.salaryInr ? ` (INR ${c.salaryInr})` : ""}\n\n` +
    verdictNarrative(c, pool);
  const f = first(c.name);
  return makeReply(text, { intent: "profile", candidateIds: [c.id] }, [
    `Why is ${f} rated ${vLabel(c.verdict)}?`,
    `Should I hire ${f}?`,
    `Interview questions for ${f}`,
    `What are ${f}'s skill gaps?`,
  ]);
}

function whyReply(c, { pool, seed }) {
  const mean = avg(pool.map((x) => x.matchScore));
  const council = gh(c) && c.council ? c.council : null;
  const agents = council
    ? [
        ["Tech lead", council.techLead],
        ["Culture & collaboration", council.culture],
        ["Fair-hiring auditor", council.fairAuditor],
        ["Seniority & compensation", council.seniorityComp],
      ]
        .filter(([, a]) => a)
        .map(([label, a]) => `  - ${label} (${a.score ?? "?"}/100): "${a.feedback || "no comment"}"`)
        .join("\n")
    : "";
  const flags = flagsOf(c);
  const reasons = [];
  reasons.push(`Match score **${c.matchScore}%** against a pool average of ${fix1(mean)}%`);
  reasons.push(`Skill coverage: ${skillsOf(c).length} verified, ${missingOf(c).length} missing${missingOf(c).length ? ` (${missingOf(c).slice(0, 4).join(", ")})` : ""}`);
  if (flags.length) reasons.push(`Audit flags: ${flags.map(explainFlag).join("; ")}`);
  reasons.push(`GitHub review: ${gh(c).score ?? "n/a"}/100 with ${risk(c)} risk`);
  if (c.atsScore < 70) reasons.push(`The resume parsed poorly (ATS ${c.atsScore}/100), which lowers confidence in the extracted data`);

  const opener = pick(
    [`Here is why **${c.name}** is rated **${vLabel(c.verdict)}**:`, `The reasoning behind **${vLabel(c.verdict)}** for **${c.name}**:`, `What drives the **${vLabel(c.verdict)}** call on **${c.name}**:`],
    seed + c.id,
  );
  const change =
    c.verdict === "STRONG_HIRE"
      ? "What could change it: an unresolved flag or a weak answer on the verification question."
      : `What would move it up: evidence for ${missingOf(c).slice(0, 2).join(" and ") || "the open gaps"}${flags.length ? " and clear answers on the flagged items" : ""}.`;
  const f = first(c.name);
  return makeReply(
    `${opener}\n\n${reasons.map((r) => `• ${r}`).join("\n")}${agents ? `\n\n**Council view:**\n${agents}` : ""}\n\n${change}`,
    { intent: "why", candidateIds: [c.id] },
    [`Should I hire ${f}?`, `Interview questions for ${f}`, `Compare ${f} with ${first(pool.find((x) => x.id !== c.id)?.name)}`],
  );
}

function decisionReply(c) {
  const flags = flagsOf(c);
  const pros = [];
  const cons = [];
  if (skillsOf(c).length >= 5) pros.push(`${skillsOf(c).length} verified skills (${skillsOf(c).slice(0, 4).join(", ")})`);
  if (c.matchScore >= 75) pros.push(`strong ${c.matchScore}% match`);
  if (c.councilScore >= 75) pros.push(`${c.councilScore}% council consensus`);
  if (risk(c) === "LOW" && gh(c).score >= 70) pros.push(`credible GitHub history (${gh(c).score}/100)`);
  if (c.evidenceSnippet) pros.push(`concrete evidence: "${c.evidenceSnippet}"`);
  if (missingOf(c).length) cons.push(`missing ${missingOf(c).slice(0, 3).join(", ")}`);
  flags.forEach((fl) => cons.push(explainFlag(fl)));
  if (risk(c) !== "LOW") cons.push(`${risk(c)} GitHub risk (${gh(c).authenticRepos ?? "?"} of ${gh(c).reposAnalyzed ?? "?"} repos look original)`);
  if (c.atsScore < 70) cons.push(`weak resume parse (ATS ${c.atsScore}/100)`);

  let call;
  if (c.verdict === "STRONG_HIRE" && risk(c) !== "HIGH") call = `**Yes, move ${first(c.name)} to a technical interview.**`;
  else if (c.verdict === "REJECT" || risk(c) === "HIGH") call = `**Not on this evidence.** I would not advance ${first(c.name)} without a strong reason.`;
  else call = `**Maybe, start with a screening call.** ${first(c.name)} is promising but has open questions.`;

  const next =
    c.verdict === "STRONG_HIRE"
      ? "Next step: schedule the technical interview and use the verification question to confirm the headline project."
      : c.verdict === "LEAN_HIRE"
        ? `Next step: a 20-minute screen focused on ${missingOf(c)[0] || (flags[0] ? explainFlag(flags[0]) : "their strongest project")}.`
        : "If you still want to consider them, probe the flagged items first and ask for a work sample.";
  const f = first(c.name);
  return makeReply(
    `${call}\n\n${pros.length ? `**In favour:**\n${pros.map((p) => `• ${p}`).join("\n")}\n\n` : ""}${cons.length ? `**Concerns:**\n${cons.map((p) => `• ${p}`).join("\n")}\n\n` : ""}${next}`,
    { intent: "decision", candidateIds: [c.id] },
    [`Interview questions for ${f}`, `Draft outreach email for ${f}`, `Why is ${f} rated ${vLabel(c.verdict)}?`],
  );
}

function skillsReply(c, { role }) {
  const roleSkills = role?.skills || [];
  const have = roleSkills.filter((s) => skillLevel(c, s));
  const lack = roleSkills.filter((s) => !skillLevel(c, s));
  const f = first(c.name);
  return makeReply(
    `**${c.name}: skills against ${role?.title || "the role"}**\n\n` +
      `• **Verified:** ${skillsOf(c).join(", ") || "none"}\n` +
      `• **Partially matched:** ${(c.partiallyMatchedSkills || []).join(", ") || "none"}\n` +
      `• **Missing for this role:** ${missingOf(c).join(", ") || "none"}\n` +
      `• **Role coverage:** ${have.length} of ${roleSkills.length} required skills (${pct(have.length, roleSkills.length)})${lack.length ? `; not shown: ${lack.slice(0, 5).join(", ")}` : ""}`,
    { intent: "skills", candidateIds: [c.id] },
    [`Should I hire ${f}?`, `Interview questions for ${f}`, `Show ${f}'s GitHub`],
  );
}

function githubReply(c, { seed }) {
  const g = gh(c);
  const f = first(c.name);
  const langs = (g.languages || []).join(", ") || "not captured";
  const verdict =
    risk(c) === "LOW" ? "The history looks authentic." : risk(c) === "MEDIUM" ? "Some of the history looks derivative; verify the main project in the interview." : "Most of the visible history looks copied or inflated; treat the GitHub claims with caution.";
  return makeReply(
    `${pick([`GitHub review for **${c.name}**:`, `What the repository audit says about **${c.name}**:`], seed + c.id)}\n\n` +
      `• **Username:** ${g.username || "n/a"}\n` +
      `• **Authenticity score:** ${g.score ?? "n/a"}/100 (${risk(c)} risk)\n` +
      `• **Repositories:** ${g.authenticRepos ?? "?"} look original out of ${g.reposAnalyzed ?? "?"} analysed, ${g.forksCount ?? "?"} forks\n` +
      `• **Signals:** ${g.archSignals ?? "?"} architecture signals, ${g.quantifiedMetrics ?? "?"} quantified results\n` +
      `• **Languages:** ${langs}\n\n${verdict}`,
    { intent: "github", candidateIds: [c.id] },
    [`Should I hire ${f}?`, `Interview questions for ${f}`, "Which candidates have high GitHub risk?"],
  );
}

function salaryReply(c, role) {
  const f = first(c.name);
  return makeReply(
    `**Compensation for ${c.name}**\n\n` +
      `• **Target:** ${c.salaryRange || "n/a"}${c.salaryInr ? ` (INR ${c.salaryInr})` : ""}\n` +
      `• **Level:** ${c.level || "n/a"}${c.bandPosPct ? `, positioned at ${c.bandPosPct}% of the band` : ""}\n` +
      `• **Role budget:** ${role?.salaryRange || "n/a"}${role?.salaryInr ? ` (INR ${role.salaryInr})` : ""}\n\n` +
      `Confirm expectations and notice period in the first call.`,
    { intent: "salary", candidateIds: [c.id] },
    [`Should I hire ${f}?`, `Draft outreach email for ${f}`],
  );
}

function interviewReply(c, role) {
  const kit = buildInterviewKit(c, role);
  const wanted = ["Technical Verification", "Skill Deep-Dive", "System Design", "Red-Flag Verification", "Behavioral & Collaboration"];
  const chosen = [];
  for (const type of wanted) {
    const q = kit.find((k) => k.type === type && !chosen.includes(k));
    if (q) chosen.push(q);
  }
  const f = first(c.name);
  return makeReply(
    `**${chosen.length} interview questions for ${c.name}** (the full kit of ${kit.length} is in the Interview Assistant tab):\n\n` +
      chosen.map((q, i) => `${i + 1}. [${q.type}] ${q.q}\n   Look for: ${q.lookFor}`).join("\n\n"),
    { intent: "interview", candidateIds: [c.id] },
    [`Should I hire ${f}?`, `Draft outreach email for ${f}`, `What are ${f}'s skill gaps?`],
  );
}

function emailReply(c, kind, { role, recruiterName, recruiterRole, company, seed }) {
  const f = first(c.name);
  const skills = skillsOf(c).slice(0, 3).join(", ") || "engineering";
  const sign = `Best regards,\n${recruiterName}\n${recruiterRole}\n${company}`;
  let body;
  if (kind === "reject") {
    body =
      `**Decline email draft for ${c.name}**\n\n**Subject:** Your application for ${role.title} at ${company}\n\n` +
      `Hi ${f},\n\nThank you for the time you put into applying for the ${role.title} role and for sharing your background with us. ` +
      `After careful review we have decided not to move forward at this stage, as we are prioritising candidates whose experience more closely matches the current requirements.\n\n` +
      `This is not a reflection of your potential, and we would be glad to stay in touch for future openings. We wish you the very best in your search.\n\n${sign}`;
  } else if (kind === "invite") {
    body =
      `**Interview invitation draft for ${c.name}**\n\n**Subject:** Interview invitation: ${role.title} at ${company}\n\n` +
      `Hi ${f},\n\nThanks again for your interest in the ${role.title} role. We would like to invite you to a 45-minute technical conversation with our team, covering your recent work with ${skills} and a short design discussion.\n\n` +
      `Could you share two or three time slots over the next week that suit you? We will confirm one and send a calendar invite with the agenda.\n\n${sign}`;
  } else {
    const subject = pick(
      [`${role.title} at ${company}: your work on ${skillsOf(c)[0] || "engineering"} stood out`, `An opportunity at ${company} that fits your ${skillsOf(c)[0] || "engineering"} background`],
      seed + c.id,
    );
    body =
      `**Outreach draft for ${c.name}**\n\n**Subject:** ${subject}\n\n` +
      `Hi ${f},\n\nI'm ${recruiterName}, ${recruiterRole} at ${company}. Your experience with ${skills} caught my attention${c.evidenceSnippet ? `, in particular: "${c.evidenceSnippet}"` : ""}.\n\n` +
      `We are growing our ${role.title} team (${role.salaryRange || "competitive band"}) and ${c.experienceYears != null ? `your ${c.experienceYears} years of experience` : "your background"} look like a strong match. Would you be open to a 20-minute introductory call this week?\n\n${sign}`;
  }
  const label = kind === "reject" ? "decline" : kind === "invite" ? "invitation" : "outreach";
  return makeReply(body, { intent: `email-${kind}`, candidateIds: [c.id] }, [
    kind === "outreach" ? `Draft an interview invitation for ${f}` : `Draft outreach email for ${f}`,
    `Interview questions for ${f}`,
    `Why is ${f} rated ${vLabel(c.verdict)}?`,
  ].filter((s) => !s.toLowerCase().includes(label)));
}

function compareReply(a, b, { seed }) {
  const rows = [
    ["Match score", a.matchScore, b.matchScore, "%"],
    ["ATS parse", a.atsScore, b.atsScore, "/100"],
    ["Council consensus", a.councilScore, b.councilScore, "%"],
    ["GitHub score", gh(a).score, gh(b).score, "/100"],
    ["Experience", a.experienceYears, b.experienceYears, " yrs"],
  ].filter(([, x, y]) => Number.isFinite(x) && Number.isFinite(y));
  let aWins = 0;
  let bWins = 0;
  const table = rows
    .map(([label, x, y, unit]) => {
      const lead = x === y ? "tie" : x > y ? first(a.name) : first(b.name);
      if (x > y) aWins++;
      if (y > x) bWins++;
      return `• **${label}:** ${x}${unit} vs ${y}${unit} (${lead === "tie" ? "tie" : `${lead} ahead`})`;
    })
    .join("\n");
  const winner = aWins === bWins ? null : aWins > bWins ? a : b;
  const loser = winner === a ? b : a;
  const verdict = winner
    ? `**${winner.name}** leads on ${Math.max(aWins, bWins)} of ${rows.length} measures${flagsOf(winner).length > flagsOf(loser).length ? ", though with more flags to clear" : ""}. ${first(loser.name)} is stronger in: ${rows.filter(([, x, y]) => (winner === a ? y > x : x > y)).map(([l]) => l.toLowerCase()).join(", ") || "no measured area"}.`
    : "These two are evenly matched; decide on the interview signal and the open flags.";
  return makeReply(
    `${pick([`Side by side: **${a.name}** vs **${b.name}**`, `**${a.name}** compared with **${b.name}**`], seed)}\n\n` +
      `• **Roles:** ${a.title || "n/a"} vs ${b.title || "n/a"}\n${table}\n` +
      `• **Verdicts:** ${vLabel(a.verdict)} vs ${vLabel(b.verdict)}\n` +
      `• **Flags:** ${flagsOf(a).length} vs ${flagsOf(b).length}\n` +
      `• **Missing skills:** ${missingOf(a).slice(0, 3).join(", ") || "none"} vs ${missingOf(b).slice(0, 3).join(", ") || "none"}\n\n${verdict}`,
    { intent: "compare", candidateIds: [(winner || a).id, (winner === a ? b : a).id] },
    [`Should I hire ${first((winner || a).name)}?`, `Why is ${first(a.name)} rated ${vLabel(a.verdict)}?`, `Interview questions for ${first((winner || a).name)}`],
  );
}

/* ------------------------------------- pool-level answers ------------------------------------ */
function statsReply(pool, role, { seed, recruiterName }) {
  const total = pool.length;
  const strong = pool.filter((c) => c.verdict === "STRONG_HIRE");
  const lean = pool.filter((c) => c.verdict === "LEAN_HIRE");
  const reject = pool.filter((c) => c.verdict === "REJECT");
  const flagged = pool.filter((c) => flagsOf(c).length);
  const highRisk = pool.filter((c) => risk(c) === "HIGH");
  const top = pool[0];
  const opener = pick(
    [`Here is the state of the pool for **${role.title}**:`, `**${total} candidates** are screened for ${role.title}. The breakdown:`, `Pool overview for ${role.title}:`],
    seed,
  );
  return makeReply(
    `${opener}\n\n` +
      `• **Candidates screened:** ${total}\n` +
      `• **Verdicts:** ${strong.length} Strong Hire (${pct(strong.length, total)}), ${lean.length} Lean Hire (${pct(lean.length, total)}), ${reject.length} Reject (${pct(reject.length, total)})\n` +
      `• **Averages:** ${fix1(avg(pool.map((c) => c.matchScore)))}% match, ATS ${fix1(avg(pool.map((c) => c.atsScore)))}/100, ${fix1(avg(pool.map((c) => c.experienceYears)))} years of experience\n` +
      `• **Audit:** ${flagged.length} candidates flagged (${pct(flagged.length, total)}); ${highRisk.length} with high GitHub risk\n` +
      `• **Top ranked:** ${top ? `${top.name} at ${top.matchScore}% (${vLabel(top.verdict)})` : "n/a"}\n\n` +
      `${strong.length === 0 ? `${first(recruiterName)}, there is no Strong Hire yet, so consider widening the shortlist to Lean Hires.` : `You can ask me to list the ${strong.length} strong hires or dig into any one of them.`}`,
    { intent: "stats", candidateIds: top ? [top.id] : [] },
    ["Show the strong hires", "Who has red flags and why?", `Who is the most experienced candidate?`, "Tell me about the role"],
  );
}

function rankingReply(pool, metric, dir, n, ctx, repeat) {
  const [, , get, label, unit] = metric;
  const sorted = pool.filter((c) => Number.isFinite(get(c))).sort((a, b) => (dir === "desc" ? get(b) - get(a) : get(a) - get(b)));
  const word = dir === "desc" ? "highest" : "lowest";
  return listReply({
    key: `rank:${label}:${dir}`,
    title: `${word[0].toUpperCase()}${word.slice(1)} ${label}`,
    rows: sorted,
    ctx,
    repeat,
    intent: "ranking",
    rowFn: (c, i) => `${i}. ${line(c)}\n   • **${label}:** ${get(c)}${unit}\n   • ${c.title || "n/a"}, ${yrs(c)}`,
    suggestions: [`Tell me about ${first(sorted[0]?.name)}`, "Show more", "Give me a pool overview"],
    offset: 0,
  });
}

function filterReply(pool, filters, skills, ctx, repeat) {
  const rows = applyFilters(pool, filters, skills).sort((a, b) => b.matchScore - a.matchScore);
  const desc = describeFilters(filters, skills);
  if (!rows.length) {
    const hint = skills.length ? `Try a single skill, or ask "who has ${skills[0]}".` : "Try loosening one of the filters.";
    return makeReply(`No candidates match **${desc}** among the ${pool.length} in the pool. ${hint}`, { intent: "filter", candidateIds: [] }, ["Give me a pool overview", "Show the strong hires", "Who has red flags and why?"]);
  }
  const key = `filter:${desc}`;
  const hasSkillFilter = skills.length > 0;
  return listReply({
    key,
    title: `${rows.length} ${rows.length === 1 ? "candidate matches" : "candidates match"}: ${desc}`,
    rows,
    ctx,
    repeat,
    intent: "filter",
    offset: 0,
    rowFn: (c, i) =>
      hasSkillFilter
        ? `${i}. ${line(c)}\n   • ${skills.map((s) => `${s}: ${skillLevel(c, s)}`).join(", ")}\n   • Evidence: "${c.evidenceSnippet || "n/a"}"\n   • GitHub ${gh(c).score ?? "n/a"}/100 (${risk(c)} risk)`
        : rowStd(c, i),
    suggestions: [`Tell me about ${first(rows[0].name)}`, rows.length > PAGE ? "Show more" : `Should I hire ${first(rows[0].name)}?`, "Give me a pool overview"],
  });
}

function flagsReply(pool, role, ctx, repeat, filters) {
  const flagged = pool.filter((c) => flagsOf(c).length);
  if (!flagged.length) return makeReply(`No red flags across the ${pool.length} candidates; every profile passed the audit.`, { intent: "flags" }, ["Show the strong hires"]);
  const counts = {};
  flagged.forEach((c) => flagsOf(c).forEach((fl) => FLAG_TEXT.forEach(([code]) => String(fl).toUpperCase().includes(code) && (counts[code] = (counts[code] || 0) + 1))));
  const summary = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([code, n]) => `• ${n} × ${explainFlag(code)}`)
    .join("\n");
  const rows = flagged
    .filter((c) => !filters.flagType || flagsOf(c).some((x) => String(x).toUpperCase().includes(filters.flagType)))
    .sort((a, b) => flagsOf(b).length - flagsOf(a).length || b.matchScore - a.matchScore);
  return listReply({
    key: `flags:${filters.flagType || "all"}`,
    title: `${rows.length} flagged candidates${filters.flagType ? ` (${explainFlag(filters.flagType)})` : ""}`,
    rows,
    ctx,
    repeat,
    intent: "flags",
    offset: 0,
    intro: `**${flagged.length} of ${pool.length}** candidates carry flags (${pct(flagged.length, pool.length)}). Most common:\n${summary}`,
    rowFn: (c, i) => `${i}. ${line(c)}\n   • ${flagsOf(c).map(explainFlag).join("; ")}\n   • GitHub: ${risk(c)} risk (${gh(c).authenticRepos ?? "?"}/${gh(c).reposAnalyzed ?? "?"} repos original)`,
    suggestions: [`Why is ${first(rows[0]?.name)} flagged?`, rows.length > PAGE ? "Show more" : null, "Which candidates have high GitHub risk?"],
  });
}

function githubPoolReply(pool, ctx, repeat) {
  const counts = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  pool.forEach((c) => (counts[risk(c)] = (counts[risk(c)] || 0) + 1));
  const rows = pool.filter((c) => risk(c) === "HIGH").sort((a, b) => (gh(a).score ?? 0) - (gh(b).score ?? 0));
  const intro = `GitHub risk across ${pool.length} candidates: **${counts.LOW} low**, **${counts.MEDIUM} medium**, **${counts.HIGH} high**.`;
  if (!rows.length) return makeReply(`${intro} Nobody is rated high risk.`, { intent: "github-pool" }, ["Give me a pool overview"]);
  return listReply({
    key: "github-high",
    title: "High GitHub risk",
    rows,
    ctx,
    repeat,
    intent: "github-pool",
    offset: 0,
    intro,
    rowFn: (c, i) => `${i}. ${line(c)}\n   • ${gh(c).authenticRepos ?? "?"} of ${gh(c).reposAnalyzed ?? "?"} repos look original, ${gh(c).forksCount ?? "?"} forks (score ${gh(c).score ?? "n/a"}/100)`,
    suggestions: [`Show ${first(rows[0].name)}'s GitHub`, rows.length > PAGE ? "Show more" : null, "Who has red flags and why?"],
  });
}

function shortlistReply(pool, n, role) {
  const clean = (c) => risk(c) !== "HIGH";
  const ordered = [
    ...pool.filter((c) => c.verdict === "STRONG_HIRE" && clean(c)),
    ...pool.filter((c) => c.verdict === "LEAN_HIRE" && clean(c)),
    ...pool.filter((c) => !(c.verdict === "STRONG_HIRE" && clean(c)) && !(c.verdict === "LEAN_HIRE" && clean(c))),
  ];
  const top = ordered.slice(0, n);
  const strongCount = top.filter((c) => c.verdict === "STRONG_HIRE").length;
  const note = strongCount < top.length ? ` Only ${strongCount} ${strongCount === 1 ? "is" : "are"} Strong Hire, so the rest are Lean Hires that need a screening call.` : "";
  return makeReply(
    `**My shortlist of ${top.length} for ${role.title}:**\n\n` +
      top.map((c, i) => `${i + 1}. ${line(c)}\n   • ${yrs(c)}; ${skillsOf(c).slice(0, 4).join(", ") || "no verified skills"}\n   • "${c.evidenceSnippet || "no evidence captured"}"\n   • Target: ${c.salaryRange || "n/a"}`).join("\n\n") +
      `\n\n${[note.trim(), "Candidates with high GitHub risk were moved down the list."].filter(Boolean).join(" ")}`,
    { intent: "shortlist", candidateIds: top.map((c) => c.id).slice(0, 1), list: { key: "shortlist", ids: top.map((c) => c.id), offset: top.length, shown: top.map((c) => c.id) } },
    [`Should I hire ${first(top[0]?.name)}?`, `Compare ${first(top[0]?.name)} and ${first(top[1]?.name)}`, `Draft outreach email for ${first(top[0]?.name)}`],
  );
}

function roleReply(pool, role) {
  const skills = role.skills || [];
  const coverage = skills
    .slice(0, 6)
    .map((s) => ({ s, n: pool.filter((c) => skillLevel(c, s) === "verified").length }))
    .sort((a, b) => b.n - a.n);
  return makeReply(
    `**${role.title}**${role.department ? ` (${role.department})` : ""}\n\n` +
      `• **Level:** ${role.level || "n/a"} • **Experience:** ${role.minExperience || "n/a"}\n` +
      `• **Budget:** ${role.salaryRange || "n/a"}${role.salaryInr ? ` (INR ${role.salaryInr})` : ""}\n` +
      `• **Brief:** ${role.description || "no description"}\n` +
      `• **Key skills:** ${skills.slice(0, 10).join(", ")}${skills.length > 10 ? ` (+${skills.length - 10} more)` : ""}\n\n` +
      `**How the pool covers them:** ${coverage.map(({ s, n }) => `${s} ${n}/${pool.length}`).join(", ")}.`,
    { intent: "role" },
    ["Show the strong hires", "Who has the required skills?", "What is the compensation band?"],
  );
}

function salaryRoleReply(pool, role) {
  const top = pool[0];
  return makeReply(
    `**Compensation for ${role.title}**\n\n• **Budget band:** ${role.salaryRange || "n/a"}${role.salaryInr ? ` (INR ${role.salaryInr})` : ""}\n• **Level:** ${role.level || "n/a"}\n` +
      (top ? `• **Top candidate:** ${top.name} targets ${top.salaryRange || "n/a"}${top.bandPosPct ? `, about ${top.bandPosPct}% of the band` : ""}\n` : "") +
      `\nAsk about a specific candidate to see their expectation against this band.`,
    { intent: "salary-role", candidateIds: top ? [top.id] : [] },
    top ? [`Compensation for ${first(top.name)}`, "Show the strong hires"] : [],
  );
}

const GLOSSARY = [
  [/ats/, "**ATS score:** how cleanly the resume could be parsed, from 0 to 100. A low score means fields may have been misread, so treat that candidate's extracted data with less confidence."],
  [/match|hybrid/, "**Match score:** the hybrid ranking that combines keyword overlap, semantic similarity with the job description, and evidence strength. Higher is a closer fit to this role."],
  [/council|agent|fair auditor/, "**Council:** four reviewers (tech lead, culture and collaboration, fair-hiring auditor, seniority and compensation) each score the candidate, and their consensus feeds the verdict."],
  [/github/, "**GitHub score:** an authenticity check of public repositories: how many look original, forks versus authored work, and signs of architecture and measurable results."],
  [/red flag|flag/, "**Red flags:** audit findings such as missing required skills, skills listed without evidence, keyword stuffing, no measurable results, date inconsistencies or an experience gap."],
  [/verdict|strong hire|lean hire|reject/, "**Verdicts:** Strong Hire means advance to a technical interview; Lean Hire means a screening call to resolve open questions; Reject means the evidence does not support moving forward."],
  [/band|level/, "**Band and level:** each role has a salary band and seniority level; a candidate's position shows where their target sits inside that band."],
];
function glossaryReply(lower) {
  const hit = GLOSSARY.find(([re]) => re.test(lower));
  return makeReply(hit ? hit[1] : GLOSSARY.map(([, t]) => t).slice(0, 4).join("\n\n"), { intent: "glossary" }, ["Give me a pool overview", "Show the strong hires", "Tell me about the role"]);
}

const HELP_GROUPS = [
  "**Look up a candidate:** \"Tell me about {n}\", \"Why is {n} rated Lean Hire?\", \"Should I hire {n}?\", \"What are {n}'s skill gaps?\"",
  "**Compare and decide:** \"Compare {n} and {m}\", \"Give me a shortlist of 5\", \"Who is the most experienced?\"",
  "**Filter the pool:** \"Show strong hires\", \"Candidates with 5+ years of Python\", \"Who has red flags?\", \"High GitHub risk\"",
  "**Take action:** \"Interview questions for {n}\", \"Draft outreach email for {n}\", \"Draft a decline email for {m}\"",
  "**Understand the data:** \"Give me a pool overview\", \"Tell me about the role\", \"What is the ATS score?\"",
];

const SUGGESTION_BANK = [
  "Give me a pool overview",
  "Show the strong hires",
  "Who has red flags and why?",
  "Who is the most experienced candidate?",
  "Which candidates have high GitHub risk?",
  "Give me a shortlist of 3",
  "Tell me about the role",
  "What is the compensation band?",
  "Candidates with 5+ years of experience",
  "Who has the required skills?",
];

/* -------------------------------------------------------------------------------------------- */
/* Main entry                                                                                       */
/* -------------------------------------------------------------------------------------------- */
export function generateChatbotReply({
  query,
  candidatesPool = [],
  activeRole = { title: "the open role", skills: [] },
  recruiterName = "the hiring team",
  recruiterRole = "Recruiter",
  company = "our company",
  history = [],
}) {
  try {
    return answer({ query, candidatesPool, activeRole, recruiterName, recruiterRole, company, history });
  } catch (err) {
    console.error("Copilot engine error:", err);
    return makeReply(
      "I hit an unexpected problem while reading the candidate data. Try rephrasing the question, or ask for a pool overview.",
      { intent: "error" },
      ["Give me a pool overview", "Show the strong hires"],
    );
  }
}

export function generateChatbotResponse(params) {
  return generateChatbotReply(params).text;
}

function answer({ query, candidatesPool: pool, activeRole: role, recruiterName, recruiterRole, company, history }) {
  if (!query || !query.trim()) {
    return makeReply("Ask me about candidates, skills, red flags, comparisons or outreach, for example \"Show the strong hires\".", {}, SUGGESTION_BANK.slice(0, 3));
  }
  if (!pool.length) {
    return makeReply("No candidates are loaded yet. Load a resume pool from the Job Management tab and I can start answering.", { intent: "empty" });
  }

  const raw = query.trim();
  const lower = norm(raw).replace(/[’‘]/g, "'");
  const words = lower.split(/\s+/).filter(Boolean);
  const index = getIndex(pool, role);
  const ctx = lastContext(history);
  const seed = `${lower}|${history.length}`;
  const repeat = history.filter((m) => m?.sender === "user" && norm(m.text).trim() === lower).length;
  const shared = { pool, role, recruiterName, recruiterRole, company, seed };
  const nameSample = (i) => first(pool[i]?.name || "Karthik");

  /* --- conversational basics --- */
  if (words.length <= 6 && /^(hi|hello|hey|hiya|good (morning|afternoon|evening)|namaste|yo)\b/.test(lower)) {
    return makeReply(
      pick(
        [
          `Hello ${first(recruiterName)}! ${pool.length} candidates are loaded for ${role.title}. What would you like to look at?`,
          `Hi ${first(recruiterName)}. I can break down the pool, compare candidates, check flags or draft emails. Where shall we start?`,
          `Hey ${first(recruiterName)}, ready when you are. ${pool.length} candidates screened for ${role.title}.`,
        ],
        seed,
      ),
      { intent: "greeting" },
      SUGGESTION_BANK.slice(0, 4),
    );
  }
  if (words.length <= 6 && /\b(thanks|thank you|thx|cheers|appreciate)\b/.test(lower)) {
    return makeReply(pick(["Happy to help. Anything else on the pool?", "You're welcome. Want me to draft the next outreach, or compare two finalists?", "Glad that helped. I can also pull interview questions for anyone on your shortlist."], seed), { intent: "thanks", candidateIds: ctx.candidateIds || [] }, ["Give me a shortlist of 3", "Give me a pool overview"]);
  }
  if (/\b(help|what can you do|capabilities|what (should|can) i ask|how (do|does) (this|it) work|commands)\b/.test(lower) && words.length <= 9) {
    const n = nameSample(0);
    const m = nameSample(1);
    return makeReply(`Here is what I can do:\n\n${HELP_GROUPS.map((g) => `• ${g.replaceAll("{n}", n).replaceAll("{m}", m)}`).join("\n")}\n\nI answer only from the loaded candidates and the active role, so nothing is invented.`, { intent: "help" }, SUGGESTION_BANK.slice(0, 4));
  }

  /* --- pagination --- */
  if (/^(show |give me |see )?(more|next|continue|keep going|go on|next page|the rest)\b(?!\s+(detail|info|step))/.test(lower) && words.length <= 5 && ctx.list?.ids) {
    const rows = ctx.list.ids.map((id) => index.byId.get(id)).filter(Boolean);
    if (ctx.list.offset >= rows.length) {
      return makeReply("That was the end of the list. Want a different cut, such as red flags or a shortlist?", { ...ctx, intent: "more" }, ["Give me a shortlist of 3", "Who has red flags and why?"]);
    }
    return listReply({ key: ctx.list.key, title: ctx.list.title, rows, offset: ctx.list.offset, ctx, repeat: 0, intent: "more", rowFn: rowStd, suggestions: ["Show more", "Give me a pool overview"] });
  }

  /* --- who is this about? --- */
  const { list: mentioned, ambiguous } = resolveCandidates(lower, pool, index, ctx);
  const pronoun = /\b(he|him|his|she|her|hers|they|them|their|this (candidate|person|one)|that (candidate|person|one)|the candidate)\b/.test(lower);
  const strictFollow =
    /^(why\b|how come|what about|and\b|tell me more|more (detail|info)|elaborate|go deeper|what else|explain|so\b|really)/.test(lower) ||
    /^(should (i|we)|is (he|she|they)|does (he|she|they)|has (he|she|they)|do they)/.test(lower);
  const poolWide = /\b(how many|overview|shortlist|candidates|everyone|everybody|the pool|all of them|strong hires|lean hires|rejects)\b/.test(lower);
  const ctxCandidate = ctx.candidateIds?.length ? index.byId.get(ctx.candidateIds[0]) : null;
  const useCtx = !mentioned.length && ctxCandidate && !poolWide && (pronoun || (strictFollow && !detectSkills(lower, index).length));
  const people = mentioned.length ? mentioned : useCtx ? [ctxCandidate] : [];
  const subject = people[0];

  const skills = detectSkills(lower, index);
  const filters = parseFilters(lower);

  /* --- ambiguous first name --- */
  if (!mentioned.length && ambiguous.length && /\b(about|who|why|should|compare|interview|email|github|salary|skills|profile|tell|draft|show)\b/.test(lower)) {
    const a = ambiguous[0];
    return makeReply(
      `I found ${a.options.length} candidates matching "${a.token}". Which one do you mean?\n\n${a.options.map((c, i) => `${i + 1}. ${line(c)} — ${c.title || "n/a"}`).join("\n")}\n\nSay the rank number (for example #${a.options[0].rank}) or "the first one".`,
      { intent: "clarify", list: { key: `clarify:${a.token}`, ids: a.options.map((c) => c.id), offset: a.options.length, shown: a.options.map((c) => c.id) } },
      a.options.slice(0, 3).map((c) => `Tell me about ${c.name} #${c.rank}`),
    );
  }

  const isEmail = /\b(e-?mail|mail|draft|message|reach out|outreach|invite|invitation|write to|compose)\b/.test(lower);
  const wantsInterview = /\binterview\b/.test(lower) && /\b(questions?|ask|prepare|prep|kit|probe)\b/.test(lower);
  const wantsCompare = /\b(compare|comparison|versus|vs\.?|difference between|better than|head to head)\b/.test(lower);

  /* --- email drafts --- */
  if (isEmail && subject && !wantsInterview) {
    const kind = /\b(reject|decline|regret|turn (him|her|them) down|not moving forward|unsuccessful)\b/.test(lower)
      ? "reject"
      : /\b(invite|invitation|schedule|interview (slot|time))\b/.test(lower)
        ? "invite"
        : "outreach";
    return emailReply(subject, kind, shared);
  }
  if (isEmail && !subject) {
    return makeReply(`Which candidate is the email for? Tell me a name or rank, for example "Draft outreach email for ${nameSample(0)}".`, { intent: "email-ask" }, [`Draft outreach email for ${nameSample(0)}`, `Draft outreach email for ${nameSample(1)}`]);
  }

  /* --- interview questions --- */
  if (wantsInterview && subject) return interviewReply(subject, role);

  /* --- comparison --- */
  if (wantsCompare || mentioned.length >= 2) {
    let [a, b] = people;
    if (!a) [a, b] = [pool[0], pool[1]];
    if (a && !b) b = pool.find((c) => c.id !== a.id) && (ctx.candidateIds?.map((id) => index.byId.get(id)).find((c) => c && c.id !== a.id) || pool.find((c) => c.id !== a.id));
    if (a && b) return compareReply(a, b, shared);
  }

  /* --- single-candidate questions --- */
  if (subject) {
    if (/\b(why|reason|explain|how come|justify|rationale|what drove|what made)\b/.test(lower) && !/\bwhy (is|are|was|were) .* flagged\b/.test(lower)) return whyReply(subject, shared);
    if (skills.length && /\b(know|knows|have|has|experience|use|used|uses|work|worked|familiar|proficient|skilled|expertise)\b/.test(lower)) {
      const f = first(subject.name);
      const rows = skills.map((s) => {
        const lvl = skillLevel(subject, s);
        const label =
          { verified: "verified on the resume", partial: "partially matched", mentioned: "mentioned in their evidence or repositories" }[lvl] ||
          "no evidence in the resume or repositories";
        return `• **${s}:** ${label}`;
      });
      const missingEvidence = skills.some((s) => !skillLevel(subject, s));
      return makeReply(
        `${pick([`On ${skills.join(" and ")} for **${subject.name}**:`, `Checking **${subject.name}** for ${skills.join(" and ")}:`], seed)}\n\n${rows.join("\n")}\n\n${
          missingEvidence ? "Where there is no evidence, ask for a concrete project in the interview." : `Evidence on file: "${subject.evidenceSnippet || "n/a"}"`
        }`,
        { intent: "skill-check", candidateIds: [subject.id] },
        [`Should I hire ${f}?`, `What are ${f}'s skill gaps?`, `Interview questions for ${f}`],
      );
    }
    if (/\bflagged\b|\bred flags?\b/.test(lower) && /\b(why|what)\b/.test(lower)) {
      const fl = flagsOf(subject);
      const f = first(subject.name);
      return makeReply(
        fl.length ? `**${subject.name}** carries ${plural(fl.length, "flag")}:\n\n${fl.map((x) => `• ${explainFlag(x)}`).join("\n")}\n\nAsk about these directly in the interview.` : `**${subject.name}** has a clean audit with no red flags.`,
        { intent: "flags-one", candidateIds: [subject.id] },
        [`Should I hire ${f}?`, `Interview questions for ${f}`],
      );
    }
    if (/\b(should (i|we)|worth|recommend|good (fit|hire|candidate)|right (fit|hire)|hire|shortlist|advance|move forward|proceed)\b/.test(lower)) return decisionReply(subject, shared);
    if (/\b(github|repos?|repositor|open.?source|commits?|forks?|authentic)\b/.test(lower)) return githubReply(subject, shared);
    if (/\b(salary|compensation|ctc|lpa|pay|paid|expect|band|budget|cost)\b/.test(lower)) return salaryReply(subject, role);
    if (/\b(skills?|competenc|strengths?|weakness|gaps?|missing|lacks?|stack|tech)\b/.test(lower)) return skillsReply(subject, shared);
    if (/^(tell me more|more (detail|info)|elaborate|go deeper|what else)/.test(lower) && ctx.intent === "profile") return whyReply(subject, shared);
    if (/^(tell me more|more (detail|info)|elaborate|go deeper|what else)/.test(lower) && (ctx.intent === "why" || ctx.intent === "decision")) return interviewReply(subject, role);
    if (repeat > 0 && ctx.intent === "profile") return whyReply(subject, shared);
    return profileReply(subject, ctx, shared);
  }

  /* --- glossary --- */
  if (/\b(what (is|are|does)|explain|meaning of|define|how (is|are) .* (calculated|computed))\b/.test(lower) && /\b(ats|match score|hybrid|council|verdict|fair auditor|red flags?|github score|strong hire|lean hire)\b/.test(lower)) {
    return glossaryReply(lower);
  }

  /* --- role questions --- */
  if (/\b(role|job description|jd|vacancy|opening|position)\b/.test(lower) && !hasFilter(filters) && !/\b(compensation|salary|budget|band|pay)\b/.test(lower)) return roleReply(pool, role, seed);

  /* --- shortlist / recommendations (unless the question names a specific measure) --- */
  if (
    /\b(shortlist|recommend|who should (i|we)|best candidates?|top candidates?|top \d+( candidates?)?|finalists?|who to (hire|interview))\b/.test(lower) &&
    !skills.length &&
    !METRICS.slice(0, 4).some(([, re]) => re.test(lower))
  ) {
    const n = Math.min(Number(lower.match(/\b(?:top|of|give me|shortlist)\s+(\d{1,2})\b/)?.[1] || 3), 10);
    return shortlistReply(pool, n, role, ctx, repeat);
  }

  /* --- extremes (most experienced, lowest score, best GitHub ...) --- */
  const extreme = lower.match(/\b(most|least|highest|lowest|best|worst|strongest|weakest|top|bottom|oldest)\b/);
  const metricHit = METRICS.find(([, re]) => re.test(lower));
  if (extreme && (metricHit || /\b(candidate|candidates|person|people|engineer|who|which|one)\b/.test(lower)) && !/\bshortlist\b/.test(lower)) {
    const metric = metricHit || METRICS[METRICS.length - 1];
    const asc = /\b(least|lowest|worst|weakest|bottom)\b/.test(lower);
    const topN = lower.match(/\b(?:top|bottom|best|worst)\s+(\d{1,2})\b/);
    return rankingReply(pool, metric, asc ? "asc" : "desc", topN ? Number(topN[1]) : PAGE, ctx, repeat);
  }

  /* --- GitHub across the pool --- */
  if (/\b(github|repos?|open.?source|authentic)\b/.test(lower)) return githubPoolReply(pool, ctx, repeat);

  /* --- salary for the role --- */
  if (/\b(salary|compensation|ctc|lpa|budget|pay band|pay|band)\b/.test(lower)) return salaryRoleReply(pool, role);

  /* --- flags --- */
  if (/\b(flags?|flagged|fraud|fake|stuffing|suspicious|inflated|cheat|unverified|audit)\b/.test(lower) && filters.flagged !== false) {
    return flagsReply(pool, role, ctx, repeat, filters);
  }

  /* --- pool statistics --- */
  if (/\b(how many|count|number of|total|overview|summary|breakdown|cohort|distribution|average|stats|statistics|snapshot|state of)\b/.test(lower) && !skills.length && !filters.minYears && !filters.maxYears) {
    return statsReply(pool, role, shared);
  }

  /* --- filtered lists: verdicts, years, categories, skills --- */
  if (hasFilter(filters) || skills.length || /\b(who (has|have|knows?|can|uses?|worked)|which candidates?|candidates? (with|who)|experience (in|with)|anyone (with|who)|competenc)\b/.test(lower)) {
    const wantSkills = skills.length ? skills : /\b(required skills|competenc|the skills)\b/.test(lower) ? (role.skills || []).slice(0, 3) : [];
    if (hasFilter(filters) || wantSkills.length) return filterReply(pool, filters, wantSkills, ctx, repeat, role);
  }

  /* --- free-text relevance search --- */
  const tokens = lower.split(/\W+/).filter((t) => t.length >= 3 && !["the", "and", "for", "with", "are", "what", "how", "who", "can", "you", "that", "this", "any", "tell", "show", "has", "have", "about"].includes(t));
  const scored = pool
    .map((c) => {
      const hay = norm([c.name, c.title, c.evidenceSnippet, c.level, ...skillsOf(c), ...missingOf(c), c.council?.techLead?.feedback, c.council?.culture?.feedback].join(" "));
      return { c, score: tokens.reduce((s, t) => s + (hay.includes(t) ? 1 : 0), 0) };
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score || b.c.matchScore - a.c.matchScore);
  if (scored.length && tokens.length) {
    return listReply({
      key: `search:${tokens.join(" ")}`,
      title: `Closest matches for "${raw}"`,
      rows: scored.map((x) => x.c),
      ctx,
      repeat,
      intent: "search",
      offset: 0,
      rowFn: (c, i) => `${i}. ${line(c)}\n   • ${c.title || "n/a"}, ${yrs(c)}\n   • Evidence: "${c.evidenceSnippet || "n/a"}"`,
      suggestions: [`Tell me about ${first(scored[0].c.name)}`, scored.length > PAGE ? "Show more" : null, "Give me a pool overview"],
    });
  }

  /* --- nothing matched: say so, and vary the suggestions --- */
  const start = hash(seed) % SUGGESTION_BANK.length;
  const sugg = Array.from({ length: 4 }, (_, i) => SUGGESTION_BANK[(start + i) % SUGGESTION_BANK.length]);
  const lastReplyWasFallback = ctx.intent === "fallback";
  return makeReply(
    `${lastReplyWasFallback ? "I still can't map that to the candidate data." : `I couldn't tie "${raw}" to anything in the candidate data.`} I can look up a candidate by name or rank, filter by verdict, years or skill, compare two people, check flags, or draft emails.\n\nTry one of these:\n${sugg.map((s, i) => `${i + 1}. "${s}"`).join("\n")}`,
    { intent: "fallback" },
    sugg,
  );
}
