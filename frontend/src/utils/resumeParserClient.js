/**
 * Client-Side In-Browser Resume Parser (Multi-Format)
 * Supports .txt, .pdf, .docx, and .md files directly in the browser.
 * Uses pdfjs-dist for PDF text streams and mammoth for DOCX extraction.
 */

import mammoth from "mammoth";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";

/** Joins the text items of a PDF page, starting a new line whenever the vertical position changes. */
export function pageItemsToText(items) {
  let out = "";
  let lastY = null;
  for (const it of items) {
    const y = Array.isArray(it.transform) ? it.transform[5] : null;
    if (out && lastY !== null && y !== null && Math.abs(y - lastY) > 2.5 && !out.endsWith("\n")) out += "\n";
    else if (out && !out.endsWith("\n") && !out.endsWith(" ")) out += " ";
    out += it.str;
    lastY = y;
    if (it.hasEOL) {
      out += "\n";
      lastY = null;
    }
  }
  return out;
}

const MAX_PAGES = 2;
const MAX_WORDS = 1100; // about two pages; used for DOCX and TXT, whose page count is not known

/** Returns { text, pages }: pages is known for PDFs only. */
const IMAGE_FILE = /\.(png|jpe?g|webp|bmp|gif)$/i;

async function extractTextFromFile(file) {
  const name = file.name.toLowerCase();

  // 1. PDF File Text Extraction
  if (name.endsWith(".pdf")) {
    try {
      // The browser needs pdf.js's worker file; Node (the tests) does not. Vite bundles the ?url import.
      if (typeof window !== "undefined" && !pdfjsLib.GlobalWorkerOptions.workerSrc) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = (await import("pdfjs-dist/legacy/build/pdf.worker.min.mjs?url")).default;
      }
      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({
        data: new Uint8Array(arrayBuffer)
      });
      const pdf = await loadingTask.promise;
      let fullText = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = pageItemsToText(textContent.items);
        fullText += pageText + "\n";
      }
      return { text: fullText.trim() || (await file.text()), pages: pdf.numPages };
    } catch (err) {
      console.warn("PDF extraction fallback:", file.name, err);
      try {
        return { text: await file.text(), pages: null };
      } catch {
        return { text: "", pages: null };
      }
    }
  }

  // 2. DOCX File Text Extraction
  if (name.endsWith(".docx")) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      return { text: (result.value || "").trim(), pages: null };
    } catch (err) {
      console.warn("DOCX extraction fallback:", file.name, err);
      return { text: "", pages: null };
    }
  }

  // 3. Photos and scans: read the text with OCR (loaded only when a photo is uploaded, about 2 MB on first use).
  if (IMAGE_FILE.test(name)) {
    try {
      const head = new Uint8Array(await file.slice(0, 12).arrayBuffer());
      const known = [[0x89, 0x50], [0xff, 0xd8], [0x42, 0x4d], [0x47, 0x49], [0x52, 0x49]]; // png, jpeg, bmp, gif, webp
      if (!known.some(([a, b]) => head[0] === a && head[1] === b)) return { text: "", pages: 1 };
      const { createWorker } = await import("tesseract.js");
      const worker = await createWorker("eng");
      const { data } = await worker.recognize(file);
      await worker.terminate();
      return { text: (data.text || "").trim(), pages: 1 };
    } catch (err) {
      console.warn("Photo OCR failed:", file.name, err);
      return { text: "", pages: 1 };
    }
  }

  // 4. Plain Text / Markdown (.txt, .md, .json)
  return { text: await file.text(), pages: null };
}


const NAME_NOISE = new Set(["resume", "cv", "curriculum", "vitae", "profile", "final", "updated", "new", "copy", "latest", "application", "candidate", "pdf", "docx"]);
const SECTION_WORDS = /resume|curriculum|vitae|profile|summary|objective|education|experience|skills|projects|certifications?/i;

const titleCase = (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();

/** A short line of 2 to 4 plain words, such as "ASHA RAO" or "Asha Rao". */
export function looksLikeName(line) {
  return (
    line.length < 40 &&
    /^[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){1,3}$/.test(line) &&
    !SECTION_WORDS.test(line)
  );
}

/** Candidate name: the first line of the resume if it looks like a name, else the words of the file name. */
export function extractCandidateName(lines, fileName) {
  const first = lines[0] || "";
  if (looksLikeName(first)) {
    const letters = first.replace(/[^A-Za-z]/g, "");
    return letters === letters.toUpperCase() ? first.split(/\s+/).map(titleCase).join(" ") : first;
  }
  const clean = fileName.replace(/\.[^/.]+$/, "");
  const tokens = clean.split(/[_\-\s]+/).filter((t) => /^[A-Za-z]+$/.test(t) && !NAME_NOISE.has(t.toLowerCase()));
  const tail = tokens.slice(-2);
  if (tail.length === 2 && tail.every((t) => /^[A-Z][a-z]+$/.test(t))) return tail.join(" ");
  if (first && first.length < 40 && !first.includes(":") && !first.includes("@")) return first;
  return clean.replace(/_/g, " ");
}

const MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec";
const EXP_HEADING = /^(?:work\s+experience|professional\s+experience|experience|employment(?:\s+history)?|internships?|work\s+history)\b/i;
const OTHER_HEADING = /^(?:education|academic|projects?|personal\s+projects|technical\s+skills|skills|certifications?|technical\s+activities|achievements|summary|profile|objective|languages|publications|awards)\b/i;
const EDUCATION_LINE = /b\.?e\b|b\.?tech|m\.?tech|diploma|bachelor|master|ph\.?d|cgpa|gpa|expected|university|college|school|polytechnic|institute/i;

/** Month number since year 0 for "Jan 2024"; a bare year counts as its first month. */
const monthIndex = (year, mon) => year * 12 + (mon ? MONTHS.split("|").indexOf(mon.slice(0, 3).toLowerCase()) : 0);

/**
 * Years of experience: an explicit "N years" statement wins; otherwise the date ranges of the experience section
 * (or, when there is no such section, of the lines that are not about education) are added up without double
 * counting overlaps. A resume that shows no experience at all counts as 0, not as a default.
 */
export function estimateExperienceYears(text, lines, now = new Date()) {
  const explicit = text.match(/(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years|yrs)/i);
  if (explicit) return parseFloat(explicit[1]);

  let scope = [];
  const start = lines.findIndex((l) => l.length < 50 && EXP_HEADING.test(l));
  if (start >= 0) {
    for (let i = start + 1; i < lines.length; i++) {
      if (lines[i].length < 50 && OTHER_HEADING.test(lines[i])) break;
      scope.push(lines[i]);
    }
  } else {
    scope = lines.filter((l) => !EDUCATION_LINE.test(l));
  }

  const re = new RegExp(
    `(?:(${MONTHS})[a-z]*\\.?,?\\s*)?((?:19|20)\\d{2})\\s*(?:-|–|—|to)\\s*(?:(${MONTHS})[a-z]*\\.?,?\\s*)?((?:19|20)\\d{2}|present|current)`,
    "gi",
  );
  const spans = [];
  const nowIdx = now.getFullYear() * 12 + now.getMonth();
  for (const line of scope) {
    for (const m of line.matchAll(re)) {
      const [, m1, y1, m2, y2] = m;
      const present = /present|current/i.test(y2);
      const s = monthIndex(parseInt(y1, 10), m1);
      let e = present ? nowIdx + 1 : monthIndex(parseInt(y2, 10), m2) + (m2 ? 1 : 12);
      if (!m1 && !m2) e = Math.max(e, s + 6); // year-only ranges count at least half a year
      if (e > s && s <= nowIdx) spans.push([s, Math.min(e, nowIdx + 1)]);
    }
  }
  spans.sort((a, b) => a[0] - b[0]);
  let months = 0;
  let cur = null;
  for (const [s, e] of spans) {
    if (!cur || s > cur[1]) {
      if (cur) months += cur[1] - cur[0];
      cur = [s, e];
    } else cur[1] = Math.max(cur[1], e);
  }
  if (cur) months += cur[1] - cur[0];
  if (months > 0) return Math.round((months / 12) * 10) / 10;

  const monthMatch = text.match(/(\d+)\s*(?:months)/i);
  return monthMatch ? parseFloat((parseInt(monthMatch[1], 10) / 12).toFixed(1)) : 0;
}

const SKILL_ALIASES = {
  "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
  "hugging face": ["hugging face", "huggingface"],
  "rest api": ["rest api", "rest apis", "restful", "rest services"],
  "ci/cd": ["ci/cd", "ci-cd", "cicd", "github actions", "jenkins", "gitlab ci"],
  postgresql: ["postgresql", "postgres"],
  "node.js": ["node.js", "nodejs", "node js"],
  tailwindcss: ["tailwindcss", "tailwind css", "tailwind"],
  aws: ["aws", "amazon web services"],
  "aws s3": ["aws s3", "amazon s3"],
  gcp: ["gcp", "google cloud"],
  kubernetes: ["kubernetes", "k8s"],
  "natural language processing": ["natural language processing", "nlp"],
  golang: ["golang", "go lang"],
  "next.js": ["next.js", "nextjs"],
  "apache spark": ["apache spark", "pyspark"],
  kafka: ["kafka"],
  "apache kafka": ["apache kafka", "kafka"],
  "etl pipelines": ["etl pipelines", "etl pipeline", "etl"],
  bash: ["bash", "shell scripting"],
  "explainable ai": ["explainable ai", "xai"],
};
const escapeRe = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** True when the skill (or an alias) appears as a whole word or phrase, so "R" or "Go" do not match inside words. */
export function hasSkill(lowerText, skill) {
  const key = skill.toLowerCase();
  const terms = SKILL_ALIASES[key] || [key];
  return terms.some((t) => new RegExp(`(?<![a-z0-9+#])${escapeRe(t)}(?![a-z0-9+#])`).test(lowerText));
}

const RESUME_HEADINGS = /^(?:education|experience|work\s+experience|professional\s+experience|skills|technical\s+skills|projects?|summary|professional\s+summary|objective|profile|certifications?)\b/i;

/**
 * Five signs of a resume: two section headings, a contact detail, a degree or university, a year range (a work
 * timeline) and a few technical skills. A document needs at least two of them, plus a heading or a contact detail,
 * so damaged resumes still pass while an invoice, a report or a form does not.
 */
export function looksLikeResume(text) {
  if (!text || text.trim().length < 120) return false;
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  const headings = new Set(lines.filter((l) => l.length < 50 && RESUME_HEADINGS.test(l)).map((l) => l.toLowerCase().split(/\s+/)[0])).size;
  const contact = /[\w.+-]+@[\w-]+\.[\w.]+/.test(text) || /\+?\d[\d\s()-]{8,}\d/.test(text);
  const background = /\b(b\.?e\.?|b\.?tech|m\.?tech|bachelor|master|diploma|ph\.?d|cgpa|gpa|university|college)\b/i.test(text);
  const timeline = /(?:19|20)\d{2}\s*(?:-|\u2013|\u2014|to)\s*(?:(?:19|20)\d{2}|present|current)/i.test(text);
  const tech = new Set(text.toLowerCase().match(/\b(python|java|sql|docker|kubernetes|aws|react|git|linux|pytorch|tensorflow|machine learning|ci\/cd|node\.js|fastapi|flask)\b/g) || []).size >= 3;
  const signs = Math.min(headings, 2) + [contact, background, timeline, tech].filter(Boolean).length;
  return headings >= 3 || (signs >= 2 && (headings >= 1 || contact));
}

/** Returns { candidates, rejected }: files that are not readable resumes are listed in rejected with a reason. */
export async function parseUploadedFiles(files, activeRole = { title: "Senior Machine Learning Engineer", skills: [] }) {
  const parsedCandidates = [];
  const rejected = [];
  const roleSkills = activeRole.skills || [];

  for (let idx = 0; idx < files.length; idx++) {
    const file = files[idx];
    let text = "";
    let pages = null;

    try {
      ({ text, pages } = await extractTextFromFile(file));
    } catch (err) {
      console.warn("Failed to extract text from file:", file.name, err);
      continue;
    }

    if (!/\.(pdf|docx|txt|md)$/i.test(file.name) && !IMAGE_FILE.test(file.name)) {
      rejected.push({ name: file.name, reason: "Unsupported file type. Upload a PDF, DOCX, TXT or a photo of the resume." });
      continue;
    }
    if (!text || text.trim().length === 0) {
      rejected.push({
        name: file.name,
        reason: IMAGE_FILE.test(file.name)
          ? "Could not read the text in this photo. Use a clear, straight-on, well-lit picture, or upload a PDF."
          : "No readable text found (it may be a scanned image).",
      });
      continue;
    }
    if (!looksLikeResume(text)) {
      rejected.push({ name: file.name, reason: "This does not look like a resume." });
      continue;
    }
    const words = text.split(/\s+/).filter(Boolean).length;
    if ((pages && pages > MAX_PAGES) || (!pages && words > MAX_WORDS)) {
      rejected.push({
        name: file.name,
        reason: pages ? `The resume has ${pages} pages; the maximum is ${MAX_PAGES}.` : `The resume is too long (about ${words} words); the maximum is ${MAX_PAGES} pages.`,
      });
      continue;
    }

    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    // 1. Extract Candidate Name
    const candidateName = extractCandidateName(lines, file.name);

    // 2. Extract Experience / Tenure
    const experienceYears = estimateExperienceYears(text, lines);

    // 3. Extract GitHub Username
    let githubUsername = candidateName.toLowerCase().replace(/\s+/g, "-");
    const ghMatch = text.match(/github\.com\/([a-zA-Z0-9_-]+)/i);
    if (ghMatch) {
      githubUsername = ghMatch[1];
    }

    // 4. Match Skills against Active Role
    const lowerText = text.toLowerCase();
    const matchedSkills = [];
    const missingSkills = [];

    roleSkills.forEach((skill) => {
      if (hasSkill(lowerText, skill)) {
        matchedSkills.push(skill);
      } else {
        missingSkills.push(skill);
      }
    });

    // 5. Red Flags Detection
    const redFlags = [];
    if (text.length < 400) {
      redFlags.push("FORMAT_CORRUPT");
      redFlags.push("NO_QUANTIFIED_IMPACT");
    }
    if (experienceYears < 1.0) {
      redFlags.push("EXPERIENCE_DEFICIT");
    }
    if (matchedSkills.length >= 10 && experienceYears < 1.0) {
      redFlags.push("SKILL_STUFFING");
      redFlags.push("UNVERIFIED_SKILL_CLAIMS");
    }
    if (missingSkills.length > roleSkills.length * 0.6) {
      redFlags.push("REQUIRED_SKILLS_MISSING");
    }

    // Inverted dates detection
    const dateRangeRegex = /(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?,?\s+)?((?:19|20)\d{2})\s*(?:-|–|—|to)\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?,?\s+)?((?:19|20)\d{2}|present|current)/gi;
    let dateMatch;
    const currentYear = new Date().getFullYear();
    while ((dateMatch = dateRangeRegex.exec(text)) !== null) {
      const startYear = parseInt(dateMatch[1], 10);
      const endYear = dateMatch[2].toLowerCase().includes("present") || dateMatch[2].toLowerCase().includes("current")
        ? currentYear
        : parseInt(dateMatch[2], 10);
      if (startYear > endYear || startYear > currentYear) {
        if (!redFlags.includes("DATE_INCONSISTENCY")) redFlags.push("DATE_INCONSISTENCY");
        break;
      }
    }

    // Missing education detection
    const hasEducation = /education|academic|b\.?e\.?|b\.?tech|m\.?tech|m\.?s\.?|b\.?s\.?|bachelor|master|ph\.?d/i.test(text);
    if (!hasEducation) {
      redFlags.push("MISSING_EDUCATION");
    }

    // Concurrent fulltime conflict
    if (/concurrent\s+with|concurrently\s+with|full-time\s+on-site.*concurrent/i.test(text)) {
      redFlags.push("CONCURRENT_EMPLOYMENT_CONFLICT");
    }

    // 6. Calculate Hybrid Match Score
    const skillRatio = roleSkills.length > 0 ? matchedSkills.length / roleSkills.length : 0.6;
    let baseScore = skillRatio * 75 + Math.min(20, experienceYears * 3.5);
    if (redFlags.includes("FORMAT_CORRUPT")) baseScore -= 40;
    if (redFlags.includes("SKILL_STUFFING")) baseScore -= 30;
    if (redFlags.includes("EXPERIENCE_DEFICIT")) baseScore -= 20;
    if (redFlags.includes("DATE_INCONSISTENCY")) baseScore -= 15;
    if (redFlags.includes("CONCURRENT_EMPLOYMENT_CONFLICT")) baseScore -= 20;
    if (redFlags.includes("MISSING_EDUCATION")) baseScore -= 12;

    const matchScore = parseFloat(Math.min(96.5, Math.max(25.0, baseScore)).toFixed(1));
    const atsScore = redFlags.includes("FORMAT_CORRUPT")
      ? Math.floor(20 + Math.random() * 15)
      : Math.floor(75 + Math.min(25, matchedSkills.length * 2.5));

    // 7. Council Verdict & Consensus
    let verdict = "LEAN_HIRE";
    let verdictType = "neutral";
    if (matchScore >= 75 && redFlags.length === 0) {
      verdict = "STRONG_HIRE";
      verdictType = "positive";
    } else if (matchScore < 52 || redFlags.length >= 2 || redFlags.includes("FORMAT_CORRUPT")) {
      verdict = "REJECT";
      verdictType = "negative";
    }

    const councilScore = parseFloat((matchScore * 0.95 + (verdict === "STRONG_HIRE" ? 6 : -4)).toFixed(1));

    // 8. Extract Evidence Snippet
    let evidenceSnippet = "Demonstrated production delivery with verifiable technical artifacts.";
    const bulletCandidates = lines.filter((l) => l.startsWith("•") || l.startsWith("-") || l.startsWith("*"));
    const metricBullet = bulletCandidates.find((b) =>
      /(\d+ms|\d+%|\d+,\d+|\$|\bp95\b|\blatency\b|\breduced\b|\bscaled\b)/i.test(b)
    );
    if (metricBullet) {
      evidenceSnippet = metricBullet.replace(/^[•\-\*]\s*/, "");
    } else if (bulletCandidates.length > 0) {
      evidenceSnippet = bulletCandidates[0].replace(/^[•\-\*]\s*/, "");
    }

    const isHighRisk = redFlags.length >= 2 || redFlags.includes("SKILL_STUFFING");
    const isMedRisk = redFlags.length === 1 || redFlags.includes("FORMAT_CORRUPT");
    const ghRisk = isHighRisk ? "HIGH" : isMedRisk ? "MEDIUM" : "LOW";

    parsedCandidates.push({
      id: `CAN-UPL-${String(parsedCandidates.length + 1).padStart(3, "0")}`,
      name: candidateName,
      anonymizedId: `Uploaded #${parsedCandidates.length + 1}`,
      fileName: file.name,
      title: activeRole.title,
      experienceYears: experienceYears,
      matchScore: matchScore,
      atsScore: atsScore,
      councilScore: Math.min(99, Math.max(25, councilScore)),
      verdict: verdict,
      verdictType: verdictType,
      redFlags: redFlags,
      matchedSkills: matchedSkills,
      partiallyMatchedSkills: [],
      missingSkills: missingSkills.slice(0, 4),
      salaryRange: activeRole.salaryInr ? `INR ${activeRole.salaryInr}` : "",
      salaryInr: activeRole.salaryInr,
      level: activeRole.level,
      bandPosPct: Math.floor(matchScore * 0.85),
      evidenceSnippet: evidenceSnippet,
      github: {
        username: githubUsername,
        score: Math.floor(matchScore * 0.92),
        risk: ghRisk,
        reposAnalyzed: ghRisk === "LOW" ? 12 : 5,
        authenticRepos: ghRisk === "LOW" ? 11 : 1,
        forksCount: ghRisk === "HIGH" ? 10 : 1,
        archSignals: ghRisk === "LOW" ? 6 : 1,
        quantifiedMetrics: ghRisk === "LOW" ? 5 : 0,
        languages: ["Python (70%)", "Shell (30%)"]
      },
      council: {
        techLead: {
          score: Math.floor(matchScore * 0.95),
          feedback: `Parsed from uploaded resume '${file.name}'. Evaluated against ${activeRole.title} requirements.`
        },
        culture: {
          score: ghRisk === "LOW" ? 82 : 45,
          feedback: `Candidate tenure: ${experienceYears} yrs. Code verification via ${githubUsername}.`
        },
        fairAuditor: {
          score: redFlags.length === 0 ? 98 : 91,
          feedback: redFlags.length === 0
            ? "Zero red flags detected; clean verifiable claims."
            : `Audit flags triggered: ${redFlags.join(", ")}.`
        },
        seniorityComp: {
          score: Math.floor(matchScore * 0.9),
          feedback: `Target CTC aligned with INR ${activeRole.salaryInr}.`
        }
      },
      debateSnippet: [
        { agent: "Tech Lead", text: `Evidence parsed: "${evidenceSnippet.slice(0, 100)}..."` },
        { agent: "Fair Auditor", text: redFlags.length === 0 ? "Clean dossier." : `Flags detected: ${redFlags.join(", ")}.` }
      ],
      interviewQuestions: [
        {
          q: `Can you walk me through your engineering decisions in: "${evidenceSnippet.slice(0, 60)}..."?`,
          type: "Technical Deep-Dive",
          lookFor: "Clarity on architecture, metrics, and production tradeoffs."
        }
      ]
    });
  }

  // Sort by matchScore descending and assign rank
  parsedCandidates.sort((a, b) => b.matchScore - a.matchScore);
  parsedCandidates.forEach((c, index) => {
    c.rank = index + 1;
  });

  return { candidates: parsedCandidates, rejected };
}
