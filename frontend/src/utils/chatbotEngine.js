/**
 * Grounded Talent Acquisition NLP & Conversational Engine
 * Evaluates candidate queries dynamically across the active pool,
 * active role specifications, council debriefs, and recruiter context.
 */

const KNOWN_TECH_KEYWORDS = [
  "python", "pytorch", "tensorflow", "docker", "kubernetes", "aws", "gcp", "azure",
  "fastapi", "flask", "sql", "spark", "hadoop", "nlp", "transformer", "transformers",
  "hugging face", "scikit-learn", "ci/cd", "git", "redis", "microservices", "linux",
  "cuda", "rag", "llm", "tableau", "power bi", "react", "typescript", "golang",
  "django", "celery", "graphql", "grpc", "pandas", "numpy", "c++", "rest api"
];

export function generateChatbotResponse({
  query,
  candidatesPool = [],
  activeRole = { title: "Senior Machine Learning Engineer", skills: [] },
  recruiterName = "the hiring team",
  recruiterRole = "Recruiter",
  company = "our company"
}) {
  if (!query || !query.trim()) {
    return "Please enter a question regarding candidates, skill coverage, red flags, or hiring recommendations.";
  }

  const q = query.trim();
  const lower = q.toLowerCase();
  const pool = candidatesPool || [];
  const total = pool.length;

  // 1. Detect candidate mentions (fuzzy search across names, ids, and ranks)
  const mentionedCandidates = [];
  for (const cand of pool) {
    const fullNameLower = cand.name.toLowerCase();
    const parts = fullNameLower.split(" ");
    const idLower = cand.id.toLowerCase();
    const cleanId = cand.id.replace("CAN-", "").toLowerCase();
    const rankStr = `#${cand.rank}`;

    if (
      lower.includes(fullNameLower) ||
      parts.some((p) => p.length >= 3 && lower.includes(p)) ||
      lower.includes(idLower) ||
      lower.includes(`candidate ${cleanId}`) ||
      lower.includes(`candidate #${cleanId}`) ||
      (lower.includes(rankStr) && !lower.includes(`${rankStr}0`))
    ) {
      if (!mentionedCandidates.some((c) => c.id === cand.id)) {
        mentionedCandidates.push(cand);
      }
    }
  }

  // 2. Detect mentioned technologies
  const matchedTech = KNOWN_TECH_KEYWORDS.filter((tech) => {
    // regex word boundary match
    const regex = new RegExp(`\\b${tech.replace("+", "\\+")}\\b`, "i");
    return regex.test(lower);
  });

  // --------------------------------------------------------------------------
  // INTENT A: CANDIDATE COMPARISON (Explicit "compare" or 2 candidates detected)
  // --------------------------------------------------------------------------
  if (
    lower.includes("compare") ||
    lower.includes(" vs ") ||
    lower.includes(" versus ") ||
    mentionedCandidates.length >= 2
  ) {
    const candA = mentionedCandidates[0] || pool[0];
    const candB =
      mentionedCandidates[1] || (pool[1]?.id !== candA?.id ? pool[1] : pool[2]) || pool[0];

    if (!candA || !candB) {
      return "Insufficient candidates in the active pool to generate a comparison.";
    }

    const matchDiff = (candA.matchScore - candB.matchScore).toFixed(1);
    const better =
      candA.matchScore >= candB.matchScore ? candA.name : candB.name;

    return (
      `**Side-by-Side Comparison: ${candA.name} vs ${candB.name}**\n\n` +
      `• **Role Title:** ${candA.title} vs ${candB.title}\n` +
      `• **Overall Match:** ${candA.name} (${candA.matchScore}%) vs ${candB.name} (${candB.matchScore}%) [Advantage: ${better} by ${Math.abs(matchDiff)}%]\n` +
      `• **ATS Readability:** ${candA.atsScore}/100 vs ${candB.atsScore}/100\n` +
      `• **Council Consensus:** ${candA.verdict} (${candA.councilScore}%) vs ${candB.verdict} (${candB.councilScore}%)\n` +
      `• **GitHub Forensics:** ${candA.github?.risk ?? "LOW"} Risk (${candA.github?.score ?? 85}%) vs ${candB.github?.risk ?? "LOW"} Risk (${candB.github?.score ?? 85}%)\n` +
      `• **Verified Tenure:** ${candA.experienceYears} Years vs ${candB.experienceYears} Years\n` +
      `• **Target Compensation:** ${candA.salaryRange} vs ${candB.salaryRange}\n\n` +
      `**Recruiter Recommendation (${recruiterName}):**\n` +
      `${better} demonstrates higher production alignment for the **${activeRole.title}** opening with superior evidence backing.`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT B: OUTREACH / RECRUITER EMAIL DRAFTING
  // --------------------------------------------------------------------------
  if (
    (lower.includes("email") ||
      lower.includes("reach out") ||
      lower.includes("outreach") ||
      lower.includes("message") ||
      lower.includes("draft")) &&
    mentionedCandidates.length > 0
  ) {
    const cand = mentionedCandidates[0];
    const keySkills = cand.matchedSkills.slice(0, 3).join(", ") || "engineering";
    return (
      `**Personalized Outreach Draft for ${cand.name}**\n\n` +
      `**Subject:** Exciting ${activeRole.title} Opening at ${company} — Impressed by your track record\n\n` +
      `Hi ${cand.name.split(" ")[0]},\n\n` +
      `I'm ${recruiterName}, ${recruiterRole} at ${company}. I recently reviewed your profile and was particularly impressed by your verifiable achievements in ${keySkills} — notably: "${cand.evidenceSnippet}".\n\n` +
      `Our engineering team is actively expanding our ${activeRole.title} practice (${activeRole.salaryRange} / INR ${activeRole.salaryInr}). Given your ${cand.experienceYears} years of verified production experience, your background stands out as a strong fit.\n\n` +
      `Would you be open to an introductory 20-minute conversation this Thursday or Friday to discuss the roadmap and team architecture?\n\n` +
      `Best regards,\n` +
      `${recruiterName}\n` +
      `${recruiterRole}\n` +
      `${company}`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT C: SINGLE CANDIDATE DEEP DIVE / SCORECARD
  // --------------------------------------------------------------------------
  if (
    mentionedCandidates.length === 1 &&
    !lower.includes("how many") &&
    !lower.includes("all candidates")
  ) {
    const cand = mentionedCandidates[0];
    const redFlagText =
      cand.redFlags.length > 0
        ? `⚠️ Flagged: ${cand.redFlags.join(", ")}`
        : "✅ Clean Audit (0 Red Flags)";

    return (
      `**Candidate Dossier: ${cand.name} (${cand.id} • Rank #${cand.rank})**\n\n` +
      `• **Role & Level:** ${cand.title} (${cand.level})\n` +
      `• **Verified Tenure:** ${cand.experienceYears} Years\n` +
      `• **Hybrid Match Score:** ${cand.matchScore}% | ATS Parse Score: ${cand.atsScore}/100\n` +
      `• **Council Consensus:** **${cand.verdict}** (${cand.councilScore}% consensus)\n` +
      `• **Audit Status:** ${redFlagText}\n` +
      `• **Verified Competencies:** ${cand.matchedSkills.join(", ") || "None verified"}\n` +
      `• **Missing / Deficit Skills:** ${cand.missingSkills.join(", ") || "None (Full Coverage)"}\n` +
      `• **Target Compensation:** ${cand.salaryRange} (INR ${cand.salaryInr})\n` +
      `• **Production Evidence:** "${cand.evidenceSnippet}"\n` +
      `• **GitHub Authenticity:** ${cand.github?.score ?? 85}/100 (${cand.github?.risk ?? "LOW"} Risk, ${cand.github?.authenticRepos ?? 10} authentic repos, ${cand.github?.forksCount ?? 1} forks)\n\n` +
      `**Four-Agent Council Breakdown:**\n` +
      `  - Tech Lead (${cand.council?.techLead?.score ?? 85}/100): "${cand.council?.techLead?.feedback || 'Approved'}"\n` +
      `  - Culture & Collab (${cand.council?.culture?.score ?? 80}/100): "${cand.council?.culture?.feedback || 'Approved'}"\n` +
      `  - Fair-Hiring Auditor (${cand.council?.fairAuditor?.score ?? 95}/100): "${cand.council?.fairAuditor?.feedback || 'Passed'}"\n` +
      `  - Seniority & Comp (${cand.council?.seniorityComp?.score ?? 85}/100): "${cand.council?.seniorityComp?.feedback || 'Approved'}"`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT D: HEADCOUNT / POOL SIZE / STATS
  // --------------------------------------------------------------------------
  if (
    lower.includes("how many") ||
    lower.includes("count") ||
    lower.includes("number of") ||
    lower.includes("members") ||
    lower.includes("total candidates") ||
    lower.includes("pool size") ||
    lower.includes("overview") ||
    lower.includes("breakdown") ||
    lower.includes("cohort")
  ) {
    const strong = pool.filter((c) => c.verdict === "STRONG_HIRE");
    const lean = pool.filter((c) => c.verdict === "LEAN_HIRE");
    const reject = pool.filter((c) => c.verdict === "REJECT");
    const flagged = pool.filter((c) => c.redFlags.length > 0);
    const avgScore = total > 0 ? (pool.reduce((acc, c) => acc + c.matchScore, 0) / total).toFixed(1) : 0;
    const topCand = pool[0];

    return (
      `**Active Candidate Pool Telemetry (${total} Candidates Screened for ${activeRole.title})**\n\n` +
      `• **Total Evaluated Candidates:** **${total}**\n` +
      `• **Strong Hires:** **${strong.length}** (${((strong.length / total) * 100).toFixed(1)}%) — e.g. ${strong.slice(0, 3).map((c) => `${c.name} (${c.matchScore}%)`).join(", ")}\n` +
      `• **Lean Hires:** **${lean.length}** (${((lean.length / total) * 100).toFixed(1)}%)\n` +
      `• **Rejections:** **${reject.length}** (${((reject.length / total) * 100).toFixed(1)}%)\n` +
      `• **Red Flags Intercepted:** **${flagged.length}** candidates (${((flagged.length / total) * 100).toFixed(1)}% intercept rate)\n` +
      `• **Cohort Average Match:** **${avgScore}%**\n` +
      `• **Top Ranked Candidate:** **${topCand?.name || "N/A"}** with **${topCand?.matchScore || 0}%** hybrid match score.\n\n` +
      `*Recruiter Insight (${recruiterName}):* All evaluations are calibrated against ${activeRole.title} required competencies. You can ask me to shortlist strong hires or deep-dive any specific candidate.`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT E: SKILL & TECHNOLOGY MATCHING
  // --------------------------------------------------------------------------
  if (
    matchedTech.length > 0 ||
    lower.includes("required skills") ||
    lower.includes("which candidate has") ||
    lower.includes("who has the skills") ||
    lower.includes("who knows") ||
    lower.includes("who has experience") ||
    lower.includes("competenc")
  ) {
    const targetTechs =
      matchedTech.length > 0 ? matchedTech : activeRole.skills.slice(0, 4);

    // Score candidates based on match against targetTechs
    const matchingCandidates = pool
      .map((c) => {
        const matches = targetTechs.filter((t) => {
          const tLower = t.toLowerCase();
          const inMatched = (c.matchedSkills || []).some((s) => s.toLowerCase().includes(tLower));
          const inSnippet = (c.evidenceSnippet || "").toLowerCase().includes(tLower);
          const inGithub = (c.github?.languages || []).some((l) => l.toLowerCase().includes(tLower));
          return inMatched || inSnippet || inGithub;
        });
        return {
          candidate: c,
          matchCount: matches.length,
          matchedTechList: matches
        };
      })
      .filter((item) => item.matchCount > 0)
      .sort((a, b) => b.candidate.matchScore - a.candidate.matchScore);

    if (matchingCandidates.length === 0) {
      return (
        `No candidates in the active pool of ${total} demonstrated verified production proficiency in **${targetTechs.join(", ")}**.\n\n` +
        `• Active Role Competencies: ${activeRole.skills.slice(0, 8).join(", ")}\n` +
        `Try searching for core stack requirements like **Python, PyTorch, Docker, or AWS**.`
      );
    }

    const topMatches = matchingCandidates.slice(0, 4);
    const techHeader = targetTechs.join(", ");

    return (
      `**Candidates Matching Skill Query [${techHeader}] (${matchingCandidates.length} found):**\n\n` +
      topMatches
        .map(
          (m, idx) =>
            `${idx + 1}. **${m.candidate.name}** (Rank #${m.candidate.rank} • **${m.candidate.matchScore}% Match** • ${m.candidate.verdict})\n` +
            `   • **Matched Competencies:** ${m.candidate.matchedSkills.join(", ")}\n` +
            `   • **Evidence:** "${m.candidate.evidenceSnippet}"\n` +
            `   • **GitHub Score:** ${m.candidate.github?.score ?? 85}% (${m.candidate.github?.risk ?? "LOW"} Risk)`
        )
        .join("\n\n") +
      `\n\n**Top Pick:** **${topMatches[0].candidate.name}** is the strongest fit with ${topMatches[0].candidate.experienceYears} years of verified production delivery.`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT F: RED FLAGS & AUDIT FRAUD INTERCEPT
  // --------------------------------------------------------------------------
  if (
    lower.includes("flag") ||
    lower.includes("fake") ||
    lower.includes("fraud") ||
    lower.includes("unverified") ||
    lower.includes("cheat") ||
    lower.includes("stuffing") ||
    lower.includes("risk") ||
    lower.includes("reject") ||
    lower.includes("why was")
  ) {
    const flagged = pool.filter((c) => (c.redFlags || []).length > 0);

    if (flagged.length === 0) {
      return `Zero red flags currently detected across the active pool of ${total} candidates. All profiles passed Fair-Hiring verification.`;
    }

    return (
      `**Audit Intercept Summary (${flagged.length} Candidates Flagged for ${activeRole.title}):**\n\n` +
      flagged
        .slice(0, 5)
        .map(
          (c) =>
            `• **${c.name}** (Rank #${c.rank} • Match: ${c.matchScore}% • ${c.verdict})\n` +
            `  - **Triggered Flags:** \`${(c.redFlags || []).join(", ")}\`\n` +
            `  - **Fair Auditor Finding:** "${c.council?.fairAuditor?.feedback || 'Audit review complete.'}"\n` +
            `  - **GitHub Forensics:** ${c.github?.forksCount ?? 0} forks vs ${c.github?.authenticRepos ?? 0} authentic repositories (${c.github?.risk ?? "LOW"} Risk)`
        )
        .join("\n\n") +
      `\n\n*Audit Standard:* Disqualifications are strictly evidence-backed based on commit histories and verifiable timeline assertions.`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT G: TOP CANDIDATES / SHORTLIST / RECOMMENDATIONS
  // --------------------------------------------------------------------------
  if (
    lower.includes("top") ||
    lower.includes("best") ||
    lower.includes("shortlist") ||
    lower.includes("recommend") ||
    lower.includes("who should i") ||
    lower.includes("hire") ||
    lower.includes("highest") ||
    lower.includes("rank 1")
  ) {
    const top3 = pool.slice(0, 3);
    return (
      `**Top ${top3.length} Recommended Candidates for ${activeRole.title}:**\n\n` +
      top3
        .map(
          (c, idx) =>
            `${idx + 1}. **${c.name}** (Rank #${c.rank} • **${c.matchScore}% Match** • ${c.verdict})\n` +
            `   • **Tenure & Level:** ${c.experienceYears} Years (${c.level})\n` +
            `   • **ATS Readability:** ${c.atsScore}/100 | Council Consensus: ${c.councilScore}%\n` +
            `   • **Core Evidence:** "${c.evidenceSnippet}"\n` +
            `   • **Salary Target:** ${c.salaryRange}`
        )
        .join("\n\n") +
      `\n\n*Next Action:* Proceed to schedule technical deep-dive interviews with **${top3[0]?.name}** and **${top3[1]?.name}**.`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT H: SALARY & COMPENSATION PLANNING
  // --------------------------------------------------------------------------
  if (
    lower.includes("salary") ||
    lower.includes("comp") ||
    lower.includes("pay") ||
    lower.includes("band") ||
    lower.includes("lpa") ||
    lower.includes("budget") ||
    lower.includes("ctc")
  ) {
    const topCand = pool[0];
    return (
      `**Compensation Intelligence for ${activeRole.title}:**\n\n` +
      `• **Role Budget Band:** **${activeRole.salaryRange}** (INR **${activeRole.salaryInr}**)\n` +
      `• **Seniority Level:** ${activeRole.level || "L4/L5 Senior"}\n` +
      `• **Top Match Positioning:** **${topCand?.name}** target is **${topCand?.salaryRange}** (aligned at ${topCand?.bandPosPct || 70}% of band).\n` +
      `• **Junior / Fresher Band:** $70,000 - $95,000 (INR 8-15 LPA)\n` +
      `• **Principal Architect Band:** $180,000 - $210,000 (INR 40-48 LPA)\n\n` +
      `*Recruiter Advice (${recruiterName}):* Budget is optimal for top-tier candidates with verifiable open-source evidence.`
    );
  }

  // --------------------------------------------------------------------------
  // INTENT I: DYNAMIC RELEVANCE SEARCH (FALLBACK FOR ARBITRARY QUESTIONS)
  // --------------------------------------------------------------------------
  const queryTokens = lower
    .split(/\W+/)
    .filter((tok) => tok.length >= 3 && !["the", "and", "for", "with", "are", "what", "how", "who"].includes(tok));

  const scoredCandidates = pool
    .map((cand) => {
      let score = 0;
      const haystack = [
        cand.name,
        cand.title,
        cand.evidenceSnippet,
        cand.level,
        cand.salaryRange,
        ...(cand.matchedSkills || []),
        ...(cand.missingSkills || []),
        ...(cand.redFlags || []),
        cand.council?.techLead?.feedback || "",
        cand.council?.culture?.feedback || "",
        cand.council?.fairAuditor?.feedback || ""
      ]
        .join(" ")
        .toLowerCase();

      for (const tok of queryTokens) {
        if (haystack.includes(tok)) score += 1;
      }
      return { candidate: cand, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || b.candidate.matchScore - a.candidate.matchScore);

  if (scoredCandidates.length > 0) {
    const best = scoredCandidates.slice(0, 3);
    return (
      `**Grounded Search Results for "${q}" across ${total} candidates:**\n\n` +
      best
        .map(
          (b, i) =>
            `${i + 1}. **${b.candidate.name}** (Rank #${b.candidate.rank} • **${b.candidate.matchScore}% Match** • ${b.candidate.verdict})\n` +
            `   • **Relevant Evidence:** "${b.candidate.evidenceSnippet}"\n` +
            `   • **Key Skills:** ${b.candidate.matchedSkills.join(", ")}`
        )
        .join("\n\n") +
      `\n\nAsk for a deeper breakdown of **${best[0].candidate.name}** or their council debate score.`
    );
  }

  // --------------------------------------------------------------------------
  // FINAL CLEAN ADVICE
  // --------------------------------------------------------------------------
  const topC = pool[0];
  return (
    `**Talent Copilot Intelligence for ${activeRole.title}**\n\n` +
    `I screened all **${total} candidates** in the active pool against your query: *"${q}"*.\n\n` +
    `• **Active Role:** ${activeRole.title} (${activeRole.salaryRange})\n` +
    `• **Required Skills:** ${activeRole.skills.slice(0, 6).join(", ")}...\n` +
    `• **Current #1 Candidate:** **${topC?.name}** (${topC?.matchScore}% match, ${topC?.verdict})\n\n` +
    `**Suggested questions to ask me:**\n` +
    `1. *"How many members are there in total?"*\n` +
    `2. *"Which candidate has the required skills?"*\n` +
    `3. *"Who has red flags and why?"*\n` +
    `4. *"Compare ${pool[0]?.name || "Karthik"} and ${pool[1]?.name || "Rahul"}"*\n` +
    `5. *"Draft an outreach email for ${topC?.name || "Karthik"}"*`
  );
}
