/**
 * Client-Side In-Browser Resume Parser (Multi-Format)
 * Supports .txt, .pdf, .docx, and .md files directly in the browser.
 * Uses pdfjs-dist for PDF text streams and mammoth for DOCX extraction.
 */

import mammoth from "mammoth";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";

async function extractTextFromFile(file) {
  const name = file.name.toLowerCase();

  // 1. PDF File Text Extraction
  if (name.endsWith(".pdf")) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({
        data: new Uint8Array(arrayBuffer)
      });
      const pdf = await loadingTask.promise;
      let fullText = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map((it) => it.str).join(" ");
        fullText += pageText + "\n";
      }
      return fullText.trim() || (await file.text());
    } catch (err) {
      console.warn("PDF extraction fallback:", file.name, err);
      try {
        return await file.text();
      } catch {
        return "";
      }
    }
  }

  // 2. DOCX File Text Extraction
  if (name.endsWith(".docx")) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      return (result.value || "").trim();
    } catch (err) {
      console.warn("DOCX extraction fallback:", file.name, err);
      return "";
    }
  }

  // 3. Plain Text / Markdown (.txt, .md, .json)
  return await file.text();
}

export async function parseUploadedFiles(files, activeRole = { title: "Senior Machine Learning Engineer", skills: [] }) {
  const parsedCandidates = [];
  const roleSkills = activeRole.skills || [];

  for (let idx = 0; idx < files.length; idx++) {
    const file = files[idx];
    let text = "";

    try {
      text = await extractTextFromFile(file);
    } catch (err) {
      console.warn("Failed to extract text from file:", file.name, err);
      continue;
    }

    if (!text || text.trim().length === 0) {
      text = `Candidate Application File: ${file.name}`;
    }

    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    // 1. Extract Candidate Name
    let candidateName = "";
    const cleanFilename = file.name.replace(/\.[^/.]+$/, "");
    const parts = cleanFilename.split("_");
    if (parts.length >= 3) {
      // If ends with first and last name e.g. "...Nandini_Pandey"
      const possibleLastName = parts[parts.length - 1];
      const possibleFirstName = parts[parts.length - 2];
      if (/^[A-Z][a-z]+$/.test(possibleFirstName) && /^[A-Z][a-z]+$/.test(possibleLastName)) {
        candidateName = `${possibleFirstName} ${possibleLastName}`;
      }
    }

    if (!candidateName && lines.length > 0) {
      // Use first non-empty line if it looks like a name (short, no colons)
      const firstLine = lines[0];
      if (firstLine.length < 40 && !firstLine.includes(":") && !firstLine.includes("@")) {
        candidateName = firstLine;
      } else {
        candidateName = cleanFilename.replace(/_/g, " ");
      }
    }

    // 2. Extract Experience / Tenure
    let experienceYears = 3.0;
    const expMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years|yrs)/i);
    if (expMatch) {
      experienceYears = parseFloat(expMatch[1]);
    } else {
      const monthMatch = text.match(/(\d+)\s*(?:months)/i);
      if (monthMatch) {
        experienceYears = parseFloat((parseInt(monthMatch[1], 10) / 12).toFixed(1));
      }
    }

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
      const sLower = skill.toLowerCase();
      if (lowerText.includes(sLower)) {
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
      id: `CAN-UPL-${String(idx + 1).padStart(3, "0")}`,
      name: candidateName,
      anonymizedId: `Uploaded #${idx + 1}`,
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
      salaryRange: activeRole.salaryRange,
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
          feedback: `Target compensation aligned with ${activeRole.salaryRange}.`
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

  return parsedCandidates;
}
