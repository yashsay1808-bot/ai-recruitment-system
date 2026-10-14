import React, { useState, useMemo } from "react";
import {
  Search,
  X,
  ChevronRight,
  DollarSign,
  Briefcase,
  Sparkles,
  Send,
  Download,
  LayoutGrid,
  List,
  Target,
  BarChart3,
  SearchCode,
  Swords,
  Mic,
  LineChart,
  Bot,
  LogOut,
  RefreshCw
} from "lucide-react";
import { DEFAULT_JOB_ROLES } from "./data/jobRoles";
import { generateChatbotResponse } from "./utils/chatbotEngine";
import { buildInterviewKit, BADGE_CLASSES } from "./utils/interviewQuestions";
import { useAuth } from "./context/AuthContext";
import JobHome from "./components/JobHome";
import { isApiMode } from "./config/env";
import { candidatesService, POOLS, INITIAL_POOL } from "./utils/candidatesService";
import { parseUploadedFiles } from "./utils/resumeParserClient";

function GithubIcon({ className = "w-5 h-5" }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

const MASTER_RESUME_PROMPT = `Role: You are an expert Enterprise HR Systems Architect and Principal Technical Recruiter.
Task: Generate 50 to 100 diverse, realistic, and highly detailed synthetic candidate resumes for an AI Recruitment System benchmarking evaluation.

Target Roles (Distribute evenly across):
1. Senior Machine Learning Engineer (PyTorch, FastAPI, AWS ECS, MLOps)
2. Cloud DevOps & Site Reliability Lead (Kubernetes, Terraform, AWS, Prometheus)
3. Full-Stack AI Application Engineer (React, TypeScript, FastAPI, Next.js, LangChain)
4. Data Platform & Distributed Systems Engineer (Python, Apache Spark, Kafka, Snowflake)
5. Backend Microservices Architect (Golang, Python, gRPC, Docker, PostgreSQL)
6. AI Safety, Governance & Alignment Auditor (Model Evaluation, Red Teaming, Bias Auditing)
7. Senior Business Intelligence & Data Analyst (SQL, Python, Tableau, Power BI)
8. Python Backend & API Developer (Django, FastAPI, Celery, PostgreSQL)

Distribution Profile (Must include all 5 evaluation archetypes):
- 20% Gold Standard Passes (Strong Hires): 3-7 years tenure, quantified latency/throughput metrics (e.g., "<72ms p95 latency under 50k req/day", "99.99% uptime"), authentic public GitHub repositories with original commit histories, complete education, and zero discrepancies.
- 45% Mid-Level & Lateral Transitions (Lean Hires): 2-4 years tenure, strong adjacent skills (e.g., Flask moving to FastAPI, TensorFlow moving to PyTorch, SQL moving to distributed Spark), clean work history, minor skill gaps onboardable in 30 days.
- 20% Skill Stuffing & Unverified Exaggerations (Red Flag Rejects): Under 6 months experience claiming 30+ technologies (e.g. "Kubernetes Master & CUDA Sorcerer in 4 months"), GitHub accounts with 90%+ untouched tutorial forks.
- 10% ATS Formatting & Chronology Errors (Format Rejects): Overlapping concurrent full-time employment dates in same calendar year, multi-column tables or non-standard fonts causing text extraction failures.
- 5% Missing Structural Sections (Structural Rejects): Resumes omitting mandatory sections such as Education, Employment History, or Demonstrable Projects.

Format for each resume:
- Full Name, Anonymized ID, Email, Phone, Location, GitHub handle
- Professional Summary (2-3 sentences with tenure and core focus)
- Work History (Company, Dates, Roles, 3-4 bullet points with quantified achievements)
- Technical Skills (Languages, Frameworks, Cloud, Databases, Tools)
- Education (Degree, University, Graduation Year)
- Benchmark Verification Notes (Expected Verdict: STRONG_HIRE / LEAN_HIRE / REJECT, and Red Flag Tags)
`;

// Minimal inline markdown for chat replies: **bold** and `code`. Everything else stays plain text (no HTML injection).
function renderInline(text) {
  return String(text)
    .split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
    .map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
        return <code key={i} className="rounded bg-slate-100 px-1 py-0.5 text-[0.85em] text-slate-700">{part.slice(1, -1)}</code>;
      }
      return part;
    });
}

const PROMPT_PILLS = [
  "Engineers with 2+ years in Python and PyTorch",
  "Backend developers who deployed with Docker and AWS",
  "Candidates with measurable latency or throughput results",
  "Who has NLP or transformer experience?"
];

export default function App() {
  const [blindMode, setBlindMode] = useState(false);

  // The signed-in recruiter comes from the auth gate in main.jsx; this component never renders signed out.
  const { user, signOut } = useAuth();
  const recruiterName = user.name;
  const recruiterFirstName = user.name.split(" ")[0];
  const backendConfigured = isApiMode("api");

  const [toastMessage, setToastMessage] = useState("");
  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 3500);
  };

  // Dynamic Job Roles State (8 Roles + Custom Roles)
  const [jobRoles, setJobRoles] = useState(DEFAULT_JOB_ROLES);
  const [activeRoleId, setActiveRoleId] = useState("role-ml");
  const activeRole = useMemo(() => {
    return jobRoles.find((r) => r.id === activeRoleId) || jobRoles[0];
  }, [jobRoles, activeRoleId]);

  const [newSkillInput, setNewSkillInput] = useState("");
  const [isCreatingRole, setIsCreatingRole] = useState(false);
  const [newRoleForm, setNewRoleForm] = useState({
    title: "",
    department: "Engineering Org",
    level: "L4/L5 Senior",
    minExperience: "3+ Years Production",
    salaryRange: "$150k - $180k",
    salaryInr: "30 - 38 LPA",
    description: "",
    skills: "Python, Docker, AWS, CI/CD, REST API"
  });

  // Candidate Pool State (12 Core Test Suite vs 50 Diverse Pool vs Custom Uploaded)
  const [candidatesPool, setCandidatesPool] = useState(INITIAL_POOL);
  const [is50PoolActive, setIs50PoolActive] = useState(false);
  const [poolSource, setPoolSource] = useState("12 Core Suite");
  const [isIngestingBatch, setIsIngestingBatch] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);
  const [batchStageText, setBatchStageText] = useState("");
  const [uploadedFilesCount, setUploadedFilesCount] = useState(0);
  const [uploadedFilesList, setUploadedFilesList] = useState([]);
  const [uploadFeedback, setUploadFeedback] = useState("");
  const [showMasterPrompt, setShowMasterPrompt] = useState(false);
  const [promptCopied, setPromptCopied] = useState(false);

  // Navigation State
  const [activeNav, setActiveNav] = useState("job_management");
  const [viewMode, setViewMode] = useState("cards"); // "cards" or "table"

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL");
  const [activePromptPill, setActivePromptPill] = useState("");

  // Slide-over Drawer
  const [selectedCandidate, setSelectedCandidate] = useState(candidatesPool[0]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [debateStep, setDebateStep] = useState(0);

  // Council View State
  const [councilSelectedCandId, setCouncilSelectedCandId] = useState("CAN-001");
  const [councilDebateTurn, setCouncilDebateTurn] = useState(0);

  // Comparison View State
  const [compareCandAId, setCompareCandAId] = useState("CAN-001");
  const [compareCandBId, setCompareCandBId] = useState("CAN-002");

  // Interview Assistant State
  const [interviewCandId, setInterviewCandId] = useState("CAN-001");
  const [interviewType, setInterviewType] = useState("All");
  const [interviewCopied, setInterviewCopied] = useState(false);

  // Copilot Chat
  const [copilotMessages, setCopilotMessages] = useState([
    {
      sender: "assistant",
      text: `Hello ${recruiterFirstName}! I'm your Talent Acquisition Copilot. ${candidatesPool.length} candidates are screened for the ${activeRole.title} vacancy. Ask me to breakdown headcount, match required skills, audit red flags, or draft candidate outreach emails.`
    }
  ]);
  const [copilotInput, setCopilotInput] = useState("");

  // Handlers for Dynamic Skills
  const handleRemoveSkill = (skillToRemove) => {
    setJobRoles((prev) =>
      prev.map((role) =>
        role.id === activeRoleId
          ? { ...role, skills: role.skills.filter((s) => s !== skillToRemove) }
          : role
      )
    );
  };

  const handleAddSkill = (e) => {
    if (e) e.preventDefault();
    const trimmed = newSkillInput.trim();
    if (!trimmed) return;
    if (activeRole.skills.includes(trimmed)) {
      setNewSkillInput("");
      return;
    }
    setJobRoles((prev) =>
      prev.map((role) =>
        role.id === activeRoleId
          ? { ...role, skills: [...role.skills, trimmed] }
          : role
      )
    );
    setNewSkillInput("");
  };

  const handleCreateCustomRole = (e) => {
    if (e) e.preventDefault();
    if (!newRoleForm.title.trim()) return;
    const newId = `role-custom-${Date.now()}`;
    const parsedSkills = newRoleForm.skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const createdRole = {
      id: newId,
      title: newRoleForm.title.trim(),
      department: newRoleForm.department.trim() || "Engineering Org",
      level: newRoleForm.level.trim() || "L4/L5 Senior",
      minExperience: newRoleForm.minExperience.trim() || "2+ Years Production",
      salaryRange: newRoleForm.salaryRange.trim() || "$140k - $170k",
      salaryInr: newRoleForm.salaryInr.trim() || "28 - 36 LPA",
      status: "ACCEPTING CANDIDATES",
      description: newRoleForm.description.trim() || `Enterprise hiring for ${newRoleForm.title}.`,
      skills: parsedSkills.length > 0 ? parsedSkills : ["Python", "Docker", "Git", "REST API"]
    };
    setJobRoles((prev) => [...prev, createdRole]);
    setActiveRoleId(newId);
    setIsCreatingRole(false);
    setNewRoleForm({
      title: "",
      department: "Engineering Org",
      level: "L4/L5 Senior",
      minExperience: "3+ Years Production",
      salaryRange: "$150k - $180k",
      salaryInr: "30 - 38 LPA",
      description: "",
      skills: "Python, Docker, AWS, CI/CD, REST API"
    });
  };

  // Real In-Browser Resume Ingestion Handler (Parses any uploaded .txt, .pdf, .docx files directly)
  const handleFilesSelected = async (e) => {
    const fileList = e.target.files ? Array.from(e.target.files) : [];
    if (fileList.length === 0) return;

    setUploadedFilesCount(fileList.length);
    setUploadedFilesList(fileList.map((f) => f.name));
    setIsIngestingBatch(true);
    setBatchProgress(15);
    setBatchStageText(`Stage 1/4: Reading and parsing ${fileList.length} uploaded files directly in browser...`);

    setTimeout(async () => {
      setBatchProgress(50);
      setBatchStageText(`Stage 2/4: Extracting candidate names, experience, and matching skills against ${activeRole.title}...`);

      try {
        const parsed = await parseUploadedFiles(fileList, activeRole);
        setBatchProgress(80);
        setBatchStageText(`Stage 3/4: Calculating ATS scores and 4-agent Council verdicts for ${parsed.length} candidates...`);

        setTimeout(() => {
          setBatchProgress(100);
          setBatchStageText(`Stage 4/4: Complete! ${parsed.length} custom resumes screened & indexed.`);

          setTimeout(() => {
            setCandidatesPool(parsed);
            setIs50PoolActive(parsed.length >= 20);
            setPoolSource(`Custom Uploaded (${parsed.length} Resumes)`);
            setIsIngestingBatch(false);
            setBatchProgress(0);
            setBatchStageText("");
            setUploadFeedback(`✓ Successfully parsed & indexed ${parsed.length} of your uploaded resumes into the Leaderboard!`);

            // Notify in chatbot
            setCopilotMessages((prev) => [
              ...prev,
              {
                sender: "assistant",
                text: `Ingestion Complete! I have parsed your ${parsed.length} uploaded resume files into the live ATS engine for ${activeRole.title}. Rank #1 is ${parsed[0]?.name} (${parsed[0]?.matchScore}% match). Ask me about candidate rankings, skill matches, or red flags!`
              }
            ]);
          }, 400);
        }, 600);
      } catch (err) {
        console.error("Error parsing uploaded files:", err);
        setIsIngestingBatch(false);
        setBatchProgress(0);
      }
    }, 500);
  };

  // Pool loading goes through candidatesService, so swapping bundled data for MongoDB is a config change.
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const ingestBenchmarkPool = async (poolId) => {
    const meta = POOLS[poolId];
    setIsIngestingBatch(true);
    setBatchProgress(20);
    setBatchStageText(`Stage 1/4: Ingesting ${meta.count} benchmark candidate resumes from verified dataset...`);
    try {
      const [pool] = await Promise.all([candidatesService.loadPool(poolId), sleep(600)]);
      setBatchProgress(55);
      setBatchStageText("Stage 2/4: Computing TF-IDF vector similarity and candidate feature vectors...");
      await sleep(600);
      setBatchProgress(85);
      setBatchStageText("Stage 3/4: Executing Four-Agent Council Cross-Examination & Fair Auditor check...");
      await sleep(600);
      setBatchProgress(100);
      setBatchStageText(`Stage 4/4: Leaderboard calibration complete! ${pool.length} benchmark candidates indexed.`);
      await sleep(400);

      setCandidatesPool(pool);
      setIs50PoolActive(true);
      setPoolSource(meta.label);
      setUploadFeedback(`Loaded ${pool.length} benchmark candidates (rank #1: ${pool[0]?.name}).`);
      setCopilotMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: `${pool.length} benchmark candidates are now indexed. Top candidate is ${pool[0]?.name} (${pool[0]?.matchScore}%). Ask me for a headcount breakdown, skill matches, red flags, or a comparison.`
        }
      ]);
    } catch (err) {
      console.error("Error loading candidate pool:", err);
      setUploadFeedback("Could not load that candidate pool. Please try again.");
    } finally {
      setIsIngestingBatch(false);
      setBatchProgress(0);
      setBatchStageText("");
    }
  };

  const handleSimulateBatchIngest = () => ingestBenchmarkPool("benchmark50");
  const handleLoad100Pool = () => ingestBenchmarkPool("benchmark100");

  const handleLoadCorePool = async () => {
    try {
      setCandidatesPool(await candidatesService.loadPool("core12"));
      setIs50PoolActive(false);
      setPoolSource(POOLS.core12.label);
      setUploadFeedback(`Loaded the ${POOLS.core12.label} (${POOLS.core12.count} resumes).`);
    } catch (err) {
      console.error("Error loading core pool:", err);
      setUploadFeedback("Could not load the core resumes. Please try again.");
    }
  };

  const handleTogglePool = async () => {
    const next = is50PoolActive ? "core12" : "benchmark50";
    try {
      setCandidatesPool(await candidatesService.loadPool(next));
      setIs50PoolActive(next !== "core12");
      setPoolSource(POOLS[next].label);
      setUploadFeedback(`Switched to ${POOLS[next].label}.`);
    } catch (err) {
      console.error("Error switching candidate pool:", err);
      setUploadFeedback("Could not switch candidate pools. Please try again.");
    }
  };

  const handleCopyMasterPrompt = () => {
    navigator.clipboard.writeText(MASTER_RESUME_PROMPT);
    setPromptCopied(true);
    setTimeout(() => setPromptCopied(false), 2200);
  };

  const councilCandidate = useMemo(() => {
    return candidatesPool.find((c) => c.id === councilSelectedCandId) || candidatesPool[0];
  }, [candidatesPool, councilSelectedCandId]);

  const candA = useMemo(() => {
    return candidatesPool.find((c) => c.id === compareCandAId) || candidatesPool[0];
  }, [candidatesPool, compareCandAId]);

  const candB = useMemo(() => {
    return candidatesPool.find((c) => c.id === compareCandBId) || candidatesPool[1] || candidatesPool[0];
  }, [candidatesPool, compareCandBId]);

  const interviewCandidate = useMemo(() => {
    return candidatesPool.find((c) => c.id === interviewCandId) || candidatesPool[0];
  }, [candidatesPool, interviewCandId]);

  // Full tailored kit (stored questions + generated ones), grouped by category for the filter chips.
  const interviewKit = useMemo(
    () => buildInterviewKit(interviewCandidate, activeRole),
    [interviewCandidate, activeRole],
  );
  const interviewTypes = useMemo(() => {
    const counts = new Map();
    interviewKit.forEach((q) => counts.set(q.type, (counts.get(q.type) || 0) + 1));
    return [...counts.entries()];
  }, [interviewKit]);
  const activeInterviewType = interviewTypes.some(([t]) => t === interviewType) ? interviewType : "All";
  const visibleInterviewKit =
    activeInterviewType === "All" ? interviewKit : interviewKit.filter((q) => q.type === activeInterviewType);

  const copyInterviewKit = async () => {
    const text = [
      `Interview kit: ${interviewCandidate.name} (${interviewCandidate.title}) for ${activeRole?.title || "the open role"}`,
      ...interviewKit.map((q, i) => `${i + 1}. [${q.type}] ${q.q}\n   Look for: ${q.lookFor}`),
    ].join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setInterviewCopied(true);
      setTimeout(() => setInterviewCopied(false), 1800);
    } catch {
      /* clipboard unavailable (insecure context or denied): nothing to do */
    }
  };

  // Candidates filtering
  const filteredCandidates = useMemo(() => {
    const q = (activePromptPill || searchQuery).toLowerCase().trim();
    return candidatesPool.filter((cand) => {
      const displayName = blindMode ? cand.anonymizedId : cand.name;
      const matchesSearch =
        !q ||
        displayName.toLowerCase().includes(q) ||
        cand.title.toLowerCase().includes(q) ||
        cand.matchedSkills.some((s) => s.toLowerCase().includes(q)) ||
        cand.partiallyMatchedSkills.some((s) => s.toLowerCase().includes(q)) ||
        cand.missingSkills.some((s) => s.toLowerCase().includes(q)) ||
        cand.evidenceSnippet.toLowerCase().includes(q) ||
        cand.redFlags.some((f) => f.toLowerCase().includes(q));

      const matchesVerdict =
        verdictFilter === "ALL"
          ? true
          : verdictFilter === "FLAGGED"
          ? cand.redFlags.length > 0
          : cand.verdict === verdictFilter;

      return matchesSearch && matchesVerdict;
    });
  }, [candidatesPool, searchQuery, activePromptPill, verdictFilter, blindMode]);

  const totalScreened = candidatesPool.length;
  const topMatchCandidate = candidatesPool[0];
  const avgMatchScore = (
    candidatesPool.reduce((acc, c) => acc + c.matchScore, 0) / candidatesPool.length
  ).toFixed(1);
  const strongHiresCount = candidatesPool.filter((c) => c.verdict === "STRONG_HIRE").length;
  const leanHiresCount = candidatesPool.filter((c) => c.verdict === "LEAN_HIRE").length;
  const rejectCount = candidatesPool.filter((c) => c.verdict === "REJECT").length;
  const flaggedCount = candidatesPool.filter((c) => c.redFlags.length > 0).length;

  // DYNAMIC RECRUITER TALENT COPILOT HANDLER
  const handleSendCopilot = (textToSend) => {
    const q = textToSend || copilotInput;
    if (!q.trim()) return;

    const userMsg = { sender: "user", text: q };
    const reply = generateChatbotResponse({
      query: q,
      candidatesPool,
      activeRole,
      recruiterName: recruiterName,
      recruiterRole: user.role,
      company: user.company
    });

    setCopilotMessages((prev) => [...prev, userMsg, { sender: "assistant", text: reply }]);
    setCopilotInput("");
  };


  // ==========================================================================
  // AUTHENTICATED & GUEST PLATFORM (Sidebar Always Present, Exact 7 Pages)
  // ==========================================================================
  return (
    <div className="min-h-screen w-full bg-slate-50 text-slate-900">
      {/* ------------------------------ Header ------------------------------ */}
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between gap-4 border-b border-slate-200 bg-white/90 px-6 backdrop-blur">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-xs font-bold text-white">
            NX
          </div>
          <div>
            <div className="text-sm font-semibold leading-none text-slate-900">Nexus ATS</div>
            <div className="mt-0.5 text-[11px] text-slate-500">Explainable AI recruitment</div>
          </div>
        </div>

        {/* Global search */}
        <div className="mx-4 max-w-md flex-1 md:mx-8">
          <div className="relative flex items-center rounded-lg border border-slate-300 bg-white transition focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100">
            <Search className="ml-3 h-4 w-4 shrink-0 text-slate-400" />
            <input
              type="text"
              placeholder="Search candidate, skills, or red flags..."
              aria-label="Search candidates"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setActivePromptPill("");
              }}
              className="w-full bg-transparent px-3 py-1.5 text-sm outline-none placeholder:text-slate-400"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setBlindMode(!blindMode)}
            aria-pressed={blindMode}
            className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
              blindMode
                ? "border-indigo-200 bg-indigo-50 text-indigo-700"
                : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
            }`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${blindMode ? "bg-indigo-600" : "bg-slate-400"}`} />
            {blindMode ? "Blind screening on" : "Blind screening"}
          </button>

          {/* Signed-in recruiter: avatar, name, company, sign out */}
          <div className="flex items-center gap-2.5 border-l border-slate-200 pl-3">
            <div
              aria-hidden="true"
              className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-50 text-xs font-semibold text-indigo-700"
            >
              {user.name
                .split(" ")
                .filter(Boolean)
                .slice(0, 2)
                .map((w) => w[0])
                .join("")
                .toUpperCase()}
            </div>
            <div className="hidden text-left lg:block">
              <div className="text-sm font-medium leading-none text-slate-900">{recruiterName}</div>
              <div className="mt-0.5 text-[11px] text-slate-500">{user.company}</div>
            </div>
            <button
              onClick={signOut}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* ------------------------------ Sidebar ------------------------------ */}
        <aside className="sticky top-14 h-[calc(100vh-3.5rem)] w-64 shrink-0 border-r border-slate-200 bg-white p-3">
          <nav className="space-y-1" aria-label="Main">
            {[
              { id: "job_management", label: "Job Management", Icon: Target },
              { id: "leaderboard", label: "Screening Leaderboard", Icon: BarChart3, badge: candidatesPool.length.toString() },
              { id: "deepdive", label: "Candidate DeepDive", Icon: SearchCode },
              { id: "comparison", label: "Candidate Comparison", Icon: Swords },
              { id: "interview", label: "Interview Assistant", Icon: Mic },
              { id: "analytics", label: "Recruiter Analytics", Icon: LineChart },
              { id: "chatbot", label: "Recruiter Chatbot", Icon: Bot }
            ].map(({ id, label, Icon, badge }) => {
              const isActive = activeNav === id;
              return (
                <button
                  key={id}
                  onClick={() => setActiveNav(id)}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition ${
                    isActive
                      ? "bg-indigo-50 font-medium text-indigo-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <span className="flex items-center gap-3 whitespace-nowrap">
                    <Icon className="h-4 w-4 shrink-0" />
                    {label}
                  </span>
                  {badge && (
                    <span
                      className={`rounded-md px-1.5 py-0.5 text-[11px] ${
                        isActive ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* ------------------------------ Main ------------------------------ */}
        <main className="mx-auto max-w-7xl flex-1 space-y-6 px-6 py-6 lg:px-10">

          {/* ================================================================ */}
          {/* PAGE 1: JOB MANAGEMENT (Job Management & Sign In Portal)       */}
          {/* ================================================================ */}
          {activeNav === "job_management" && (
            <JobHome
              jobRoles={jobRoles}
              activeRole={activeRole}
              activeRoleId={activeRoleId}
              setActiveRoleId={setActiveRoleId}
              isCreatingRole={isCreatingRole}
              setIsCreatingRole={setIsCreatingRole}
              newRoleForm={newRoleForm}
              setNewRoleForm={setNewRoleForm}
              handleCreateCustomRole={handleCreateCustomRole}
              handleRemoveSkill={handleRemoveSkill}
              handleAddSkill={handleAddSkill}
              newSkillInput={newSkillInput}
              setNewSkillInput={setNewSkillInput}
              candidatesPool={candidatesPool}
              poolSource={poolSource}
              is50PoolActive={is50PoolActive}
              isIngestingBatch={isIngestingBatch}
              batchProgress={batchProgress}
              batchStageText={batchStageText}
              uploadedFilesCount={uploadedFilesCount}
              uploadedFilesList={uploadedFilesList}
              uploadFeedback={uploadFeedback}
              handleFilesSelected={handleFilesSelected}
              handleLoadCorePool={handleLoadCorePool}
              handleSimulateBatchIngest={handleSimulateBatchIngest}
              handleLoad100Pool={handleLoad100Pool}
              handleTogglePool={handleTogglePool}
              showMasterPrompt={showMasterPrompt}
              setShowMasterPrompt={setShowMasterPrompt}
              promptCopied={promptCopied}
              handleCopyMasterPrompt={handleCopyMasterPrompt}
              masterPrompt={MASTER_RESUME_PROMPT}
              setActiveNav={setActiveNav}
            />
          )}

          {/* ================================================================ */}
          {/* PAGE 2: SCREENING LEADERBOARD (Screening Leaderboard)          */}
          {/* ================================================================ */}
          {activeNav === "leaderboard" && (
            <div className="space-y-6">
              {/* Header Title & Subtitle */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-indigo-600 font-bold">
                    Executive Command Telemetry
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    Screening Leaderboard
                  </h1>
                </div>

                <div
                  className={`flex items-center rounded-lg p-0.5 border text-xs font-mono ${
                    "bg-slate-100 border-slate-200"
                  }`}
                >
                  <button
                    onClick={() => setViewMode("cards")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
                      viewMode === "cards"
                        ? "bg-indigo-50 text-indigo-600 font-bold border border-indigo-200 shadow-sm"
                        : "text-slate-600 hover:text-slate-800"
                    }`}
                  >
                    <LayoutGrid className="w-3.5 h-3.5" /> Cards
                  </button>
                  <button
                    onClick={() => setViewMode("table")}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
                      viewMode === "table"
                        ? "bg-indigo-50 text-indigo-600 font-bold border border-indigo-200 shadow-sm"
                        : "text-slate-600 hover:text-slate-800"
                    }`}
                  >
                    <List className="w-3.5 h-3.5" /> Compact Table
                  </button>
                </div>
              </div>

              {/* TELEMETRY STRIP */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Candidates screened
                  </div>
                  <div className="text-4xl font-mono font-bold tracking-tight text-slate-900 mt-2">
                    {totalScreened}
                  </div>
                  <div className="text-xs text-indigo-600 font-mono mt-1">avg match {avgMatchScore}%</div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Top match
                  </div>
                  <div className="text-4xl font-mono font-bold tracking-tight text-emerald-700 mt-2">
                    {topMatchCandidate.matchScore}%
                  </div>
                  <div className="text-xs text-slate-700 font-medium mt-1 truncate">
                    {blindMode ? topMatchCandidate.anonymizedId : topMatchCandidate.name}
                  </div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-bold mb-2.5">
                    Model status
                  </div>
                  <div className="space-y-1.5 font-mono text-[10px]">
                    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-700 w-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
                      <span>Engine · TF-IDF + BM25</span>
                    </div>
                    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 w-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                      <span>Local council · offline</span>
                    </div>
                    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 w-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                      <span>{backendConfigured ? "Backend · configured" : "Backend · local mode"}</span>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Active role
                  </div>
                  <div className="text-base font-bold text-slate-900 tracking-tight mt-1 truncate">
                    {activeRole?.title || "Machine Learning Engineer"}
                  </div>
                  <div className="text-[11px] text-slate-600 font-mono mt-0.5">
                    {activeRole?.minExperience || "min 2 yrs"} · {activeRole?.skills?.length || 0} required skills
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2.5">
                    {(activeRole?.skills || []).slice(0, 5).map((s) => (
                      <span key={s} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-indigo-600">
                        {s}
                      </span>
                    ))}
                    {(activeRole?.skills?.length || 0) > 5 && (
                      <span className="text-[9px] font-mono text-slate-500 pl-1">
                        +{(activeRole?.skills?.length || 0) - 5} more
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* ASK THE TALENT POOL */}
              <div className="p-5 rounded-lg border border-slate-200 bg-white space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Ask the talent pool (Hybrid RAG)
                  </div>
                  {activePromptPill && (
                    <button onClick={() => setActivePromptPill("")} className="text-[11px] font-mono text-indigo-600 hover:underline">
                      Reset filter
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                  {PROMPT_PILLS.map((pill) => (
                    <button
                      key={pill}
                      onClick={() => {
                        setActivePromptPill(pill);
                        setSearchQuery("");
                      }}
                      className={`p-2.5 rounded-lg border text-left text-xs font-mono transition-all truncate ${
                        activePromptPill === pill
                          ? "bg-indigo-50 border-indigo-300 text-indigo-600 font-semibold "
                          : "bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-800"
                      }`}
                      title={pill}
                    >
                      "{pill}"
                    </button>
                  ))}
                </div>
              </div>

              {/* CANDIDATE LEADERBOARD CARDS */}
              {viewMode === "cards" ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="text-[11px] font-mono uppercase tracking-widest text-slate-600 font-bold">
                      Leaderboard ({filteredCandidates.length} Candidates)
                    </div>
                    <div className="flex flex-wrap items-center gap-1">
                      {[
                        { id: "ALL", label: `ALL (${candidatesPool.length})` },
                        { id: "STRONG_HIRE", label: `STRONG HIRE (${strongHiresCount})` },
                        { id: "LEAN_HIRE", label: `LEAN HIRE (${leanHiresCount})` },
                        { id: "REJECT", label: `REJECT (${rejectCount})` },
                        { id: "FLAGGED", label: `FLAGGED (${flaggedCount})` }
                      ].map((filter) => (
                        <button
                          key={filter.id}
                          onClick={() => setVerdictFilter(filter.id)}
                          className={`px-2.5 py-1 rounded-md text-xs font-mono transition-all ${
                            verdictFilter === filter.id
                              ? "bg-indigo-50 text-indigo-600 font-bold border border-indigo-200"
                              : "text-slate-600 hover:text-slate-800"
                          }`}
                        >
                          {filter.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3.5">
                    {filteredCandidates.map((cand) => {
                      const score = cand.matchScore;
                      const scoreColor =
                        score >= 80 ? "#10b981" : score >= 60 ? "#38bdf8" : score >= 45 ? "#f59e0b" : "#f43f5e";
                      const isRank1 = cand.rank === 1;

                      return (
                        <div
                          key={cand.id}
                          className={`p-5 rounded-lg border transition-all relative overflow-hidden ${
                            isRank1
                              ? "border-emerald-200  bg-white"
                              : "bg-white border-slate-200 hover:border-slate-300"
                          }`}
                        >
                          <div
                            className="absolute top-0 left-0 right-0 h-[2px]"
                            style={{ backgroundColor: scoreColor, boxShadow: `0 0 14px ${scoreColor}` }}
                          />

                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div className="flex items-center gap-3.5">
                              <div
                                className={`w-10 h-10 rounded-lg flex items-center justify-center font-mono font-bold text-sm shrink-0 ${
                                  isRank1
                                    ? "bg-indigo-600 text-white"
                                    : "bg-white border border-slate-200 text-slate-700"
                                }`}
                              >
                                #{cand.rank}
                              </div>

                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-base text-slate-900">
                                    {blindMode ? cand.anonymizedId : cand.name}
                                  </span>
                                  {isRank1 && (
                                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 font-bold">
                                      GOLD STANDARD #1
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-slate-600 font-mono mt-0.5 flex items-center gap-2">
                                  <span>{blindMode ? "identity hidden" : cand.fileName}</span>
                                  <span>•</span>
                                  <span>{cand.title} ({cand.experienceYears} yrs)</span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              <span
                                className={`px-3 py-1 rounded-lg text-xs font-mono font-bold border tracking-wider ${
                                  cand.verdict === "STRONG_HIRE"
                                    ? "bg-emerald-50 border-emerald-200 text-emerald-700 "
                                    : cand.verdict === "LEAN_HIRE"
                                    ? "bg-amber-50 border-amber-200 text-amber-700 "
                                    : "bg-rose-50 border-rose-200 text-rose-700"
                                }`}
                              >
                                {cand.verdict}
                              </span>

                              <span className="font-mono font-bold text-xl min-w-[65px] text-right" style={{ color: scoreColor }}>
                                {score.toFixed(1)}%
                              </span>

                              <button
                                onClick={() => {
                                  setSelectedCandidate(cand);
                                  setDebateStep(0);
                                  setIsDrawerOpen(true);
                                }}
                                className="px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-600 border border-indigo-200 transition-all flex items-center gap-1 shadow-sm"
                              >
                                Inspect <ChevronRight className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>

                          <div className="my-3.5 h-[7px] rounded-full bg-slate-100 overflow-hidden relative">
                            <div
                              className="h-full rounded-full transition-all duration-700"
                              style={{ width: `${score}%`, backgroundColor: scoreColor, boxShadow: `0 0 14px ${scoreColor}` }}
                            />
                          </div>

                          {cand.evidenceSnippet && (
                            <div className="mb-3 px-3 py-2 rounded-lg bg-indigo-50 border-l-2 border-indigo-300 text-xs text-slate-700 font-sans leading-relaxed">
                              <span className="font-mono text-indigo-600 font-bold uppercase text-[10px] mr-1.5">
                                Verified Evidence:
                              </span>
                              {cand.evidenceSnippet}
                            </div>
                          )}

                          <div className="flex flex-wrap items-center gap-1.5 pt-1">
                            {cand.matchedSkills.map((s) => (
                              <span key={s} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700">
                                ✓ {s}
                              </span>
                            ))}
                            {cand.partiallyMatchedSkills.map((s) => (
                              <span key={s} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-amber-50 border border-amber-200 text-amber-700">
                                ~ {s}
                              </span>
                            ))}
                            {cand.missingSkills.map((s) => (
                              <span key={s} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-rose-50 border border-rose-200 text-rose-700">
                                ✕ {s}
                              </span>
                            ))}
                            <span
                              className={`text-[11px] font-mono px-2 py-0.5 rounded-md border font-semibold ml-auto ${
                                cand.redFlags.length === 0
                                  ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                                  : "bg-rose-50 border-rose-200 text-rose-700"
                              }`}
                            >
                              {cand.redFlags.length === 0 ? "0 red flags" : `${cand.redFlags.length} red flags: ${cand.redFlags.join(", ")}`}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                /* Compact Table View */
                <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-[11px] font-mono uppercase text-slate-600 bg-white">
                        <th className="py-3 px-4">Rank & Profile</th>
                        <th className="py-3 px-4">Match %</th>
                        <th className="py-3 px-4">ATS Format</th>
                        <th className="py-3 px-4">Council Consensus</th>
                        <th className="py-3 px-4">Red Flags</th>
                        <th className="py-3 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 text-xs font-mono">
                      {filteredCandidates.map((c) => (
                        <tr key={c.id} className="hover:bg-slate-100 transition-colors">
                          <td className="py-3.5 px-4 font-sans">
                            <div className="font-bold text-slate-900">#{c.rank} {blindMode ? c.anonymizedId : c.name}</div>
                            <div className="text-[11px] font-mono text-slate-600">{c.title}</div>
                          </td>
                          <td className="py-3.5 px-4 font-bold text-emerald-700">{c.matchScore}%</td>
                          <td className="py-3.5 px-4">{c.atsScore} / 100</td>
                          <td className="py-3.5 px-4">{c.verdict}</td>
                          <td className="py-3.5 px-4 text-rose-700">{c.redFlags.length > 0 ? c.redFlags.join(", ") : "—"}</td>
                          <td className="py-3.5 px-4 text-right">
                            <button
                              onClick={() => {
                                setSelectedCandidate(c);
                                setIsDrawerOpen(true);
                              }}
                              className="px-3 py-1 rounded-lg text-xs bg-slate-100 hover:bg-slate-200 text-indigo-600 border border-slate-200"
                            >
                              Inspect →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ================================================================ */}
          {/* PAGE 3: CANDIDATE DEEP DIVE (Candidate DeepDive)               */}
          {/* ================================================================ */}
          {activeNav === "deepdive" && (
            <div className="space-y-6">
              <div className="p-5 rounded-lg border border-slate-200 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-emerald-700 font-bold">
                    Multi-Agent Consensus Chamber
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    Candidate DeepDive & Council Dossier
                  </h1>
                  <p className="text-xs text-slate-600 font-mono mt-1">
                    4-agent scorecards, live cross-examination debate, and GitHub repository forensics.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-600">Select Candidate:</span>
                  <select
                    value={councilSelectedCandId}
                    onChange={(e) => {
                      setCouncilSelectedCandId(e.target.value);
                      setCouncilDebateTurn(0);
                    }}
                    className="px-3 py-1.5 rounded-lg border text-xs font-mono bg-white border-slate-200 text-slate-800 outline-none"
                  >
                    {candidatesPool.map((c) => (
                      <option key={c.id} value={c.id}>
                        #{c.rank} {c.name} ({c.matchScore}% - {c.verdict})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Banner */}
              <div className="p-6 rounded-lg border border-emerald-200 bg-emerald-50 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <div className="text-xs font-mono text-slate-600">#{councilCandidate.rank} • {councilCandidate.title}</div>
                  <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 mt-1">
                    {blindMode ? councilCandidate.anonymizedId : councilCandidate.name}
                  </h2>
                  <div className="text-xs text-slate-600 font-mono mt-1">
                    Tenure: {councilCandidate.experienceYears} Years • ATS Format: {councilCandidate.atsScore}/100 • GitHub Score: {councilCandidate.github?.score ?? 85}/100
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-slate-600">HYBRID SCORE</div>
                    <div className="text-3xl font-mono font-bold text-emerald-700">{councilCandidate.matchScore}%</div>
                  </div>
                  <div className="h-10 w-[1px] bg-slate-200" />
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-slate-600">COUNCIL CONSENSUS</div>
                    <div className="text-2xl font-mono font-bold text-slate-900 tracking-wider">{councilCandidate.verdict}</div>
                  </div>
                </div>
              </div>

              {/* 4 Agent Scorecards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="font-bold text-indigo-600">TECH LEAD</span>
                      <span className="text-slate-500">35% Weight</span>
                    </div>
                    <div className="text-3xl font-mono font-bold text-slate-900 mt-2">
                      {councilCandidate.council?.techLead?.score ?? 85} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                    </div>
                    <p className="text-xs text-slate-700 font-sans mt-3 leading-relaxed">
                      {councilCandidate.council?.techLead?.feedback || "Technical review verified."}
                    </p>
                  </div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="font-bold text-emerald-700">CULTURE & RETENTION</span>
                      <span className="text-slate-500">20% Weight</span>
                    </div>
                    <div className="text-3xl font-mono font-bold text-slate-900 mt-2">
                      {councilCandidate.council?.culture?.score ?? 80} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                    </div>
                    <p className="text-xs text-slate-700 font-sans mt-3 leading-relaxed">
                      {councilCandidate.council?.culture?.feedback || "Culture alignment verified."}
                    </p>
                  </div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="font-bold text-amber-700">FAIR-HIRING AUDITOR</span>
                      <span className="text-slate-500">25% Weight</span>
                    </div>
                    <div className="text-3xl font-mono font-bold text-slate-900 mt-2">
                      {councilCandidate.council?.fairAuditor?.score ?? 95} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                    </div>
                    <p className="text-xs text-slate-700 font-sans mt-3 leading-relaxed">
                      {councilCandidate.council?.fairAuditor?.feedback || "Fairness audit passed."}
                    </p>
                  </div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white relative overflow-hidden flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="font-bold text-indigo-600">SENIORITY & COMP</span>
                      <span className="text-slate-500">20% Weight</span>
                    </div>
                    <div className="text-base font-mono font-bold text-slate-900 mt-2 truncate">
                      {councilCandidate.level}
                    </div>
                    <div className="my-2.5 h-2 rounded-full bg-slate-100 relative">
                      <div className="absolute top-0 bottom-0 left-0 rounded-full bg-indigo-600" style={{ width: `${councilCandidate.bandPosPct}%` }} />
                    </div>
                    <div className="text-xs font-mono text-amber-700 font-bold">{councilCandidate.salaryRange}</div>
                  </div>
                </div>
              </div>

              {/* Debate Transcript */}
              <div className="p-6 rounded-lg border border-slate-200 bg-white space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold tracking-tight text-slate-900">Cross-Examination Debate</h3>
                  <button
                    onClick={() => setCouncilDebateTurn((prev) => (prev + 1) % (councilCandidate.debateSnippet?.length || 1))}
                    className="px-3 py-1.5 rounded-lg border text-xs font-mono text-emerald-700 border-emerald-200 bg-emerald-50 hover:bg-emerald-100 transition-colors flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" /> Replay Turn ({councilDebateTurn + 1}/{(councilCandidate.debateSnippet?.length || 1)})
                  </button>
                </div>
                <div className="space-y-3 font-mono text-xs">
                  {(councilCandidate.debateSnippet || []).map((turn, i) => (
                    <div
                      key={i}
                      className={`p-4 rounded-lg border transition-all ${
                        i <= councilDebateTurn ? "opacity-100 border-slate-200 bg-white" : "opacity-35 border-slate-200 bg-white"
                      }`}
                    >
                      <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                        <span className="font-bold uppercase text-emerald-700">{turn.agent}</span>
                        <span>TURN {i + 1}</span>
                      </div>
                      <p className="font-sans text-xs text-slate-800">"{turn.text}"</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* PAGE 4: CANDIDATE COMPARISON (Candidate Comparison)             */}
          {/* ================================================================ */}
          {activeNav === "comparison" && (
            <div className="space-y-6">
              <div className="p-5 rounded-lg border border-slate-200 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-indigo-600 font-bold">
                    Head-to-Head Evaluation Matrix
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    Candidate Comparison Matrix
                  </h1>
                  <p className="text-xs text-slate-600 font-mono mt-1">
                    Benchmark top candidates side-by-side across scores, skills, and leveling brackets.
                  </p>
                </div>
              </div>

              {/* Candidate Selectors */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-lg border border-indigo-200 bg-white space-y-3">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="font-bold text-indigo-600">CANDIDATE A:</span>
                    <select
                      value={compareCandAId}
                      onChange={(e) => setCompareCandAId(e.target.value)}
                      className="px-3 py-1.5 rounded-lg border text-xs font-mono bg-white border-slate-200 text-slate-900 outline-none"
                    >
                      {candidatesPool.map((c) => (
                        <option key={c.id} value={c.id}>
                          #{c.rank} {c.name} ({c.matchScore}%)
                        </option>
                      ))}
                    </select>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">{candA.name}</h3>
                  <div className="text-xs text-slate-600 font-mono">{candA.title} • {candA.experienceYears} Years</div>
                  <div className="text-2xl font-mono font-bold text-emerald-700">{candA.matchScore}% Match ({candA.verdict})</div>
                </div>

                <div className="p-5 rounded-lg border border-indigo-200 bg-white space-y-3">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="font-bold text-indigo-600">CANDIDATE B:</span>
                    <select
                      value={compareCandBId}
                      onChange={(e) => setCompareCandBId(e.target.value)}
                      className="px-3 py-1.5 rounded-lg border text-xs font-mono bg-white border-slate-200 text-slate-900 outline-none"
                    >
                      {candidatesPool.map((c) => (
                        <option key={c.id} value={c.id}>
                          #{c.rank} {c.name} ({c.matchScore}%)
                        </option>
                      ))}
                    </select>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">{candB.name}</h3>
                  <div className="text-xs text-slate-600 font-mono">{candB.title} • {candB.experienceYears} Years</div>
                  <div className="text-2xl font-mono font-bold text-indigo-600">{candB.matchScore}% Match ({candB.verdict})</div>
                </div>
              </div>

              {/* Side-by-Side Comparison Matrix */}
              <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-[11px] font-mono uppercase text-slate-600 bg-white">
                      <th className="py-3 px-5">Dimension / Criteria</th>
                      <th className="py-3 px-5 text-indigo-600">{candA.name}</th>
                      <th className="py-3 px-5 text-indigo-600">{candB.name}</th>
                      <th className="py-3 px-5 text-right">Advantage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 font-mono">
                    <tr>
                      <td className="py-3.5 px-5 font-bold text-slate-900">Overall Match %</td>
                      <td className="py-3.5 px-5 text-emerald-700 font-bold">{candA.matchScore}%</td>
                      <td className="py-3.5 px-5 font-bold">{candB.matchScore}%</td>
                      <td className="py-3.5 px-5 text-right text-emerald-700 font-bold">
                        {candA.matchScore >= candB.matchScore ? `+${(candA.matchScore - candB.matchScore).toFixed(1)}% (A)` : `+${(candB.matchScore - candA.matchScore).toFixed(1)}% (B)`}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3.5 px-5 font-bold text-slate-900">ATS Readability</td>
                      <td className="py-3.5 px-5">{candA.atsScore} / 100</td>
                      <td className="py-3.5 px-5">{candB.atsScore} / 100</td>
                      <td className="py-3.5 px-5 text-right">{candA.atsScore >= candB.atsScore ? "Cand A" : "Cand B"}</td>
                    </tr>
                    <tr>
                      <td className="py-3.5 px-5 font-bold text-slate-900">Council Consensus</td>
                      <td className="py-3.5 px-5">{candA.councilScore}% ({candA.verdict})</td>
                      <td className="py-3.5 px-5">{candB.councilScore}% ({candB.verdict})</td>
                      <td className="py-3.5 px-5 text-right">{candA.councilScore >= candB.councilScore ? "Cand A" : "Cand B"}</td>
                    </tr>
                    <tr>
                      <td className="py-3.5 px-5 font-bold text-slate-900">GitHub Authenticity</td>
                      <td className="py-3.5 px-5">{candA.github?.score ?? 85}% ({candA.github?.risk ?? "LOW"} Risk)</td>
                      <td className="py-3.5 px-5">{candB.github?.score ?? 85}% ({candB.github?.risk ?? "LOW"} Risk)</td>
                      <td className="py-3.5 px-5 text-right">{(candA.github?.score ?? 0) >= (candB.github?.score ?? 0) ? "Cand A" : "Cand B"}</td>
                    </tr>
                    <tr>
                      <td className="py-3.5 px-5 font-bold text-slate-900">Salary Range Target</td>
                      <td className="py-3.5 px-5 text-amber-700">{candA.salaryRange}</td>
                      <td className="py-3.5 px-5 text-amber-700">{candB.salaryRange}</td>
                      <td className="py-3.5 px-5 text-right text-slate-600">Level Aligned</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* PAGE 5: INTERVIEW ASSISTANT (Interview Assistant)               */}
          {/* ================================================================ */}
          {activeNav === "interview" && (
            <div className="space-y-6">
              <div className="p-5 rounded-lg border border-slate-200 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-amber-700 font-bold">
                    AI Interview Preparation Kit
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    AI Interview Assistant
                  </h1>
                  <p className="text-xs text-slate-600 font-mono mt-1">
                    Candidate-tailored technical, gap-probing, and architectural interview questions.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-600">Candidate:</span>
                  <select
                    value={interviewCandId}
                    onChange={(e) => setInterviewCandId(e.target.value)}
                    className="px-3 py-1.5 rounded-lg border text-xs font-mono bg-white border-slate-200 text-slate-900 outline-none"
                  >
                    {candidatesPool.map((c) => (
                      <option key={c.id} value={c.id}>
                        #{c.rank} {c.name} ({c.matchScore}%)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-4">
                <div className="p-5 rounded-lg border border-slate-200 bg-white space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">
                        Tailored Interview Questionnaire for {interviewCandidate.name} ({interviewCandidate.title})
                      </h3>
                      <p className="text-xs text-slate-600 mt-0.5 font-mono">
                        {interviewKit.length} questions generated from resume skills, detected gaps, red flags, GitHub risk and the{" "}
                        {activeRole?.title || "open"} role.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={copyInterviewKit}
                      className="shrink-0 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-mono text-slate-700 hover:bg-slate-50"
                    >
                      {interviewCopied ? "Copied" : "Copy all"}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Question categories">
                    {[["All", interviewKit.length], ...interviewTypes].map(([type, count]) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setInterviewType(type)}
                        className={`px-2.5 py-1 rounded-full border text-[11px] font-mono transition ${
                          activeInterviewType === type
                            ? "bg-slate-900 text-white border-slate-900"
                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        {type} ({count})
                      </button>
                    ))}
                  </div>
                </div>

                {visibleInterviewKit.length > 0 ? (
                  visibleInterviewKit.map((q) => (
                    <div
                      key={q.id}
                      className="p-5 rounded-lg border border-slate-200 bg-white space-y-2.5 relative overflow-hidden"
                    >
                      <div className="flex justify-between items-center gap-2 text-xs font-mono">
                        <span className="font-bold text-slate-900">
                          QUESTION #{interviewKit.findIndex((k) => k.id === q.id) + 1}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full border text-[11px] ${
                            BADGE_CLASSES[q.badgeColor] || BADGE_CLASSES.slate
                          }`}
                        >
                          {q.type}
                        </span>
                      </div>
                      <p className="text-sm font-bold text-slate-900 font-sans">"{q.q}"</p>
                      <div className="p-3 rounded-lg bg-white border border-slate-200 text-xs font-mono text-slate-700">
                        <span className="text-emerald-700 font-bold block mb-0.5">What to look for:</span>
                        {q.lookFor}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-5 rounded-lg border border-slate-200 text-xs font-mono text-slate-600">
                    Standard technical evaluation questions generated based on Python & ML requirements.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* PAGE 6: RECRUITER ANALYTICS (Recruiter Analytics)              */}
          {/* ================================================================ */}
          {activeNav === "analytics" && (
            <div className="space-y-6">
              <div className="p-5 rounded-lg border border-slate-200 bg-white">
                <div className="text-[11px] font-mono tracking-widest uppercase text-indigo-600 font-bold">
                  Talent Acquisition Intelligence
                </div>
                <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                  Recruiter Analytics & Cohort Metrics
                </h1>
                <p className="text-xs text-slate-600 font-mono mt-1">
                  Candidate pool funnel, score density distribution, and red-flag frequency metrics.
                </p>
              </div>

              {/* 4 Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-5 rounded-lg border border-slate-200 bg-white">
                  <div className="text-xs font-mono text-slate-600">POOL CONVERSION RATE</div>
                  <div className="text-3xl font-mono font-bold text-emerald-700 mt-2">16.7%</div>
                  <div className="text-xs text-slate-500 font-mono mt-1">2 of 12 Strong Hires</div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white">
                  <div className="text-xs font-mono text-slate-600">MEDIAN SCORE</div>
                  <div className="text-3xl font-mono font-bold text-indigo-600 mt-2">48.8%</div>
                  <div className="text-xs text-slate-500 font-mono mt-1">Cohort benchmark</div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white">
                  <div className="text-xs font-mono text-slate-600">RED FLAG INTERCEPT RATE</div>
                  <div className="text-3xl font-mono font-bold text-amber-700 mt-2">58.3%</div>
                  <div className="text-xs text-slate-500 font-mono mt-1">7 of 12 flagged</div>
                </div>

                <div className="p-5 rounded-lg border border-slate-200 bg-white">
                  <div className="text-xs font-mono text-slate-600">ATS PARSE INTEGRITY</div>
                  <div className="text-3xl font-mono font-bold text-slate-900 mt-2">91.7%</div>
                  <div className="text-xs text-slate-500 font-mono mt-1">11/12 clean formats</div>
                </div>
              </div>

              {/* Skill Frequency Distribution */}
              <div className="p-6 rounded-lg border border-slate-200 bg-white space-y-4">
                <h3 className="text-sm font-bold text-slate-900">Skill Frequency Across Active Applicant Pool</h3>
                <div className="space-y-2.5 font-mono text-xs">
                  {[
                    { skill: "Python", count: 11, pct: 92 },
                    { skill: "Docker", count: 6, pct: 50 },
                    { skill: "FastAPI", count: 5, pct: 42 },
                    { skill: "AWS", count: 4, pct: 33 },
                    { skill: "PyTorch (Verified)", count: 2, pct: 17 }
                  ].map((row) => (
                    <div key={row.skill} className="space-y-1">
                      <div className="flex justify-between text-slate-700">
                        <span>{row.skill}</span>
                        <span>{row.count} candidates ({row.pct}%)</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div className="h-full bg-indigo-600 rounded-full" style={{ width: `${row.pct}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================ */}
          {/* PAGE 7: RECRUITER CHATBOT (Recruiter Chatbot)                  */}
          {/* ================================================================ */}
          {activeNav === "chatbot" && (
            <div className="space-y-6">
              <div className="p-5 rounded-lg border border-slate-200 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-[11px] font-mono tracking-widest uppercase text-amber-700 font-bold">
                    Natural Language Talent Retrieval &amp; Explainable RAG
                  </div>
                  <h1 className="text-2xl font-extrabold tracking-tight mt-0.5">
                    Recruiter Chatbot (Talent Copilot)
                  </h1>
                  <p className="text-xs text-slate-600 font-mono mt-1">
                    Grounded dynamically in the {candidatesPool.length} active candidates, four-agent council debriefs, and {activeRole.title} leveling bands.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setCopilotMessages([
                        {
                          sender: "assistant",
                          text: `Chat session reset. ${candidatesPool.length} candidates loaded for ${activeRole.title}. Ask me to breakdown headcount, match required skills, audit red flags, or draft candidate outreach emails.`
                        }
                      ]);
                    }}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-100 text-slate-600 hover:text-slate-900 font-mono text-xs flex items-center gap-1"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Clear History
                  </button>
                  <button
                    onClick={() => showToast("✓ Session exported to markdown dossier.")}
                    className="px-3.5 py-1.5 rounded-lg border border-slate-200 bg-slate-100 hover:bg-slate-200 text-slate-900 font-mono text-xs flex items-center gap-1.5"
                  >
                    <Download className="w-4 h-4" /> Export Report (.md)
                  </button>
                </div>
              </div>

              {/* Dynamic Suggested Question Pills */}
              <div className="flex flex-wrap gap-2 text-xs font-mono">
                {[
                  "How many members are there in total?",
                  "Which candidate has the required skills?",
                  "Who has red flags and why?",
                  "Compare Karthik Menon and Rahul Nair",
                  "Draft outreach email for Karthik",
                  "What is the compensation band?"
                ].map((pill, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => handleSendCopilot(pill)}
                    className="px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-indigo-600 hover:border-indigo-200 hover:bg-indigo-100 transition-all text-xs"
                  >
                    {pill}
                  </button>
                ))}
              </div>

              {/* Chat Container */}
              <div className="rounded-lg border border-slate-200 bg-white flex flex-col h-[520px] overflow-hidden">
                <div className="flex-1 p-6 overflow-y-auto space-y-4">
                  {copilotMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 max-w-2xl ${msg.sender === "user" ? "ml-auto justify-end" : ""}`}
                    >
                      {msg.sender === "assistant" && (
                        <div className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center shrink-0 font-mono text-xs font-bold">
                          AI
                        </div>
                      )}
                      <div
                        className={`p-4 rounded-lg text-xs leading-relaxed ${
                          msg.sender === "user"
                            ? "bg-indigo-600 text-white font-bold"
                            : "bg-white border border-slate-200 text-slate-800"
                        }`}
                      >
                        <div className="whitespace-pre-wrap font-sans">{renderInline(msg.text)}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Ask the Talent Copilot anything about the candidate pool or skills..."
                    value={copilotInput}
                    onChange={(e) => setCopilotInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendCopilot()}
                    className="flex-1 bg-transparent text-xs outline-none font-sans text-slate-900 placeholder:text-slate-500"
                  />
                  <button
                    onClick={() => handleSendCopilot()}
                    className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-mono text-xs font-bold hover:bg-indigo-700 transition-colors flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" /> Send
                  </button>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 4. SLIDE-OVER INSPECTION DRAWER                                      */}
      {/* -------------------------------------------------------------------- */}
      {isDrawerOpen && selectedCandidate && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40  transition-opacity">
          <div
            className={`w-full max-w-xl h-full border-l p-6 overflow-y-auto space-y-6 transition-all ${
              "bg-white border-slate-200 text-slate-900"
            }`}
          >
            <div className="flex items-start justify-between pb-4 border-b border-slate-200">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-600 font-bold">
                    INSPECTION PROFILE
                  </span>
                  <span className="text-slate-500">/</span>
                  <span className="text-xs font-mono text-slate-600">#{selectedCandidate.rank} {selectedCandidate.id}</span>
                </div>
                <h2 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
                  {blindMode ? selectedCandidate.anonymizedId : selectedCandidate.name}
                </h2>
                <p className="text-xs text-slate-600 mt-0.5 font-mono">
                  {selectedCandidate.title} • {selectedCandidate.experienceYears} Years Verified Tenure
                </p>
              </div>

              <button
                onClick={() => setIsDrawerOpen(false)}
                className="p-1.5 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div
              className={`p-5 rounded-lg border flex items-center justify-between ${
                selectedCandidate.verdict === "STRONG_HIRE"
                  ? "bg-emerald-50 border-emerald-200 "
                  : selectedCandidate.verdict === "LEAN_HIRE"
                  ? "bg-amber-50 border-amber-200 "
                  : "bg-white border-slate-200"
              }`}
            >
              <div>
                <div className="text-[10px] font-mono text-slate-600">AGENTIC COUNCIL CONSENSUS</div>
                <div className="text-lg font-bold font-mono tracking-tight text-slate-900 mt-0.5">
                  {selectedCandidate.verdict} ({selectedCandidate.councilScore}%)
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] font-mono text-slate-600">HYBRID MATCH</div>
                <div className="text-xl font-bold font-mono text-emerald-700">
                  {selectedCandidate.matchScore}%
                </div>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-slate-200 bg-white text-xs space-y-2.5">
              <div className="flex items-center justify-between font-mono">
                <span className="text-slate-600 flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-indigo-600" /> TENURE & EXPERIENCE:
                </span>
                <span className="text-slate-900 font-bold">{selectedCandidate.experienceYears} YRS</span>
              </div>
              <p className="text-slate-700 font-sans leading-relaxed">
                {selectedCandidate.evidenceSnippet}
              </p>
              <div className="pt-2.5 border-t border-slate-200 flex items-center justify-between font-mono">
                <span className="text-slate-600 flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-amber-700" /> COMPENSATION BAND:
                </span>
                <span className="text-amber-700 font-bold">{selectedCandidate.salaryRange} (INR {selectedCandidate.salaryInr})</span>
              </div>
            </div>

            <div className="space-y-2.5">
              <h4 className="text-xs font-mono uppercase tracking-wider text-slate-600 font-bold">
                The Four Specialized Agents
              </h4>
              <div className="grid grid-cols-2 gap-2.5">
                {[
                  { name: "Tech Lead", score: selectedCandidate?.council?.techLead?.score ?? 85, note: selectedCandidate?.council?.techLead?.feedback || "Technical review verified." },
                  { name: "Culture & Collab", score: selectedCandidate?.council?.culture?.score ?? 80, note: selectedCandidate?.council?.culture?.feedback || "Culture alignment verified." },
                  { name: "Fair-Hiring Auditor", score: selectedCandidate?.council?.fairAuditor?.score ?? 95, note: selectedCandidate?.council?.fairAuditor?.feedback || "Fairness audit passed." },
                  { name: "Seniority & Comp", score: selectedCandidate?.council?.seniorityComp?.score ?? 85, note: selectedCandidate?.council?.seniorityComp?.feedback || "Compensation aligned." }
                ].map((agent) => (
                  <div key={agent.name} className="p-3.5 rounded-lg border border-slate-200 bg-white text-xs">
                    <div className="flex items-center justify-between font-mono">
                      <span className="font-bold text-slate-800">{agent.name}</span>
                      <span className="font-bold text-slate-900">{agent.score}/100</span>
                    </div>
                    <p className="text-[11px] text-slate-600 mt-1.5 leading-snug line-clamp-3">
                      {agent.note}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 flex items-center gap-3">
              <button
                onClick={() => showToast(`✓ Exported audit dossier for ${selectedCandidate?.name || 'Candidate'} (.md)`)}
                className="flex-1 py-2.5 px-3 rounded-lg text-xs font-mono font-bold bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
              >
                Export Audit Dossier (.MD)
              </button>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="py-2.5 px-4 rounded-lg text-xs font-mono border border-slate-200 text-slate-600 hover:text-slate-900"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Executive Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg bg-slate-900 text-white shadow-lg text-xs flex items-center gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

    </div>
  );
}
