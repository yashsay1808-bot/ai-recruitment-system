/**
 * General recruitment know-how for the chatbot: short, practical answers to questions that are about hiring in
 * general (not about a particular candidate). Anything outside recruitment is politely declined.
 */

// [trigger, answer]. The first entry whose trigger matches the question wins.
const KNOWLEDGE = [
  [/\bctc\b|cost to company/, "**CTC (Cost to Company)** is the total yearly amount a company spends on one employee: fixed salary plus variable pay, bonuses, provident fund, insurance and other benefits. It is quoted in INR per annum, usually as LPA (lakhs per annum; 1 lakh = 100,000). In-hand salary is lower than CTC because of tax, PF and deductions."],
  [/\blpa\b|lakhs? per annum/, "**LPA** means lakhs per annum: 12 LPA is INR 12,00,000 a year, or about INR 1,00,000 a month of CTC. It is the usual way to quote CTC in India."],
  [/notice period|serving notice|buy.?out/, "**Notice period** is the time an employee must work after resigning, usually 30 to 90 days in India. Many employers shorten it by a **buy-out** (the new employer or the candidate pays the unserved days). Ask about it early because it decides the joining date."],
  [/negotiat|counter.?offer|salary expectation|hike/, "**Negotiating an offer:** know the role's CTC band first, ask for the candidate's expectation and current CTC, anchor inside the band, and explain the whole package (fixed, variable, joining bonus, benefits). For a **counter-offer** from the current employer, check why the candidate wanted to leave; money alone rarely fixes that."],
  [/offer letter|offer acceptance|joining bonus|offer drop/, "**Offer stage:** send a written offer with CTC breakup, joining date, probation and notice terms; keep in touch until the joining date because offer drop-outs are common. A healthy **offer acceptance rate** is above about 80 percent."],
  [/\bats\b|applicant tracking/, "An **ATS (Applicant Tracking System)** collects resumes, parses them into fields, ranks them against a job description and tracks candidates through the hiring stages. Basic ATS tools only count keywords; ours adds evidence checks, skill relationships and an explanation for every verdict."],
  [/(write|writing|draft|create|good|tips for).*(job description|\bjd\b)|(job description|\bjd\b).*(tips|template|format|how to write)/, "**A good job description** has: a clear title and level; a two-line summary of the work; 5 to 8 must-have skills and a few nice-to-haves; the minimum experience (use the title honestly: Senior usually means 5+ years); the CTC band in LPA; location and work mode; and the hiring steps. Avoid long wish-lists, because they discourage good candidates and invite keyword stuffing."],
  [/source|sourcing|where to find|find candidates|talent pool/, "**Sourcing channels:** employee referrals (best quality), job boards, LinkedIn search, campus drives, GitHub or portfolio search for technical roles, and your own database of past applicants. Track which channel gives the most interviews and hires, and put effort there."],
  [/screening call|phone screen|first round|hr round/, "**A screening call (10 to 15 minutes)** checks: motivation to change, current role and CTC, expected CTC, notice period, location or work-mode fit, and a quick check of the two or three must-have skills. It saves the technical team's time."],
  [/behaviou?ral|\bstar\b method|situational question/, "**Behavioural questions** ask for real past examples. Use the **STAR** method: Situation, Task, Action, Result. Good answers are specific, say what the candidate personally did and give a measurable result. Example: \"Tell me about a time you fixed a production issue under pressure.\""],
  [/technical interview|coding (round|test)|take.?home|system design round|assessment/, "**Technical assessment options:** a live coding round (problem solving), a short take-home task (real-world skills), a system-design discussion for experienced people, and a project deep-dive on the resume. Use the same rubric for every candidate so that results can be compared fairly."],
  [/fresher|campus|entry.?level|graduate/, "**Hiring freshers:** judge potential, not years. Look at fundamentals (data structures, one language), projects and internships, learning speed, communication and CGPA as a minor signal. A short practical task works better than trivia questions."],
  [/experienced|lateral|senior (hire|level)|what does senior mean/, "**Experienced hires:** test depth and ownership: what they designed, decided and measured. A \"Senior\" title normally means 5 or more years of experience; below that, look for a mid-level title. Ask for results with numbers and verify the main project in the interview."],
  [/red flags? (in|on) (a )?resume|resume red flag|what to look for in (a )?resume|inflated|job.?hopp|employment gap/, "**Resume red flags:** skills listed with no project or job that uses them, a very long skill list for little experience, dates that overlap or run backwards, no measurable results, unexplained long gaps and very frequent job changes. Treat each as a question to ask, not as proof of a problem."],
  [/reference check|background (check|verification)|bgv/, "**Reference and background checks:** do them after the offer is accepted and before joining: employment dates and last CTC from the previous employer, education verification, and one or two references. Always get the candidate's written consent."],
  [/referral/, "**Employee referrals** give faster hiring and better retention. Set a clear referral bonus, share open roles regularly, and give feedback to the referrer even when the candidate is rejected."],
  [/time to hire|cost per hire|metrics|kpi|hiring funnel|funnel/, "**Key hiring metrics:** time to hire (days from opening to offer acceptance), cost per hire, offer acceptance rate, source of hire, quality of hire (performance after 6 to 12 months) and the pass rate of each funnel stage (applied, screened, interviewed, offered, joined)."],
  [/bias|diversity|inclusion|blind (hiring|screening)|fair hiring|discriminat/, "**Fair hiring:** use the same job-relevant criteria for everyone, structured questions and a scoring rubric, and hide names and personal details while screening (blind screening). Keep humans in the final decision. Regulations such as the EU AI Act treat recruitment AI as high-risk and require transparency and human oversight."],
  [/probation|onboarding|first 90 days/, "**Probation and onboarding:** probation is usually 3 to 6 months. Give a clear 30-60-90 day plan, a buddy, access to tools on day one and a review at the end of each month."],
  [/retention|attrition|why (do )?(employees|people) leave|reduce turnover/, "**Retention:** people leave mainly for growth, manager quality, pay and workload. Keep CTC competitive, give clear career paths, hold regular one-to-ones and act on exit-interview feedback."],
  [/interview (panel|rubric|scorecard|feedback)|structured interview|scoring rubric/, "**Structured interviews:** decide the competencies first, ask every candidate the same core questions, score each answer 1 to 5 against written descriptions, and collect each interviewer's score before the group discussion so nobody anchors on the first opinion."],
  [/contract(ual)?|full.?time|part.?time|freelanc|permanent|third.?party payroll/, "**Employment types:** full-time (permanent, with benefits and notice period), contract (fixed duration, usually higher pay and no long-term benefits), third-party payroll (employed by an agency, working for the client) and freelance (project-based). State the type clearly in the offer."],
  [/remote|hybrid|work from home|\bwfh\b|work mode/, "**Work mode:** state whether the job is on-site, hybrid or remote in the job description, because it changes who applies and what CTC is expected. Check time-zone overlap and the tools needed for remote work."],
  [/levels?|l[3-6]\b|leveling|grade|band structure/, "**Levels in this system:** L3 Associate or junior (under 2 years), L4 Engineer (2 to 5 years), L5 Senior (5 to 9 years), L6 Principal or Staff (9+ years). Each level has a CTC band in LPA, and a candidate's position inside the band depends on evidence and scope."],
  [/resume (length|format|pages|tips)|good resume|how (long|many pages)/, "**Resume tips:** one to two pages, a short summary, skills grouped by area, projects and jobs with measurable results (for example \"cut latency by 40%\"), consistent dates, and links to GitHub or a portfolio. Our uploader accepts resumes of up to 2 pages."],
  [/explainable ai|xai|why (use|is) ai (in|for) hiring|ai (in|for) (hiring|recruit)/, "**Explainable AI in hiring** means every score has a reason a recruiter can read: which skills matched, what was missing, which red flags fired and how the four review agents voted. It builds trust, helps correct mistakes and supports legal requirements for transparency."],
];

const HOW_TO = /\b(what (is|are|does|do)|what's|whats|explain|meaning|define|how (do|does|to|can|should|long|many|is|are)|tips?|best (way|practice)|difference|why (do|is|are|should)|advice|guide|checklist|steps?)\b/;

/** An answer for a general recruitment question, or null when none of the topics fits. */
export function generalRecruitmentReply(lower) {
  if (!HOW_TO.test(lower)) return null;
  const hit = KNOWLEDGE.find(([re]) => re.test(lower));
  return hit ? hit[1] : null;
}

const OFF_TOPIC = /\b(weather|cricket|football|ipl|movie|film|song|lyrics|joke|riddle|recipe|politics|election|stock price|bitcoin|crypto|horoscope|capital of|prime minister|poem|homework|girlfriend|boyfriend)\b/;

/** True when the question is clearly not about recruitment. */
export const isOffTopic = (lower) => OFF_TOPIC.test(lower);

export const OFF_TOPIC_REPLY =
  "I can only help with recruitment: the candidates in this pool, the role and its CTC band, interview questions, outreach emails, and general hiring topics such as CTC, notice period, writing a job description or structured interviews. Try one of the suggestions below.";
